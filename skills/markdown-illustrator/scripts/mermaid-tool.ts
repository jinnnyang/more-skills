import fs from 'fs/promises';
import path from 'path';
import { JSDOM } from 'jsdom';
import dompurify from 'dompurify';
import { renderMermaidSVG, THEMES } from 'beautiful-mermaid';
import { Resvg } from '@resvg/resvg-js';

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

// Helper to parse Hex color to RGB
function parseColor(c: string): { r: number; g: number; b: number } | null {
  c = c.trim();
  if (c.startsWith('#')) {
    const hex = c.substring(1);
    if (hex.length === 3) {
      const r = parseInt(hex[0] + hex[0], 16);
      const g = parseInt(hex[1] + hex[1], 16);
      const b = parseInt(hex[2] + hex[2], 16);
      return { r, g, b };
    } else if (hex.length === 6 || hex.length === 8) {
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return { r, g, b };
    }
  }
  const colors: Record<string, string> = {
    white: '#ffffff',
    black: '#000000',
    red: '#ff0000',
    green: '#00ff00',
    blue: '#0000ff'
  };
  if (colors[c.toLowerCase()]) {
    return parseColor(colors[c.toLowerCase()]);
  }
  return null;
}

// Mix two colors together for color-mix compatibility
function mixColors(color1Str: string, color2Str: string, weight1: number): string {
  const c1 = parseColor(color1Str);
  const c2 = parseColor(color2Str);
  if (!c1 || !c2) return color1Str;

  const w1 = weight1 / 100;
  const w2 = 1 - w1;

  const r = Math.round(c1.r * w1 + c2.r * w2);
  const g = Math.round(c1.g * w1 + c2.g * w2);
  const b = Math.round(c1.b * w1 + c2.b * w2);

  const toHex = (n: number) => n.toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// Resolve CSS color-mix expressions in generated SVGs
function resolveColorMixes(svg: string): string {
  const styleMatch = svg.match(/<svg[^>]*style="([^"]*)"/);
  const variables: Record<string, string> = {};
  if (styleMatch) {
    const styleContent = styleMatch[1];
    const varRegex = /(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+)/g;
    let match;
    while ((match = varRegex.exec(styleContent)) !== null) {
      variables[match[1]] = match[2].trim();
    }
  }

  const resolveVal = (val: string): string => {
    val = val.trim();
    if (val.startsWith('var(')) {
      const varName = val.substring(4, val.length - 1).trim();
      return variables[varName] || '#000000';
    }
    return val;
  };

  const colorMixRegex = /color-mix\(\s*in\s+srgb\s*,\s*(var\((?:--[a-zA-Z0-9_-]+)\)|#[0-9a-fA-F]{3,8})\s+(\d+)%\s*,\s*(var\((?:--[a-zA-Z0-9_-]+)\)|#[0-9a-fA-F]{3,8})\s*\)/g;

  return svg.replace(colorMixRegex, (match, val1, pctStr, val2) => {
    const c1 = resolveVal(val1);
    const c2 = resolveVal(val2);
    const pct = parseInt(pctStr, 10);
    return mixColors(c1, c2, pct);
  });
}

// Inline CSS variables in SVG elements to ensure Resvg prints correct colors
function resolveAllCSSVariables(svg: string): string {
  let cleanSvg = resolveColorMixes(svg);
  const variables: Record<string, string> = {};

  const styleMatch = cleanSvg.match(/<svg[^>]*style="([^"]*)"/);
  if (styleMatch) {
    const styleContent = styleMatch[1];
    const varRegex = /(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+)/g;
    let match;
    while ((match = varRegex.exec(styleContent)) !== null) {
      variables[match[1]] = match[2].trim();
    }
  }

  const styleBlockRegex = /<style[^>]*>([\s\S]*?)<\/style>/g;
  let styleBlockMatch;
  while ((styleBlockMatch = styleBlockRegex.exec(cleanSvg)) !== null) {
    const styleBlockContent = styleBlockMatch[1];
    const varRegex = /(--[a-zA-Z0-9_-]+)\s*:\s*([^;}\r\n]+)/g;
    let match;
    while ((match = varRegex.exec(styleBlockContent)) !== null) {
      variables[match[1]] = match[2].trim();
    }
  }

  const resolveVarExpression = (expr: string): string => {
    expr = expr.trim();
    if (!expr.startsWith('var(')) return expr;

    const varMatch = expr.match(/^var\(\s*(--[a-zA-Z0-9_-]+)(?:\s*,\s*(.+))?\s*\)$/);
    if (!varMatch) return expr;

    const varName = varMatch[1];
    const fallback = varMatch[2];

    if (variables[varName] !== undefined) {
      return resolveVarExpression(variables[varName]);
    }
    if (fallback !== undefined) {
      return resolveVarExpression(fallback);
    }
    return '#000000';
  };

  const resolvedVariables: Record<string, string> = {};
  for (const name of Object.keys(variables)) {
    resolvedVariables[name] = resolveVarExpression(variables[name]);
  }

  let output = cleanSvg;
  const varRefRegex = /var\(\s*(--[a-zA-Z0-9_-]+)(?:\s*,\s*([^()]+|(?:\([^()]*\))))?\s*\)/g;

  for (let pass = 0; pass < 5; pass++) {
    const next = output.replace(varRefRegex, (match, varName, fallback) => {
      if (resolvedVariables[varName] !== undefined) {
        return resolvedVariables[varName];
      }
      if (fallback !== undefined) {
        return resolveVarExpression(fallback);
      }
      return '#000000';
    });
    if (next === output) break;
    output = next;
  }

  return output;
}

