import * as fs from 'fs';
import * as path from 'path';

interface ImageAsset {
  alt: string;
  url: string; // 原始路径
  title?: string;
  sourceFile: string;
}

// 核心匹配逻辑：编辑距离模糊匹配及包含匹配
function fuzzyMatch(str1: string, str2: string): boolean {
  const s1 = str1.toLowerCase().trim();
  const s2 = str2.toLowerCase().trim();
  
  if (!s1 || !s2) return false;
  if (s1.includes(s2) || s2.includes(s1)) return true;
  
  // 简单编辑距离实现
  const track = Array(s2.length + 1).fill(null).map(() =>
    Array(s1.length + 1).fill(null));
  for (let i = 0; i <= s1.length; i += 1) track[0][i] = i;
  for (let j = 0; j <= s2.length; j += 1) track[j][0] = j;
  for (let j = 1; j <= s2.length; j += 1) {
    for (let i = 1; i <= s1.length; i += 1) {
      const indicator = s1[i - 1] === s2[j - 1] ? 0 : 1;
      track[j][i] = Math.min(
        track[j][i - 1] + 1, // deletion
        track[j - 1][i] + 1, // insertion
        track[j - 1][i - 1] + indicator // substitution
      );
    }
  }
  const distance = track[s2.length][s1.length];
  const maxLength = Math.max(s1.length, s2.length);
  const similarity = 1 - distance / maxLength;
  return similarity > 0.65; // 相似度大于 65%
}

// 递归扫描所有的 markdown 文件
function scanMarkdownFiles(dir: string, excludeDirs: string[] = []): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  
  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat && stat.isDirectory()) {
      const baseName = path.basename(filePath);
      if (
        !baseName.startsWith('.') && 
        baseName !== 'node_modules' && 
        !excludeDirs.includes(filePath)
      ) {
        results = results.concat(scanMarkdownFiles(filePath, excludeDirs));
      }
    } else if (filePath.endsWith('.md')) {
      // 排除规划文件和候选清单本身，防止循环扫描
      if (!filePath.endsWith('.plan.md') && !filePath.endsWith('.cand.md')) {
        results.push(filePath);
      }
    }
  });
  
  return results;
}

