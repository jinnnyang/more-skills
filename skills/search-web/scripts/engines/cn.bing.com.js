import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { SimpleFakeBrowser } from '../browser.js';
export class BingClient extends SimpleFakeBrowser {
    constructor(rateLimitRPM = 20) {
        super(rateLimitRPM);
    }
    /**
     * Utility to clean HTML tags and decode basic entities from string
     */
    cleanHtmlText(text) {
        if (!text)
            return '';
        let cleaned = text.replace(/<[^>]+>/g, '');
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
     * 1. Search pages by texts (General web search)
     */
    async search_pages_by_texts(query) {
        const url = `https://cn.bing.com/search?q=${encodeURIComponent(query)}`;
        const response = await this.get(url);
        const html = await response.text();
        const results = [];
        const parts = html.split('<li class="b_algo"');
        for (let i = 1; i < parts.length; i++) {
            const part = parts[i].split('</li>')[0];
            // Match title link inside any h2 header tag: <h2 ...><a href="URL" ...>TITLE</a></h2>
            const hrefMatch = part.match(/<h2[^>]*><a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
            if (hrefMatch) {
                const resultUrl = hrefMatch[1];
                // Skip internal or relative links if any
                if (resultUrl.startsWith('/') || resultUrl.includes('bing.com/')) {
                    continue;
                }
                const title = this.cleanHtmlText(hrefMatch[2]);
                // Snippet extraction
                let snippet = '';
                const snippetMatch = part.match(/<p[^>]*>([\s\S]*?)<\/p>/i) ||
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
                const link = match[1];
                const text = this.cleanHtmlText(match[2]);
                if (link.startsWith('http') &&
                    !link.includes('bing.com') &&
                    text.length > 15 &&
                    !results.some(r => r.url === link)) {
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
    async search_images_by_texts(query) {
        const url = `https://cn.bing.com/images/search?q=${encodeURIComponent(query)}`;
        const response = await this.get(url);
        const html = await response.text();
        const results = [];
        const regex = /class="iusc"[^>]*\s+m="([^"]+)"/gi;
        let match;
        while ((match = regex.exec(html)) !== null) {
            try {
                const jsonStr = match[1].replace(/&quot;/g, '"');
                const data = JSON.parse(jsonStr);
                if (data.murl) {
                    const title = data.desc || 'Bing Image';
                    results.push({
                        title,
                        alt: `Alt description: ${title}`,
                        url: data.murl
                    });
                }
            }
            catch (err) {
                // Ignore parsing error
            }
        }
        return results;
    }
    /**
     * 3. Search videos by texts
     */
    async search_videos_by_texts(query) {
        const url = `https://cn.bing.com/videos/search?q=${encodeURIComponent(query)}`;
        const response = await this.get(url);
        const html = await response.text();
        const results = [];
        const videoCards = html.split(/class="mc_vtvc_card"|class="mc_vtvc"/i);
        for (let i = 1; i < videoCards.length; i++) {
            const card = videoCards[i].split('</div></div>')[0];
            const urlMatch = card.match(/href="([^"]+)"/i);
            const titleMatch = card.match(/class="mc_vtvc_title"[^>]*>([\s\S]*?)<\/div>/i) || card.match(/title="([^"]+)"/i);
            const durMatch = card.match(/class="td_dur"[^>]*>([\s\S]*?)<\/span>/i) || card.match(/class="vr_dur"[^>]*>([\s\S]*?)<\/div>/i);
            if (urlMatch) {
                let videoUrl = urlMatch[1];
                if (videoUrl.startsWith('/')) {
                    videoUrl = 'https://cn.bing.com' + videoUrl;
                }
                const title = titleMatch ? this.cleanHtmlText(titleMatch[1]) : 'Bing Video';
                const duration = durMatch ? this.cleanHtmlText(durMatch[1]) : 'Unknown duration';
                results.push({
                    title,
                    alt: `Video description: ${title} (Duration: ${duration})`,
                    url: videoUrl
                });
            }
        }
        return results;
    }
    /**
     * 4. Search papers by texts (Academic papers)
     */
    async search_papers_by_texts(query) {
        const augmentedQuery = `site:arxiv.org OR site:ieee.org OR site:nature.com OR site:springer.com OR site:researchgate.net OR site:science.org OR site:pubmed.ncbi.nlm.nih.gov ${query}`;
        return this.search_pages_by_texts(augmentedQuery);
    }
    /**
     * 5. Search locations by texts (Maps)
     */
    async search_locations_by_texts(query) {
        const augmentedQuery = `map location ${query}`;
        return this.search_pages_by_texts(augmentedQuery);
    }
    /**
     * 6. Search terms by texts (Dictionary / Wikipedia definitions)
     */
    async search_terms_by_texts(query) {
        const augmentedQuery = `definition term wikipedia ${query}`;
        return this.search_pages_by_texts(augmentedQuery);
    }
    /**
     * 7. Search images by images (Reverse visual search for similar images)
     */
    async search_images_by_images(imagePathOrUrl) {
        const html = await this.fetch_visual_search_html(imagePathOrUrl);
        const results = [];
        const imgExtensions = /\.(jpg|jpeg|png|webp|gif|svg|bmp)(\?|$)/i;
        // 1. Extract visually similar images from embedded metadata (class="iusc" m="{...}")
        const imgRegex = /class="iusc"[^>]*\s+m="([^"]+)"/gi;
        let match;
        while ((match = imgRegex.exec(html)) !== null && results.length < 30) {
            try {
                const jsonStr = match[1].replace(/&quot;/g, '"');
                const data = JSON.parse(jsonStr);
                if (data.murl) {
                    const isImage = imgExtensions.test(data.murl) ||
                        data.murl.includes('/th/id/') ||
                        data.murl.includes('imgurl=');
                    if (isImage && !results.some(r => r.url === data.murl)) {
                        const title = data.desc || 'Visual Match Image';
                        results.push({
                            title,
                            alt: `Visual Match Image: ${title}`,
                            url: data.murl
                        });
                    }
                }
            }
            catch (err) { }
        }
        // 2. Fallback: extract direct links ending with image extensions
        const anchorRegex = /<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
        while ((match = anchorRegex.exec(html)) !== null && results.length < 40) {
            const link = match[1];
            if (imgExtensions.test(link) && !results.some(r => r.url === link)) {
                const text = this.cleanHtmlText(match[2]) || 'Similar Image';
                results.push({
                    title: text,
                    alt: `Visual Match Image Link: ${text}`,
                    url: link
                });
            }
        }
        return results;
    }
    /**
     * 8. Search pages by images (Reverse visual search for pages/articles containing the image)
     */
    async search_pages_by_images(imagePathOrUrl) {
        const html = await this.fetch_visual_search_html(imagePathOrUrl);
        const results = [];
        const imgExtensions = /\.(jpg|jpeg|png|webp|gif|svg|bmp)(\?|$)/i;
        const anchorRegex = /<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
        let match;
        while ((match = anchorRegex.exec(html)) !== null && results.length < 20) {
            const link = match[1];
            const text = this.cleanHtmlText(match[2]);
            // Filter: web page link, not bing.com, not an image file URL, and must contain substantial text
            if (link.startsWith('http') &&
                !link.includes('bing.com') &&
                !imgExtensions.test(link) &&
                text.length > 10 &&
                !results.some(r => r.url === link)) {
                results.push({
                    title: text,
                    alt: `Visual Match Page: ${text}`,
                    url: link
                });
            }
        }
        return results;
    }
    /**
     * Helper to execute Visual Search upload/submission and retrieve results page HTML
     */
    async fetch_visual_search_html(imagePathOrUrl) {
        let targetUrl = '';
        if (imagePathOrUrl.startsWith('http://') || imagePathOrUrl.startsWith('https://')) {
            const submitUrl = `https://cn.bing.com/images/searchbyimage?cbir=sbi&imgurl=${encodeURIComponent(imagePathOrUrl)}`;
            const response = await this.get(submitUrl);
            targetUrl = response.url;
        }
        else {
            let localPath = imagePathOrUrl;
            if (localPath.startsWith('file://')) {
                localPath = fileURLToPath(localPath);
            }
            if (!fs.existsSync(localPath)) {
                throw new Error(`Local file path not found: ${localPath}`);
            }
            const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2);
            const fileBuffer = fs.readFileSync(localPath);
            const fileName = path.basename(localPath);
            const header = `--${boundary}\r\nContent-Disposition: form-data; name="imageBin"; filename="${fileName}"\r\nContent-Type: image/jpeg\r\n\r\n`;
            const footer = `\r\n--${boundary}--\r\n`;
            const body = Buffer.concat([
                Buffer.from(header, 'utf-8'),
                fileBuffer,
                Buffer.from(footer, 'utf-8')
            ]);
            const response = await this.post('https://cn.bing.com/images/app/upload?app=msbing', body, {
                'Content-Type': `multipart/form-data; boundary=${boundary}`
            });
            targetUrl = response.url;
            if (!targetUrl || targetUrl.includes('app/upload')) {
                const text = await response.text();
                const urlMatch = text.match(/href="([^"]+)"/i) || text.match(/URL='([^']+)'/i);
                if (urlMatch) {
                    targetUrl = urlMatch[1];
                }
            }
        }
        if (!targetUrl) {
            throw new Error('Could not obtain Visual Search results URL from Bing.');
        }
        const detailResponse = await this.get(targetUrl);
        return detailResponse.text();
    }
    /**
     * Public interface to retrieve raw unmodified HTML from the search engine
     */
    async get_raw_html(output_type, input_type, query) {
        if (input_type === 'images') {
            return this.fetch_visual_search_html(query);
        }
        let url = '';
        if (output_type === 'pages') {
            url = `https://cn.bing.com/search?q=${encodeURIComponent(query)}`;
        }
        else if (output_type === 'images') {
            url = `https://cn.bing.com/images/search?q=${encodeURIComponent(query)}`;
        }
        else if (output_type === 'videos') {
            url = `https://cn.bing.com/videos/search?q=${encodeURIComponent(query)}`;
        }
        else if (output_type === 'papers') {
            const q = `site:arxiv.org OR site:ieee.org OR site:nature.com OR site:springer.com OR site:researchgate.net OR site:science.org OR site:pubmed.ncbi.nlm.nih.gov ${query}`;
            url = `https://cn.bing.com/search?q=${encodeURIComponent(q)}`;
        }
        else if (output_type === 'locations') {
            url = `https://cn.bing.com/search?q=${encodeURIComponent('map location ' + query)}`;
        }
        else if (output_type === 'terms') {
            url = `https://cn.bing.com/search?q=${encodeURIComponent('definition term wikipedia ' + query)}`;
        }
        const res = await this.get(url);
        return res.text();
    }
}
