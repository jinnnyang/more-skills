#!/usr/bin/env node
/**
 * @fileoverview CLI entry point for normalize-images.
 * Auto-installs dependencies if node_modules is missing and invokes TypeScript via tsx.
 * @copyright Follows same pattern as pretty-markdown for consistency.
 */

import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

// 1. Check if node_modules exists, if not, run npm install
if (!fs.existsSync(path.join(__dirname, 'node_modules'))) {
  console.log('Dependencies for normalize-images not found. Installing...');
  const npmInstall = spawnSync(npmCmd, ['install'], {
    cwd: __dirname,
    stdio: 'inherit',
    shell: true
  });
  if (npmInstall.status !== 0) {
    console.error('\n[AGENT GUIDANCE - FALLBACK STRATEGY]');
    console.error('1. FALLBACK: Run npm install inside this directory manually to check for network/permission errors.');
    console.error('2. ESCALATE: Review package.json to ensure dependencies are valid.');
    process.exit(npmInstall.status || 1);
  }
}

// 2. Run the TypeScript entry file using tsx
const args = process.argv.slice(2);
const cliPath = path.join(__dirname, 'normalize-images.ts');
const runResult = spawnSync(npxCmd, ['tsx', cliPath, ...args], {
  stdio: 'inherit',
  shell: true // Important for npx resolution on Windows
});

if (runResult.error) {
  console.error('\n[AGENT GUIDANCE - FALLBACK STRATEGY]');
  console.error(`[ERROR] ${runResult.error.message}`);
  process.exit(1);
}

process.exit(runResult.status !== null ? runResult.status : 0);
