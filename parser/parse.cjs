// parse.cjs
// Converts a .rofl file → metadata JSON using the local rofl-parser build

const { ROFLReader } = require('./rofl-parser/dist/index.js');
const fs = require('fs');

const [,, input, output] = process.argv;

if (!input || !output) {
  console.error("❌ Usage: node parse.cjs <input.rofl> <output.json>");
  process.exit(1);
}

try {
  console.log(`🚀 Starting parse for ${input}`);
  const reader = new ROFLReader(input);
  const metadata = reader.getMetadata(); // FIXED — no async parse()
  fs.writeFileSync(output, JSON.stringify(metadata, null, 2));
  console.log(`✅ Parsed successfully: ${input} → ${output}`);
} catch (err) {
  console.error("❌ Parsing failed:", err);
  process.exit(1);
}
