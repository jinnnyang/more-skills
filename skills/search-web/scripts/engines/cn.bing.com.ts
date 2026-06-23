import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { SimpleFakeBrowser } from '../browser.js';

export interface SearchResult {
  title: string;
  alt: string;
  url: string;
}

export class BingClient extends SimpleFakeBrowser {
  constructor(rateLimitRPM = 20) {
    super(rateLimitRPM);
  }

  /**
   * Utility to clean HTML tags and decode basic entities from string
   */
  private cleanHtmlText(text: string): string {
    if (!text) return '';
    let cleaned = text.replace(/<[^>]+>/g, '');
    // Strip Unicode Private Use Area (PUA) highlight characters (\uE000-\uF8FF)
    cleaned = cleaned.replace(/[\uE000-\uF8FF]/g, '');
    cleaned = cleaned
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    return cleaned;
  }

  /**
   * Helper to decode Bing tracking redirect URLs (bing.com/ck/a)
   */
  private decodeBingUrl(url: string): string {
    if (url.includes('bing.com/ck/a')) {
      try {
        const uParam = url.match(/[?&](?:amp;)?u=([^&;]+)/i);
        if (uParam) {
          let b64 = uParam[1];
          // Strip the first two characters (e.g. 'a1')
          b64 = b64.substring(2);
          // Standard base64 decoding
          b64 = b64.replace(/-/g, '+').replace(/_/g, '/');
          while (b64.length % 4 !== 0) {
            b64 += '=';
          }
          const decoded = Buffer.from(b64, 'base64').toString('utf-8');
          if (decoded.startsWith('http')) {
            return decoded;
          }
        }
      } catch (err) {
        // Ignore decoding errors
      }
    }
    return url;
  }

  /**
   * 1. Search pages by texts (General web search)
   */
  public async search_pages_by_texts(query: string): Promise<SearchResult[]> {
    const url = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
    const response = await this.get(url);
    const html = await response.text();

    const results: SearchResult[] = [];
    const parts = html.split('<li class="b_algo"');

    for (let i = 1; i < parts.length; i++) {
      const part = parts[i].split('</li>')[0];
      // Match title link inside any h2 header tag: <h2 ...><a href="URL" ...>TITLE</a></h2>
      const hrefMatch = part.match(/<h2[^>]*><a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
      
      if (hrefMatch) {
        const resultUrl = this.decodeBingUrl(hrefMatch[1]);
        // Skip internal or relative links if any
        if (resultUrl.startsWith('/') || resultUrl.includes('bing.com/')) {
          continue;
        }
        const title = this.cleanHtmlText(hrefMatch[2]);

        // Snippet extraction
        let snippet = '';
        const snippetMatch = 
          part.match(/<p[^>]*>([\s\S]*?)<\/p>/i) || 
          part.match(/<div\s+class="b_caption"[^>]*>([\s\S]*?)<\/div>/i) ||
          part.match(/<div\s+class="b_snippet"[^>]*>([\s\S]*?)<\/div>/i);
        
        if (snippetMatch) {
          snippet = this.cleanHtmlText(snippetMatch[1]);
        }

        results.push({
          title,
          alt: `Search Result: ${title} - ${snippet}`,
          url: resultUrl
        });
      }
    }

    // Fallback: if no list item results matched, try a generic anchor extractor
    if (results.length === 0) {
      const anchorRegex = /<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
      let match;
      while ((match = anchorRegex.exec(html)) !== null && results.length < 10) {
        const link = this.decodeBingUrl(match[1]);
        const text = this.cleanHtmlText(match[2]);
        if (
          link.startsWith('http') && 
          !link.includes('bing.com') && 
          text.length > 15 && 
          !results.some(r => r.url === link)
        ) {
          results.push({
            title: text,
            alt: `Search Result Link: ${text}`,
            url: link
          });
        }
      }
    }

    return results;
  }

  /**
   * 2. Search images by texts
   */
  public async search_images_by_texts(query: string): Promise<SearchResult[]> {
    const url = `https://www.bing.com/images/search?q=${encodeURIComponent(query)}`;
    const response = await this.get(url);
    const html = await response.text();

    const results: SearchResult[] = [];
    const regex = /class="iusc"[^>]*\s+m="([^"]+)"/gi;
    let match;

    while ((match = regex.exec(html)) !== null) {
      try {
        const jsonStr = match[1].replace(/&quot;/g, '"');
        const data = JSON.parse(jsonStr);
        if (data.murl) {
          const title = this.cleanHtmlText(data.desc || data.t || 'Bing Image');
          results.push({
            title,
            alt: `Alt description: ${title}`,
            url: data.murl
          });
        }
      } catch (err) {
        // Ignore parsing error
      }
    }

    return results;
  }

  /**
   * Public interface to retrieve raw unmodified HTML from the search engine
   */
  public async get_raw_html(output_type: string, input_type: string, query: string): Promise<string> {
    let url = '';
    if (output_type === 'pages') {
      url = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
    } else if (output_type === 'images') {
      url = `https://www.bing.com/images/search?q=${encodeURIComponent(query)}`;
    } else {
      throw new Error(`Unsupported raw HTML type: ${output_type} by ${input_type}`);
    }

    const res = await this.get(url);
    return res.text();
  }
}
