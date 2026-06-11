import { analyzeImage } from './llm.js';
import fs from 'fs/promises';
import path from 'path';

async function downloadImageFile(url: string, destDir: string, filename: string): Promise<void> {
  const headers: Record<string, string> = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  };

  const response = await fetch(url, { headers });
  console.log(`Fetch OK: ${response.ok}, Status: ${response.status}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.mkdir(destDir, { recursive: true });
  await fs.writeFile(path.join(destDir, filename), buffer);
  console.log(`Saved to ${path.join(destDir, filename)}, size: ${buffer.length}`);
}

async function main() {
  const testUrl = 'https://mmbiz.qpic.cn/mmbiz_jpg/DlicUgzw0fWpquZ9sYKsAClgWaSmotlLNSE1rTSktqsLVEC3skgia4Qo2YrRV0ZGPicW0LUAqlMAmoibhok7tXtY6A/0?wx_fmt=jpeg';
  try {
    await downloadImageFile(testUrl, './test_download_dir', 'test_img.jpg');
  } catch (err: any) {
    console.error('Download error:', err.message);
  }
}

main();
