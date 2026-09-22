import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const forbidden = [
  /--model\b/i,
  /privatecloudcomput/i,
  /node:http/,
  /https?:\/\//,
  /requestSampling/,
  /oauth/i,
];

async function files(root) {
  const found = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) found.push(...await files(full));
    else if (/\.(ts|json)$/.test(entry.name)) found.push(full);
  }
  return found;
}

const violations = [];
for (const file of await files('src')) {
  const source = await readFile(file, 'utf8');
  for (const pattern of forbidden) {
    if (pattern.test(source)) violations.push(`${file}: ${pattern}`);
  }
}

if (violations.length) {
  console.error(violations.join('\n'));
  process.exitCode = 1;
}
