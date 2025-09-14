#!/usr/bin/env node
const fs = require('fs');
try {
  require.resolve('js-yaml');
} catch (e) {
  console.error('js-yaml not installed. Run: npm install -D js-yaml');
  process.exit(0);
}
const yaml = require('js-yaml');

const [,, inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  console.error('Usage: json_to_yaml.js <input.json> <output.yaml>');
  process.exit(1);
}
try {
  const data = JSON.parse(fs.readFileSync(inPath, 'utf8'));
  fs.writeFileSync(outPath, yaml.dump(data));
  console.log(`Wrote ${outPath}`);
} catch (err) {
  console.error('Conversion failed:', err.message);
  process.exit(1);
}
