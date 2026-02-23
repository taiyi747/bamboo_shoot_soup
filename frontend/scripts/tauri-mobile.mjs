#!/usr/bin/env node

import { spawnSync } from 'node:child_process'

const [target, action] = process.argv.slice(2)

if (!target || !action) {
  console.error('Usage: bun scripts/tauri-mobile.mjs <ios|android> <init|dev|build>')
  process.exit(1)
}

if (target === 'ios' && process.platform !== 'darwin') {
  console.log('Skip iOS command: iOS build chain requires macOS + Xcode.')
  process.exit(0)
}

const result = spawnSync('bun', ['run', 'tauri', target, action], {
  stdio: 'inherit',
  shell: process.platform === 'win32',
})

if (typeof result.status === 'number') {
  process.exit(result.status)
}

process.exit(1)
