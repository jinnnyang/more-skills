#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const scriptsDir = path.join(__dirname, 'scripts');
const searchPath = path.join(scriptsDir, 'search.ts');

const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

// 1. Check if node_modules exists, if not, run npm install
if (!fs.existsSync(path.join(scriptsDir, 'node_modules'))) {
  console.log('Dependencies for search-web not found. Installing...');
  const npmInstall = spawnSync(npmCmd, ['install'], {
    cwd: scriptsDir,
    stdio: 'inherit',
    shell: true
  });
  if (npmInstall.status !== 0) {
    console.error('\n[AGENT GUIDANCE - FALLBACK STRATEGY]');
    console.error('1. FALLBACK: Run npm install inside the scripts directory manually to check for network/permission errors.');
    console.error('2. ESCALATE: Review package.json to ensure dependencies are valid.');
    process.exit(npmInstall.status || 1);
  }
}

// 2. Run search.ts using tsx
const args = process.argv.slice(2);
const runResult = spawnSync(npxCmd, ['tsx', searchPath, ...args], {
  stdio: 'inherit',
  shell: process.platform === 'win32' // Use shell only on Windows for npx.cmd
});

if (runResult.error) {
  console.error('\n[AGENT GUIDANCE - FALLBACK STRATEGY]');
  console.error(`1. FALLBACK: Check if tsx or node configuration is broken: ${runResult.error.message}`);
  process.exit(1);
}

process.exit(runResult.status !== null ? runResult.status : 0);
