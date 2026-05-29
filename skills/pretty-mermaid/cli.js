#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const scriptsDir = path.join(__dirname, 'scripts');
const distDir = path.join(scriptsDir, 'dist');
const distCliPath = path.join(distDir, 'cli.js');

const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';

// 1. Check if node_modules exists, if not, run npm install
if (!fs.existsSync(path.join(scriptsDir, 'node_modules'))) {
  console.log('Dependencies for pretty-mermaid not found. Installing...');
  const npmInstall = spawnSync(npmCmd, ['install'], {
    cwd: scriptsDir,
    stdio: 'inherit',
    shell: true
  });
  if (npmInstall.status !== 0) {
    console.error('Failed to install dependencies.');
    process.exit(npmInstall.status || 1);
  }
}

// 2. Check if dist/cli.js exists, if not, build it using tsc
if (!fs.existsSync(distCliPath)) {
  console.log('Building TypeScript scripts...');
  const npmBuild = spawnSync(npmCmd, ['run', 'build'], {
    cwd: scriptsDir,
    stdio: 'inherit',
    shell: true
  });
  if (npmBuild.status !== 0) {
    console.error('Failed to build scripts.');
    process.exit(npmBuild.status || 1);
  }
}

// 3. Run dist/cli.js using node directly (shell: false prevents arg mangling).
// Omit cwd to keep the user's terminal working directory, allowing relative output paths to resolve correctly.
const args = process.argv.slice(2);
const runResult = spawnSync(process.execPath, [distCliPath, ...args], {
  stdio: 'inherit',
  shell: false
});

if (runResult.error) {
  console.error('Failed to start cli process:', runResult.error.message);
  process.exit(1);
}

process.exit(runResult.status !== null ? runResult.status : 0);
