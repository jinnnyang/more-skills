const fs = require('fs');
const path = require('path');

function countWords(text) {
  let clean = text
    .replace(/```[\s\S]*?```/g, '') // remove code blocks
    .replace(/`.*?`/g, '') // remove inline code
    .replace(/!\[.*?\]\(.*?\)/g, '') // remove images
    .replace(/\[.*?\]\(.*?\)/g, '') // remove links
    .replace(/<!--[\s\S]*?-->/g, '') // remove comments
    .replace(/[#*_\-`>+\|]/g, '') // remove markdown syntax characters
    .trim();
  
  // Count Chinese characters
  const chineseChars = clean.match(/[\u4e00-\u9fa5]/g) || [];
  // Count English words
  const englishWords = clean.match(/[a-zA-Z0-9'-]+/g) || [];
  
  return chineseChars.length + englishWords.length;
}

function verifyArticle(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found at ${filePath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(filePath, 'utf8');
  
  // 1. Calculate word counts and ratios based on sections
  const lines = content.split('\n');
  let currentType = 'unlabeled';
  const textSegments = {
    dry: '',
    hook: '',
    conversion: '',
    unlabeled: ''
  };

  for (const line of lines) {
    const match = line.match(/<!--\s*type:\s*(\w+)\s*-->/i);
    if (match) {
      const type = match[1].toLowerCase();
      if (textSegments[type] !== undefined) {
        currentType = type;
      }
    } else {
      textSegments[currentType] += line + '\n';
    }
  }

  const dryWords = countWords(textSegments.dry);
  const hookWords = countWords(textSegments.hook);
  const convWords = countWords(textSegments.conversion);
  const unlabeledWords = countWords(textSegments.unlabeled);
  const totalWords = dryWords + hookWords + convWords + unlabeledWords;

  // 2. Parse images
  // Regex supporting alt text, url, and optional title in quotes
  const imgRegex = /!\[([\s\S]*?)\]\((.*?)(?:\s+"([\s\S]*?)")?\)/g;
  const images = [];
  let imgMatch;
  while ((imgMatch = imgRegex.exec(content)) !== null) {
    images.push({
      alt: imgMatch[1].trim(),
      url: imgMatch[2].trim(),
      title: (imgMatch[3] || '').trim()
    });
  }

  // 3. Perform Checks
  const issues = [];
  const passes = [];

  // Word count check
  if (totalWords < 500) {
    issues.push(`[LOW WORD COUNT] Article has only ${totalWords} words. Recommended length is at least 1000-2000 words for deep writing.`);
  } else {
    passes.push(`[WORD COUNT] Total words: ${totalWords}`);
  }

  // Content Ratio evaluation
  if (totalWords > 0) {
    const labeledWords = dryWords + hookWords + convWords;
    if (labeledWords / totalWords < 0.3) {
      issues.push(`[UNLABELED SECTIONS] Only ${(labeledWords / totalWords * 100).toFixed(1)}% of the article is labeled with <!-- type: ... --> comments. Run verification with labeled segments for accurate ratio checks.`);
    } else {
      const dryPct = (dryWords / labeledWords * 100);
      const hookPct = (hookWords / labeledWords * 100);
      const convPct = (convWords / labeledWords * 100);

      // Check if it fits 631 (roughly 50-70% dry, 20-40% hook, 5-15% conv)
      // or 361 (roughly 20-40% dry, 50-70% hook, 5-15% conv)
      const is631 = dryPct > hookPct;
      const trackName = is631 ? '631 (Knowledge/Tech)' : '361 (Emotional/Opinion)';
      
      passes.push(`[TRACK DETECTED] Looks like ${trackName} track: Dry: ${dryPct.toFixed(1)}%, Hook: ${hookPct.toFixed(1)}%, Conversion: ${convPct.toFixed(1)}%`);

      if (is631) {
        if (dryPct < 50 || dryPct > 70) issues.push(`[RATIO WARNING] Dry content ratio (${dryPct.toFixed(1)}%) deviates from ideal 60%`);
        if (hookPct < 20 || hookPct > 40) issues.push(`[RATIO WARNING] Hook/Emotion ratio (${hookPct.toFixed(1)}%) deviates from ideal 30%`);
        if (convPct < 5 || convPct > 15) issues.push(`[RATIO WARNING] Conversion ratio (${convPct.toFixed(1)}%) deviates from ideal 10%`);
      } else {
        if (dryPct < 20 || dryPct > 40) issues.push(`[RATIO WARNING] Dry content ratio (${dryPct.toFixed(1)}%) deviates from ideal 30%`);
        if (hookPct < 50 || hookPct > 70) issues.push(`[RATIO WARNING] Hook/Emotion ratio (${hookPct.toFixed(1)}%) deviates from ideal 60%`);
        if (convPct < 5 || convPct > 15) issues.push(`[RATIO WARNING] Conversion ratio (${convPct.toFixed(1)}%) deviates from ideal 10%`);
      }
    }
  }

  // Image Pacing checks
  if (images.length === 0) {
    issues.push(`[NO IMAGES] No images found. Recommended pacing: 4-5 images for a 2000-word article.`);
  } else {
    passes.push(`[IMAGES COUNT] Found ${images.length} images.`);
    
    // Alt text detail checks (must be detailed for prompt generation)
    images.forEach((img, index) => {
      const isHeader = index === 0;
      const typeLabel = isHeader ? 'Header' : `Image #${index + 1}`;
      
      if (!img.alt) {
        issues.push(`[IMAGE MISSING ALT] ${typeLabel} is missing alt text description.`);
      } else if (img.alt.length < 30) {
        issues.push(`[IMAGE ALT TOO SHORT] ${typeLabel} alt text has only ${img.alt.length} characters. Describe composition, style, color palette, and subject details for text-to-image prompts.`);
      } else {
        passes.push(`[IMAGE ALT OK] ${typeLabel} alt text has detailed description (${img.alt.length} chars).`);
      }

      if (!img.title) {
        issues.push(`[IMAGE MISSING TITLE] ${typeLabel} is missing a title.`);
      }
    });

    // Pacing density check
    const wordsPerImage = totalWords / images.length;
    if (wordsPerImage > 600) {
      issues.push(`[IMAGE SPACING WARNING] Spacing is too sparse. Average words per image: ${Math.round(wordsPerImage)}. Recommended: 350-500 words per image.`);
    } else if (wordsPerImage < 200) {
      issues.push(`[IMAGE SPACING WARNING] Spacing is too dense. Average words per image: ${Math.round(wordsPerImage)}. Ensure text breathes and doesn't look cluttered.`);
    } else {
      passes.push(`[IMAGE SPACING OK] Spacing pacing is good. Average words per image: ${Math.round(wordsPerImage)}.`);
    }
  }

  // Output results
  console.log(`\n=== Verification Report for ${path.basename(filePath)} ===`);
  console.log(`Word Count: ${totalWords} words`);
  console.log(`Dry: ${dryWords} | Hook: ${hookWords} | Conv: ${convWords} | Unlabeled: ${unlabeledWords}`);
  console.log(`Images: ${images.length}`);
  
  if (passes.length > 0) {
    console.log('\n✅ PASSES:');
    passes.forEach(p => console.log(`  - ${p}`));
  }
  
  if (issues.length > 0) {
    console.log('\n⚠️ WARNINGS/ISSUES:');
    issues.forEach(i => console.log(`  - ${i}`));
    process.exit(1);
  } else {
    console.log('\n🎉 ALL CHECKS PASSED SUCCESSFULLY!');
    process.exit(0);
  }
}

// CLI Execution
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: node verify.js <path-to-markdown-file>');
    process.exit(1);
  }
  verifyArticle(args[0]);
}
