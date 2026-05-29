import fs from 'fs/promises';
import path from 'path';
import { renderMermaidSVG, THEMES } from 'beautiful-mermaid';
import { Resvg } from '@resvg/resvg-js';

async function exportDiagram() {
  const args = process.argv.slice(2);
  let inputCode = '';
  let outputPath = 'output.svg';
  let format = 'svg';
  let theme = 'zinc-light'; // Default theme

  // Simple argument parsing
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '-i' || args[i] === '--input') {
      const inputPath = args[++i];
      try {
        inputCode = await fs.readFile(inputPath, 'utf8');
      } catch (e) {
        console.error(`Error reading input file: ${inputPath}`);
        process.exit(1);
      }
    } else if (args[i] === '-o' || args[i] === '--output') {
      outputPath = args[++i];
      format = outputPath.toLowerCase().endsWith('.png') ? 'png' : 'svg';
    } else if (args[i] === '-t' || args[i] === '--theme') {
      theme = args[++i];
    } else if (!inputCode && !args[i].startsWith('-')) {
      // Assume it's direct code if not a flag and inputCode is empty
      inputCode = args[i];
    }
  }

  // Read from stdin if no input provided
  if (!inputCode && !process.stdin.isTTY) {
    try {
      const chunks = [];
      for await (const chunk of process.stdin) {
        chunks.push(chunk);
      }
      inputCode = Buffer.concat(chunks).toString('utf8');
    } catch (err) {
      console.error("Error reading from stdin:", err);
    }
  }

  if (!inputCode || !inputCode.trim()) {
    console.error("Error: No Mermaid code provided.");
    console.error("Usage: tsx export.ts -i <input.mmd> -o <output.svg|png> [-t <theme>]");
    console.error("Available themes: zinc-light, zinc-dark, tokyo-night, dracula, github-light, github-dark, etc.");
    process.exit(1);
  }

  try {
    // Get theme options
    const themeOptions = THEMES[theme as keyof typeof THEMES] || THEMES['zinc-light'];

    // Render SVG using beautiful-mermaid
    const svg = renderMermaidSVG(inputCode, themeOptions);

    if (format === 'svg') {
      await fs.writeFile(outputPath, svg, 'utf8');
      console.log(`Successfully exported SVG to ${outputPath}`);
    } else if (format === 'png') {
      const resvg = new Resvg(svg, {
        background: themeOptions.bg || '#ffffff',
        fitTo: {
          mode: 'width',
          value: 1200 // Default width for good resolution
        }
      });
      const pngData = resvg.render();
      const pngBuffer = pngData.asPng();
      await fs.writeFile(outputPath, pngBuffer);
      console.log(`Successfully exported PNG to ${outputPath}`);
    }
  } catch (error: any) {
    console.error("Error exporting diagram:", error.message || error);
    process.exit(1);
  }
}

exportDiagram();
