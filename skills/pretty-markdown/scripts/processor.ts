import { MarkdownParser, MarkdownRender } from 'md2ast';
import type { AnyNode, Image, CodeBlock, Text } from 'md2ast/dist/ast';
import { analyzeImage, inferCodeLanguage, extractGlobalMetadata } from './llm.js';
import type { Heading, Yaml } from 'md2ast/dist/ast';
import pangu from 'pangu';
import fs from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * Download a remote image with anti-scraping headers and save to destPath.
 * Returns the final extension determined from content-type or URL.
 */
async function downloadImageFile(url: string, destDir: string, baseNameWithoutExt: string, usedNames: Set<string>): Promise<string> {
  const headers: Record<string, string> = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  };

  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const contentType = response.headers.get('content-type') || '';
  let ext = '';
  if (contentType.includes('image/jpeg')) ext = '.jpg';
  else if (contentType.includes('image/png')) ext = '.png';
  else if (contentType.includes('image/gif')) ext = '.gif';
  else if (contentType.includes('image/webp')) ext = '.webp';
  else if (contentType.includes('image/svg+xml')) ext = '.svg';
  else {
    // try to extract from URL path
    try {
      const urlPath = new URL(url).pathname;
      ext = path.extname(urlPath) || '.png';
    } catch {
      ext = '.png';
    }
  }

  // Get unique filename
  let filename = `${baseNameWithoutExt}${ext}`;
  let counter = 1;
  while (usedNames.has(filename.toLowerCase())) {
    filename = `${baseNameWithoutExt}_${counter}${ext}`;
    counter++;
  }
  usedNames.add(filename.toLowerCase());

  const fullPath = path.join(destDir, filename);
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.writeFile(fullPath, buffer);
  
  return filename;
}

/**
 * Perform typography cleanup on a text string:
 * 1. Convert ASCII quotes to typographic quotes
 * 2. Add spaces between CJK and English/Numbers
 */
function cleanText(text: string): string {
  if (!text) return text;
  
  let cleaned = text.replace(/"([^"]*)"/g, '“$1”');
  cleaned = cleaned.replace(/「([^」]*)」/g, '“$1”');

  return pangu.spacing(cleaned);
}

/**
 * Traverse the AST recursively and execute a callback for each node.
 */
function traverse(node: AnyNode, callback: (node: AnyNode, parent?: AnyNode) => void, parent?: AnyNode) {
  callback(node, parent);
  if ('children' in node && Array.isArray(node.children)) {
    for (const child of node.children) {
      traverse(child as AnyNode, callback, node);
    }
  }
}

