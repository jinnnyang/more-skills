import fs from 'fs/promises';
import path from 'path';
import { processMarkdown } from './processor.js';

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log(`
Usage: npx tsx scripts/cli.ts <input.md> [output.md]

Formats a markdown file by:
- Automatically generating alt/title texts for images via LLM
- Inferring missing languages for code blocks via LLM
- Fixing typography and CJK spacing

Output defaults to the input file (in-place modification) if no output file is specified.
    `);
    process.exit(0);
  }

  const inputFile = args.find(arg => !arg.startsWith('-'));
  if (!inputFile) {
    console.error('Error: Input file must be specified.');
    process.exit(1);
  }
  const skipDownload = args.includes('--no-assets');
  const deleteOriginal = args.includes('--delete-original');
  
  // Find output file (second non-flag argument)
  const nonFlagArgs = args.filter(arg => !arg.startsWith('-'));
  const outputFile = nonFlagArgs[1];

  try {
    const inputPath = path.resolve(process.cwd(), inputFile);
    console.log(`[INFO] Reading ${inputPath}...`);
    const content = await fs.readFile(inputPath, 'utf-8');

    const docExt = path.extname(inputPath);
    const docBase = path.basename(inputPath, docExt);
    
    let outputMarkdownPath: string;
    let assetsDir: string;
    let isFolderized = false;
    let originalFileToDelete: string | null = null;
    
    if (outputFile) {
      const outputPath = path.resolve(process.cwd(), outputFile);
      const outExt = path.extname(outputPath);
      const outBase = path.basename(outputPath, outExt);
      if (outBase.toLowerCase() === 'index') {
        outputMarkdownPath = outputPath;
        assetsDir = path.join(path.dirname(outputPath), 'assets');
      } else {
        const outputFolder = path.join(path.dirname(outputPath), outBase);
        outputMarkdownPath = path.join(outputFolder, 'index.md');
        assetsDir = path.join(outputFolder, 'assets');
      }
    } else {
      // In-place conversion
      if (docBase.toLowerCase() === 'index') {
        outputMarkdownPath = inputPath;
        assetsDir = path.join(path.dirname(inputPath), 'assets');
      } else {
        const outputFolder = path.join(path.dirname(inputPath), docBase);
        outputMarkdownPath = path.join(outputFolder, 'index.md');
        assetsDir = path.join(outputFolder, 'assets');
        isFolderized = true;
        originalFileToDelete = inputPath;
      }
    }



    console.log(`[INFO] Processing markdown...`);
    const formatted = await processMarkdown(content, inputPath, outputMarkdownPath, assetsDir, './assets', skipDownload, isFolderized);

    if (formatted === content && outputMarkdownPath === inputPath) {
      console.log(`[INFO] Document is already processed. Skipping write.`);
    } else {
      // Ensure target folder exists
      await fs.mkdir(path.dirname(outputMarkdownPath), { recursive: true });
      await fs.writeFile(outputMarkdownPath, formatted, 'utf-8');
    }

    // Clean up original file if folderized in-place and --delete-original is present
    if (isFolderized && originalFileToDelete && deleteOriginal) {
      try {
        await fs.unlink(originalFileToDelete);
        console.log(`[INFO] Cleaned up original file: ${originalFileToDelete}`);
      } catch (err: any) {
        console.warn(`[WARNING] Could not delete original file: ${err.message}`);
      }
    } else if (isFolderized && originalFileToDelete) {
      console.log(`[INFO] Kept original file: ${originalFileToDelete} (use --delete-original to remove)`);
    }

    console.log(`\n[AGENT GUIDANCE]`);
    console.log(`SUCCESS. The markdown file was formatted and saved to ${outputMarkdownPath}.`);
    console.log(`Next: Review the formatted output if needed, or inform the user that the file has been successfully pretty-printed.`);
    
  } catch (err: any) {
    console.error(`\n[AGENT GUIDANCE - FALLBACK STRATEGY]`);
    console.error(`1. FALLBACK: Check if the OPENAI_API_KEY is correctly set in the environment or in the .env file.`);
    console.error(`2. ESCALATE: If there is a syntax error in the script or a parsing failure, review the error message: ${err.message}`);
    process.exit(1);
  }
}

main();
