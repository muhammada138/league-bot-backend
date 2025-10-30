// parse.js
// Uses the local rofl-parser build to convert .rofl → metadata JSON

const { ROFLReader } = require('./rofl-parser/dist/index.js');
const fs = require('fs');
const [,, input, output] = process.argv;

(async () => {
  try {
    const reader   = new ROFLReader(input);
    const metadata = reader.getMetadata();
    fs.writeFileSync(output, JSON.stringify(metadata, null, 2));
    console.log(`✅ Parsed ${input} → ${output}`);
  } catch (err) {
    console.error("Parsing failed:", err);
    process.exit(1);
  }
})();
