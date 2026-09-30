const fs = require('fs');
let lines = fs.readFileSync('app/ask/page.tsx', 'utf8').split('\n');

for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('className={') && lines[i].includes('lex items-start gap-4 }')) {
    lines[i] = '                className={lex items-start gap-4 }';
  }
  if (lines[i].includes('className={w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 }')) {
    lines[i] = '                  className={w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 }';
  }
  if (lines[i].includes('className={max-w-[90%] md:max-w-[850px] }')) {
    lines[i] = '                  className={max-w-[90%] md:max-w-[850px] }';
  }
}

fs.writeFileSync('app/ask/page.tsx', lines.join('\n'));
