import fs from 'fs/promises';
import path from 'path';

async function main() {
  const waitingDir = path.resolve('../waiting');
  const items = await fs.readdir(waitingDir);
  for (const item of items) {
    const codes = Array.from(item).map(c => c.charCodeAt(0)).join(',');
    console.log(`${item} -> [${codes}]`);
  }
}

main();
