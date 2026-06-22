import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const STATE_FILE = path.join(__dirname, '..', '..', '.rate-limit-state.json');
const LOCK_FILE = path.join(__dirname, '..', '..', '.rate-limit.lock');

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function acquireLock(maxRetries = 300): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      // 'wx' flag fails if file already exists (atomic create)
      fs.writeFileSync(LOCK_FILE, process.pid.toString(), { flag: 'wx' });
      return true;
    } catch (err) {
      await sleep(100);
    }
  }
  return false;
}

function releaseLock() {
  try {
    if (fs.existsSync(LOCK_FILE)) {
      fs.unlinkSync(LOCK_FILE);
    }
  } catch (err) {
    // Ignore release errors
  }
}

export async function checkRateLimit(rpmLimit = 20): Promise<void> {
  const intervalMs = Math.ceil(60000 / rpmLimit); // Default: 3000ms for 20 RPM
  const hasLock = await acquireLock();

  if (!hasLock) {
    console.warn('[WARNING] Failed to acquire rate limiter lock. Proceeding with caution...');
  }

  let lastRequestTime = 0;
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      lastRequestTime = data.lastRequestTime || 0;
    }
  } catch (err) {
    // Ignore read/parse errors, default to 0
  }

  const now = Date.now();
  const elapsed = now - lastRequestTime;
  const waitTime = intervalMs - elapsed;

  if (waitTime > 0) {
    await sleep(waitTime);
  }

  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify({ lastRequestTime: Date.now() }), 'utf-8');
  } catch (err) {
    // Ignore write errors
  } finally {
    releaseLock();
  }
}
