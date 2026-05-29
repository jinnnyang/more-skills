import fs from 'fs/promises';
import { JSDOM } from 'jsdom';
import dompurify from 'dompurify';

// Setup JSDOM before importing mermaid to mock browser environment
const dom = new JSDOM('', {
  url: "http://localhost/",
});

const DOMPurify = dompurify(dom.window as any);

// Mock the default export of dompurify so that when mermaid imports it, it has the methods
(dompurify as any).sanitize = DOMPurify.sanitize;
(dompurify as any).addHook = DOMPurify.addHook;
(dompurify as any).setConfig = DOMPurify.setConfig;

Object.assign(global, {
  window: dom.window,
  document: dom.window.document,
  DOMPurify: DOMPurify
});

(global as any).window = dom.window;
(global as any).document = dom.window.document;
(global as any).Element = dom.window.Element;
(global as any).SVGElement = dom.window.SVGElement || class SVGElement extends (global as any).Element {};
(global as any).DOMPurify = DOMPurify;
(dom.window as any).DOMPurify = DOMPurify;

async function validate() {
  const { default: mermaid } = await import('mermaid');

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose"
  });

  let code = '';
  const input = process.argv[2];

  if (input) {
    try {
      const stat = await fs.stat(input);
      if (stat.isFile()) {
        code = await fs.readFile(input, 'utf8');
      } else {
        code = input;
      }
    } catch (err) {
      code = input;
    }
  } else {
    if (!process.stdin.isTTY) {
      try {
        const chunks = [];
        for await (const chunk of process.stdin) {
          chunks.push(chunk);
        }
        code = Buffer.concat(chunks).toString('utf8');
      } catch (err) {
        console.error("Error reading from stdin:", err);
      }
    }
  }

  if (!code || !code.trim()) {
    console.error("Error: No Mermaid code provided via argument or stdin.");
    process.exit(1);
  }

  try {
    await mermaid.parse(code);
    console.log("Valid Mermaid code.");
    process.exit(0);
  } catch (error: any) {
    console.error("Invalid Mermaid code:");
    console.error(error.message || error);
    if (error.hash) {
      console.error("Line:", error.hash.line);
      console.error("Expected:", error.hash.expected);
      console.error("Token:", error.hash.token);
    }
    process.exit(1);
  }
}

validate();
