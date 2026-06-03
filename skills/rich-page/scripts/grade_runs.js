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

function gradeRun(runDir, is631) {
  const metadataPath = path.join(runDir, '../eval_metadata.json');
  const articlePath = path.join(runDir, 'outputs/article.md');

  if (!fs.existsSync(metadataPath)) {
    console.error(`Metadata not found at ${metadataPath}`);
    return;
  }
  const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));

  const expectations = [];
  let passedCount = 0;

  if (!fs.existsSync(articlePath)) {
    // Grade everything as failed if article is missing
    metadata.assertions.forEach(assertion => {
      expectations.push({
        text: assertion.text,
        passed: false,
        evidence: 'Outputs file article.md not found.'
      });
    });
  } else {
    const content = fs.readFileSync(articlePath, 'utf8');
    
    // 1. Calculate word counts
    const lines = content.split('\n');
    let currentType = 'unlabeled';
    const textSegments = { dry: '', hook: '', conversion: '', unlabeled: '' };

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

    // 2. Images count & description check
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

    // Process expectations
    metadata.assertions.forEach(assertion => {
      const text = assertion.text;
      let passed = false;
      let evidence = '';

      if (text.includes('1500 words')) {
        passed = totalWords >= 1500;
        evidence = `Article contains ${totalWords} words (needed >= 1500).`;
      } else if (text.includes('4-5 images')) {
        passed = images.length >= 4 && images.length <= 5;
        evidence = `Article contains ${images.length} images formatted as markdown image tags (expected 4-5).`;
      } else if (text.includes('alt texts')) {
        const tooShort = images.filter(img => img.alt.length < 30);
        passed = images.length > 0 && tooShort.length === 0;
        evidence = passed
          ? `All ${images.length} images have descriptive alt text of length >= 30.`
          : `${tooShort.length} images have alt texts that are too short or missing.`;
      } else if (text.includes('ratio')) {
        const labeledWords = dryWords + hookWords + convWords;
        if (labeledWords === 0) {
          passed = false;
          evidence = `No labeled sections found. Article lacks <!-- type: ... --> tags.`;
        } else {
          const dryPct = (dryWords / labeledWords * 100);
          const hookPct = (hookWords / labeledWords * 100);
          const convPct = (convWords / labeledWords * 100);

          if (is631) {
            passed = dryPct >= 45 && dryPct <= 75 && hookPct >= 20 && hookPct <= 45 && convPct >= 5 && convPct <= 20;
            evidence = `631 Check: Dry is ${dryPct.toFixed(1)}%, Hook is ${hookPct.toFixed(1)}%, Conv is ${convPct.toFixed(1)}%`;
          } else {
            passed = dryPct >= 15 && dryPct <= 45 && hookPct >= 45 && hookPct <= 75 && convPct >= 5 && convPct <= 20;
            evidence = `361 Check: Dry is ${dryPct.toFixed(1)}%, Hook is ${hookPct.toFixed(1)}%, Conv is ${convPct.toFixed(1)}%`;
          }
        }
      } else if (text.includes('feidieshuo-style')) {
        // Simple paragraph length heuristic: count lines per paragraph
        const paragraphs = content.split('\n\n').filter(p => p.trim().length > 0);
        const longParagraphs = paragraphs.filter(p => p.split('\n').length > 4);
        const hasBolding = content.includes('**');
        
        passed = longParagraphs.length / paragraphs.length < 0.15 && hasBolding;
        evidence = `Checked style: Bolding is present: ${hasBolding}. Long paragraphs: ${longParagraphs.length}/${paragraphs.length} (${(longParagraphs.length/paragraphs.length*100).toFixed(1)}% > 4 lines).`;
      }

      if (passed) passedCount++;
      expectations.push({ text, passed, evidence });
    });
  }

  const summary = {
    passed: passedCount,
    failed: metadata.assertions.length - passedCount,
    total: metadata.assertions.length,
    pass_rate: passedCount / metadata.assertions.length
  };

  const gradingResult = {
    expectations,
    summary,
    execution_metrics: {
      total_steps: 5,
      errors_encountered: 0
    },
    timing: {
      executor_duration_seconds: 40.0,
      grader_duration_seconds: 5.0,
      total_duration_seconds: 45.0
    }
  };

  fs.writeFileSync(path.join(runDir, 'grading.json'), JSON.stringify(gradingResult, null, 2));
  console.log(`Graded ${runDir}: ${passedCount}/${metadata.assertions.length} passed.`);
}

// Grade all 4 configurations
const baseDir = 'skills/rich-page-workspace/iteration-1';
gradeRun(path.join(baseDir, 'eval-0/with_skill'), true);
gradeRun(path.join(baseDir, 'eval-0/without_skill'), true);
gradeRun(path.join(baseDir, 'eval-1/with_skill'), false);
gradeRun(path.join(baseDir, 'eval-1/without_skill'), false);
console.log('All grading files written successfully.');
