import { checkRateLimit } from './utils/rate-limiter.js';

interface Cookie {
  value: string;
  domain?: string;
  path?: string;
  expires?: Date;
}

export class SimpleFakeBrowser {
  private cookies: Map<string, Cookie> = new Map();
  private userAgent: string;
  private defaultHeaders: Record<string, string>;
  private rateLimitRPM: number;

  constructor(rateLimitRPM = 20) {
    this.rateLimitRPM = rateLimitRPM;
    // Premium Chrome on Windows User Agent
    this.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36';
    
    this.defaultHeaders = {
      'User-Agent': this.userAgent,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
      'Sec-Ch-Ua-Mobile': '?0',
      'Sec-Ch-Ua-Platform': '"Windows"',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1'
    };
  }

  /**
   * Sets/updates cookies manually
   */
  public setCookie(name: string, value: string, domain?: string, path = '/'): void {
    this.cookies.set(name, { value, domain, path });
  }

  /**
   * Generates a Cookie header string matching the target URL domain and path
   */
  private getCookieHeader(targetUrl: string): string {
    const url = new URL(targetUrl);
    const host = url.hostname;
    const cookiePairs: string[] = [];

    for (const [name, cookie] of this.cookies.entries()) {
      // Basic domain matching (e.g. .bing.com matches cn.bing.com)
      if (cookie.domain) {
        const domainPattern = cookie.domain.startsWith('.') ? cookie.domain : `.${cookie.domain}`;
        if (!host.endsWith(domainPattern) && host !== cookie.domain) {
          continue;
        }
      }
      cookiePairs.push(`${name}=${cookie.value}`);
    }

    return cookiePairs.join('; ');
  }

  /**
   * Parses Set-Cookie headers from response and stores them
   */
  private saveCookies(targetUrl: string, headers: Headers): void {
    const url = new URL(targetUrl);
    const host = url.hostname;
    
    // Node 18+ provides getSetCookie() on Headers
    let setCookieHeaders: string[] = [];
    if (typeof headers.getSetCookie === 'function') {
      setCookieHeaders = headers.getSetCookie();
    } else {
      const singleHeader = headers.get('set-cookie');
      if (singleHeader) {
        setCookieHeaders = [singleHeader];
      }
    }

    for (const cookieStr of setCookieHeaders) {
      const parts = cookieStr.split(';').map(p => p.trim());
      if (parts.length === 0) continue;

      const [eqPart, ...rest] = parts;
      const eqIdx = eqPart.indexOf('=');
      if (eqIdx === -1) continue;

      const name = eqPart.substring(0, eqIdx).trim();
      const value = eqPart.substring(eqIdx + 1).trim();

      const cookie: Cookie = { value };

      for (const attr of parts.slice(1)) {
        const [k, v] = attr.split('=').map(p => p.trim());
        const lowerK = k.toLowerCase();
        if (lowerK === 'domain') {
          cookie.domain = v;
        } else if (lowerK === 'path') {
          cookie.path = v;
        } else if (lowerK === 'expires') {
          cookie.expires = new Date(v);
        }
      }

      // Default domain if omitted
      if (!cookie.domain) {
        cookie.domain = host;
      }

      this.cookies.set(name, cookie);
    }
  }

  public async get(url: string, customHeaders: Record<string, string> = {}): Promise<Response> {
    await checkRateLimit(this.rateLimitRPM);

    // If cookies are empty and requesting a search-related page, pre-fetch from homepage to populate cookies
    if (this.cookies.size === 0 && (url.includes('/search') || url.includes('/images') || url.includes('/videos'))) {
      try {
        const parsedUrl = new URL(url);
        const homepage = `${parsedUrl.protocol}//${parsedUrl.hostname}/`;
        const prefetchHeaders = { ...this.defaultHeaders, ...customHeaders };
        const prefetchRes = await fetch(homepage, {
          method: 'GET',
          headers: prefetchHeaders
        });
        this.saveCookies(homepage, prefetchRes.headers);
      } catch (err) {
        // Ignore pre-fetch failures and proceed
      }
    }

    const cookieHeader = this.getCookieHeader(url);
    const headers = { ...this.defaultHeaders, ...customHeaders };
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers
    });

    this.saveCookies(url, response.headers);
    return response;
  }

  /**
   * Performs a HTTP POST request with multipart or JSON body, cookie tracking, and rate limiting
   */
  public async post(
    url: string, 
    body: BodyInit, 
    customHeaders: Record<string, string> = {}
  ): Promise<Response> {
    await checkRateLimit(this.rateLimitRPM);

    const cookieHeader = this.getCookieHeader(url);
    const headers = { ...this.defaultHeaders, ...customHeaders };
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body
    });

    this.saveCookies(url, response.headers);
    return response;
  }
}
