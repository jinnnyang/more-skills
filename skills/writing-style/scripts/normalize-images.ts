/**
 * @fileoverview Main entry point for markdown normalization.
 * This standalone tool normalizes markdown by:
 * 1. Completing missing alt text and title for images using multimodal LLM
 * 2. Adding proper spacing between CJK characters and English/numbers
 * 3. Inferring missing programming language for code blocks
 * 4. Adding YAML frontmatter if missing
 */

import fs from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { processMarkdown } from './processor.js';

/**
 * Main entry point for the normalization script.
 * @remarks Reads input markdown, processes it, writes output.
 * Expects command line arguments: {@code node cli.js <input.md> [output.md]}
 * When output is omitted, overwrites input in-place.
 */
async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node cli.js <input.md> [output.md]');
    console.error('  If output.md is omitted, overwrites input in-place');
    process.exit(1);
  }

  const inputPath = path.resolve(args[0]);
  const outputPath = args[1] ? path.resolve(args[1]) : inputPath;

  if (!existsSync(inputPath)) {
    console.error(`[ERROR] Input file not found: ${inputPath}`);
    process.exit(1);
  }

  console.log(`[INFO] Normalizing markdown: ${inputPath}`);
  console.log(`[INFO] Output will be written to: ${outputPath}`);

  try {
    // Read input markdown from disk
    const content = await fs.readFile(inputPath, 'utf-8');
    
    // Process markdown with default options for writing-style:
    // - skip download: keep original image URLs
    // - force: false = don't overwrite existing alt/title
    const processed = await processMarkdown(
      content,
      inputPath,
      outputPath,
      undefined,
      undefined,
      true,
      false
    );

    // Write processed markdown to output
    await fs.writeFile(outputPath, processed, 'utf-8');
    
    console.log('\n[SUCCESS] Markdown normalization completed!');
    console.log('  - Missing image alt/title have been completed');
    console.log('  - Text formatting and spacing has been normalized');
    console.log('  - Code block languages have been inferred');
    console.log(`  - Output saved to: ${outputPath}`);
    process.exit(0);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error('\n[AGENT GUIDANCE]');
    console.error(`[ERROR] Normalization failed: ${message}`);
    console.error('1. Check that dependencies are installed: run npm install in this directory');
    console.error('2. Check that skills/writing-style/.env has valid OPENAI_API_KEY');
    console.error('3. Verify network connectivity to the LLM API endpoint');
    process.exit(1);
  }
}

// Start execution
main();
