import { existsSync } from 'fs';
import path from 'path';

async function main() {
  const waitingDir = path.resolve('../waiting');
  
  // Test Black Myth assets folder
  const assetsFolder = path.join(waitingDir, '《黑神话：悟空》价格定高了吗？_assets');
  console.log(`Folder exists: ${existsSync(assetsFolder)}`);
  
  // Find files in it if it exists
  try {
    const fs = await import('fs/promises');
    const items = await fs.readdir(assetsFolder);
    console.log('Items in folder:', items);
  } catch (err: any) {
    console.error('Error reading folder:', err.message);
  }
}

main();
