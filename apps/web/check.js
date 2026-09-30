const fs = require('fs');
let lines = fs.readFileSync('app/ask/page.tsx', 'utf8').split('\n');

for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('className={')) {
    console.log(i + ': ' + lines[i]);
  }
}