// CLI Execution Wrapper
async function run() {
  const args = process.argv.slice(2);
  let inputPath = '';
  let directCode = '';
  let outputPath = '';
  let theme = 'zinc-light';
  let validateOnly = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '-i' || args[i] === '--input') {
      inputPath = args[++i];
    } else if (args[i] === '-c' || args[i] === '--code') {
      directCode = args[++i];
    } else if (args[i] === '-o' || args[i] === '--output') {
      outputPath = args[++i];
    } else if (args[i] === '-t' || args[i] === '--theme') {
      theme = args[++i];
    } else if (args[i] === '-v' || args[i] === '--validate-only') {
      validateOnly = true;
    }
  }

  let code = '';
  if (directCode) {
    code = directCode;
  } else if (inputPath) {
    try {
      code = await fs.readFile(inputPath, 'utf8');
    } catch (err: any) {
      console.error(`Error reading input file: ${err.message}`);
      process.exit(1);
    }
  }

  if (!code || !code.trim()) {
    console.error("Error: No Mermaid code provided.");
    console.log("Usage: node scripts/mermaid-tool.ts [-c <code> | -i <input.mmd>] [-o <output.svg|.png>] [-t <theme>] [-v]");
    console.log("Options:");
    console.log("  -c, --code            Direct Mermaid code string");
    console.log("  -i, --input           Path to input .mmd file");
    console.log("  -o, --output          Path to save the generated SVG or PNG");
    console.log("  -t, --theme           Visual theme (zinc-light, zinc-dark, tokyo-night, etc.)");
    console.log("  -v, --validate-only   Only validate syntax without rendering");
    process.exit(1);
  }

  // Parse check using mermaid.parse
  const { default: mermaid } = await import('mermaid');
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose"
  });

  try {
    await mermaid.parse(code);
  } catch (error: any) {
    console.error("\x1b[31mInvalid Mermaid code:\x1b[0m");
    console.error(error.message || error);
    if (error.hash) {
      console.error(`Line: ${error.hash.line}`);
      console.error(`Expected: ${error.hash.expected}`);
      console.error(`Token: ${error.hash.token}`);
    }
    
    // Structured Output Protocol: print Agent guidance
    console.error("\n\x1b[33m[AGENT GUIDANCE - DIAGNOSIS]\x1b[0m");
    console.error("1. Check if all text or node labels containing brackets, parentheses, or special chars are wrapped in double quotes, e.g. Node[\"Text (Label)\"].");
    console.error("2. Verify that you have the correct diagram preamble (e.g. 'flowchart TD', 'sequenceDiagram').");
    console.error("3. Ensure arrow syntax is correct (e.g. '-->' or '-.->').");
    process.exit(1);
  }

  if (validateOnly) {
    console.log("Mermaid code is valid.");
    console.log("\n[AGENT GUIDANCE] SUCCESS. Mermaid code syntax validated successfully.");
    process.exit(0);
  }

  if (!outputPath) {
    console.log("Mermaid code is valid. Pass -o to export as image.");
    process.exit(0);
  }

  // Render and export
  try {
    const themeOptions = THEMES[theme as keyof typeof THEMES] || THEMES['zinc-light'];
    let svg = renderMermaidSVG(code, themeOptions);
    svg = resolveAllCSSVariables(svg);
    const format = outputPath.toLowerCase().endsWith('.png') ? 'png' : 'svg';

    if (format === 'svg') {
      await fs.writeFile(outputPath, svg, 'utf8');
      console.log(`Successfully exported SVG to: ${path.resolve(outputPath)}`);
      console.log(`\n[AGENT GUIDANCE] SUCCESS. Mermaid diagram exported to SVG: ${outputPath}.`);
    } else if (format === 'png') {
      const resvg = new Resvg(svg, {
        background: themeOptions.bg || '#ffffff',
        fitTo: {
          mode: 'zoom',
          value: 4.0 // 4x scale for ultra high-res pixel density
        }
      });
      const pngData = resvg.render();
      const pngBuffer = pngData.asPng();
      
      const width = pngData.width;
      const height = pngData.height;
      const aspectRatio = width / height;

      await fs.writeFile(outputPath, pngBuffer);
      console.log(`Successfully exported PNG to: ${path.resolve(outputPath)}`);
      console.log(`\n[AGENT GUIDANCE] SUCCESS. Mermaid diagram compiled and exported to PNG: ${outputPath}.`);
      
      let hasWarning = false;
      if (aspectRatio > 2.5 || aspectRatio < 0.4) {
        console.warn(`\n\x1b[33m[AGENT GUIDANCE - WARNING] Extreme Aspect Ratio Detected\x1b[0m`);
        console.warn(`The rendered image has an extreme aspect ratio (width/height = ${aspectRatio.toFixed(2)}). Width: ${width}px, Height: ${height}px.`);
        console.warn(`This often makes text unreadable when scaled to fit a document.`);
        console.warn(`RECOMMENDATION: Modify the Mermaid code to balance the layout. Try using nested subgraphs with different directions (e.g., 'direction RL' inside a 'flowchart TD' graph) or introducing line breaks in long node texts.`);
        hasWarning = true;
      }
      
      if (width < 1500 && height < 1500) {
        console.warn(`\n\x1b[33m[AGENT GUIDANCE - WARNING] Low Resolution Detected\x1b[0m`);
        console.warn(`The rendered image resolution is low (${width}x${height}). It may not be crisp enough for high-DPI displays.`);
        hasWarning = true;
      }
    }
  } catch (error: any) {
    console.error("Error exporting diagram:", error.message || error);
    console.error("\n[AGENT GUIDANCE — FALLBACK STRATEGY]");
    console.error("1. FALLBACK: Render failed. Double-check node labels and remove custom styling tags to simplify layout.");
    console.error("2. ESCALATE: If it continues to fail, export the raw .mmd code and skip compilation, relying on downstream rendering.");
    process.exit(1);
  }
}

run();