// 主资产收割函数
export function harvestAssets(
  workspaceDir: string, 
  targetArticlePath: string, 
  keyword: string,
  candLogPath: string
) {
  console.log(`[START] 开始扫描工作区: ${workspaceDir}`);
  console.log(`[INFO] 检索关键词: "${keyword}"`);
  console.log(`[INFO] 目标文章: ${targetArticlePath}`);
  
  const mdFiles = scanMarkdownFiles(workspaceDir);
  console.log(`[INFO] 扫描到候选 Markdown 文件数: ${mdFiles.length}`);
  
  const imagesFound: ImageAsset[] = [];
  
  // 匹配 ![alt](url "title") 的正则
  // 兼容单引号、双引号及无引号 url
  const mdImageRegex = /!\[(.*?)\]\((.*?)(?:\s+["'](.*?)["'])?\)/g;
  
  mdFiles.forEach(file => {
    // 不要自己扫描自己
    if (path.resolve(file) === path.resolve(targetArticlePath)) return;
    
    try {
      const content = fs.readFileSync(file, 'utf8');
      let match;
      // 重置正则的 lastIndex
      mdImageRegex.lastIndex = 0;
      
      while ((match = mdImageRegex.exec(content)) !== null) {
        imagesFound.push({
          alt: match[1] || '',
          url: match[2] || '',
          title: match[3],
          sourceFile: file
        });
      }
    } catch (e) {
      console.warn(`[WARN] 无法读取文件: ${file}, 错误: ${(e as Error).message}`);
    }
  });
  
  console.log(`[INFO] 共发现图片引用数: ${imagesFound.length}`);
  
  let matchCount = 0;
  // 确保目标文章的 images/ 文件夹存在
  const targetDir = path.dirname(targetArticlePath);
  const destImagesDir = path.join(targetDir, 'images');
  
  imagesFound.forEach(img => {
    const isAltMatch = fuzzyMatch(img.alt, keyword);
    const isTitleMatch = img.title ? fuzzyMatch(img.title, keyword) : false;
    
    if (isAltMatch || isTitleMatch) {
      // 计算图片在磁盘上的绝对路径
      let sourceImgPath = '';
      if (img.url.startsWith('http://') || img.url.startsWith('https://')) {
        // 远程图片无需物理复制，但可以记录
        return;
      } else {
        sourceImgPath = path.resolve(path.dirname(img.sourceFile), img.url);
      }
      
      if (fs.existsSync(sourceImgPath) && fs.statSync(sourceImgPath).isFile()) {
        if (!fs.existsSync(destImagesDir)) {
          fs.mkdirSync(destImagesDir, { recursive: true });
        }
        
        const fileExt = path.extname(sourceImgPath);
        const articleSlug = path.basename(targetArticlePath, '.md');
        const uniqueSuffix = `${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        const newFileName = `${articleSlug}-${uniqueSuffix}${fileExt}`;
        const destImgPath = path.join(destImagesDir, newFileName);
        
        try {
          // 1. 物理复制图片
          fs.copyFileSync(sourceImgPath, destImgPath);
          matchCount++;
          
          // 2. 将此记录写入候选清单中
          const relativeUrlToCand = path.relative(path.dirname(candLogPath), destImgPath);
          const titlePart = img.title ? ` "${img.title}"` : '';
          const markdownLine = `*   本地匹配候选：![${img.alt}](${relativeUrlToCand}${titlePart}) (源自: [${path.basename(img.sourceFile)}](file://${img.sourceFile}))\n`;
          fs.appendFileSync(candLogPath, markdownLine);
          
          console.log(`[MATCH] 命中并复制: ${img.alt} -> images/${newFileName}`);
        } catch (copyErr) {
          console.error(`[ERROR] 复制文件失败: ${sourceImgPath}, 错误: ${(copyErr as Error).message}`);
        }
      } else {
        console.warn(`[WARN] 物理图片不存在或无法访问: ${sourceImgPath}`);
      }
    }
  });
  
  console.log(`[FINISHED] 扫描完成。共匹配并复制了 ${matchCount} 张图片。`);
  
  // 打印 Agent 引导，遵守 Structured Output Protocol
  if (matchCount > 0) {
    console.log(`\n[AGENT GUIDANCE] SUCCESS. Harvested ${matchCount} local candidate(s) to: ${candLogPath}.`);
    console.log(`[AGENT GUIDANCE] Next: Open the candidate log, compare these local files with web search results, select the best evidence, and record your final choice in *.cand.md.`);
  } else {
    console.log(`\n[AGENT GUIDANCE — FALLBACK STRATEGY]`);
    console.log(`1. FALLBACK: No local match found. Proceed to Web Search & Retrieval channel to retrieve remote assets.`);
    console.log(`2. ESCALATE: If both fail, report to the user or request manual upload placeholder.`);
  }
}

// 允许命令行直接运行
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 4) {
    console.error('使用方法: node scripts/harvest-assets.ts <workspaceDir> <targetArticlePath> <keyword> <candLogPath>');
    process.exit(1);
  }
  
  const [workspaceDir, targetArticlePath, keyword, candLogPath] = args;
  
  // 确保日志文件存在
  if (!fs.existsSync(candLogPath)) {
    fs.writeFileSync(candLogPath, `# 🔍 本地资产匹配候选清单 (Local Image Matches)\n\n对于关键词: "${keyword}"\n\n`, 'utf8');
  }
  
  harvestAssets(
    path.resolve(workspaceDir),
    path.resolve(targetArticlePath),
    keyword,
    path.resolve(candLogPath)
  );
}