export async function processMarkdown(
  content: string, 
  inputMarkdownPath?: string,
  outputMarkdownPath?: string, 
  assetsDir?: string, 
  relativeAssetsDir?: string, 
  skipDownload: boolean = false,
  force: boolean = false
): Promise<string> {
  const parser = new MarkdownParser();
  const ast = parser.parse(content);
  const lines = content.split('\n');

  const hasYaml = ast.children && ast.children[0]?.type === 'yaml';

  interface ImageTask {
    img: Image;
    contextText: string;
  }

  const imagesToAnalyze: ImageTask[] = [];
  const codeBlocksToInfer: CodeBlock[] = [];

  // Step 1: Collect tasks and extract title
  let codeTitle = '';
  if (ast.children) {
    for (const child of ast.children) {
      if (child.type === 'heading' && (child as Heading).depth === 1) {
        // Simple extraction of heading text
        const h1 = child as Heading;
        const textNode = h1.children?.find(c => c.type === 'text') as Text;
        if (textNode) codeTitle = textNode.value;
        break;
      }
    }
  }

  traverse(ast, (node) => {
    if (node.type === 'image') {
      const img = node as Image;
      // If missing descriptive alt text or title, queue for analysis
      if (!img.alt || img.alt.trim().length < 5 || !img.title) {
        let contextText = '';
        if (typeof img.line_num === 'number') {
          const start = Math.max(0, img.line_num - 5);
          const end = Math.min(lines.length - 1, img.line_num + 5);
          const contextLines = lines.slice(start, end + 1).filter((_, i) => (start + i) !== img.line_num);
          contextText = contextLines.join('\n').trim();
        }
        imagesToAnalyze.push({ img, contextText });
      }
    } else if (node.type === 'code') {
      const code = node as CodeBlock;
      // If language marker is missing, queue for inference
      if (!code.lang || code.lang.trim() === '') {
        codeBlocksToInfer.push(code);
      }
    }
  });

  let docLanguage = 'text';

  if (!hasYaml) {
    console.log(`[INFO] Document Title detected as: ${codeTitle || 'None'}`);
    console.log(`[INFO] Extracting global metadata and detecting language...`);
    const globalMeta = await extractGlobalMetadata(content, codeTitle);
    docLanguage = globalMeta.language || 'text';
    console.log(`[INFO] Detected Language: ${docLanguage}`);

    const yamlValue = `title: "${globalMeta.title || codeTitle || ''}"\ndescription: "${globalMeta.description || ''}"\nkeywords: "${globalMeta.keywords || ''}"\nauthor: "${globalMeta.author || ''}"\nlanguage: "${docLanguage}"`;
    if (ast.children) {
      ast.children.unshift({ type: 'yaml', value: yamlValue } as Yaml);
    }
  } else {
    console.log(`[INFO] Document already has YAML frontmatter. Skipping metadata extraction.`);
    const yamlNode = ast.children![0] as Yaml;
    const langMatch = yamlNode.value.match(/lang(?:uage)?:\s*(.+)/i);
    if (langMatch) {
      docLanguage = langMatch[1].trim().replace(/['"]/g, '');
    }
  }

  console.log(`[INFO] Found ${imagesToAnalyze.length} images to analyze and ${codeBlocksToInfer.length} code blocks to infer.`);

  // Step 2: Execute API Calls in parallel (using batching to prevent rate limits)
  async function processInBatches<T>(items: T[], batchSize: number, processFn: (item: T) => Promise<void>) {
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);
      await Promise.all(batch.map(processFn));
    }
  }

  await processInBatches(imagesToAnalyze, 3, async (task) => {
    console.log(`[INFO] Analyzing image: ${task.img.url}`);
    const res = await analyzeImage(task.img.url, docLanguage, task.contextText);
    if (res.alt) task.img.alt = res.alt;
    if (res.title) task.img.title = res.title;
  });

  await processInBatches(codeBlocksToInfer, 3, async (code) => {
    console.log(`[INFO] Inferring code language...`);
    const lang = await inferCodeLanguage(code.value);
    if (lang && lang !== 'text') {
      code.lang = lang;
    }
  });

  // Step 3: Download remote images and rewrite paths if requested
  if (!skipDownload && assetsDir && relativeAssetsDir) {
    try {
      // Create assets folder
      await fs.mkdir(assetsDir, { recursive: true });

      const usedFilenames = new Set<string>();
      const allImages: Image[] = [];
      traverse(ast, (node) => {
        if (node.type === 'image') {
          allImages.push(node as Image);
        }
      });

      for (const img of allImages) {
        // If it's a remote URL, download it
        if (img.url.startsWith('http://') || img.url.startsWith('https://') || img.url.startsWith('//')) {
          const urlToFetch = img.url.startsWith('//') ? `https:${img.url}` : img.url;
          
          // Clean title to form baseline filename
          const cleanTitle = (img.title || img.alt || 'image')
            .replace(/[\\/:*?"<>|]/g, '_')
            .trim();
          
          console.log(`[INFO] Downloading remote image to local assets: ${img.url}`);
          try {
            const filename = await downloadImageFile(urlToFetch, assetsDir, cleanTitle, usedFilenames);
            // Update URL in AST to relative local path
            img.url = `${relativeAssetsDir}/${filename}`;
          } catch (dlError: any) {
            console.error(`[WARNING] Failed to download image ${img.url}: ${dlError.message}. Retaining original URL.`);
          }
        } else if (inputMarkdownPath) {
          // If it's a local file relative to the original input file, and we are folderizing, copy it to the new assetsDir
          try {
            // Resolve path relative to input file directory
            const srcPath = path.resolve(path.dirname(inputMarkdownPath), img.url);
            if (existsSync(srcPath)) {
              const cleanTitle = (img.title || img.alt || path.basename(srcPath, path.extname(srcPath)))
                .replace(/[\\/:*?"<>|]/g, '_')
                .trim();
              const ext = path.extname(srcPath);
              
              let filename = `${cleanTitle}${ext}`;
              let counter = 1;
              while (usedFilenames.has(filename.toLowerCase())) {
                filename = `${cleanTitle}_${counter}${ext}`;
                counter++;
              }
              usedFilenames.add(filename.toLowerCase());
              
              const destPath = path.join(assetsDir, filename);
              await fs.copyFile(srcPath, destPath);
              img.url = `${relativeAssetsDir}/${filename}`;
              console.log(`[INFO] Copied local asset from ${srcPath} to ${destPath}`);
            }
          } catch (copyError: any) {
            console.warn(`[WARNING] Failed to copy local asset ${img.url}: ${copyError.message}`);
          }
        }
      }
    } catch (fsError: any) {
      console.error(`[ERROR] Failed to set up local assets directory: ${fsError.message}`);
    }
  }

  // Step 4: Clean up nodes (Typography and Structure)
  traverse(ast, (node) => {
    if (node.type === 'text') {
      const textNode = node as Text;
      textNode.value = cleanText(textNode.value);
    }
  });

  // Step 5: Render back to Markdown
  const renderer = new MarkdownRender();
  return renderer.render(ast);
}
