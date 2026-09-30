const fs = require('fs');
let lines = fs.readFileSync('app/ask/page.tsx', 'utf8').split('\n');

lines[140] = '                className={lex items-start gap-4 }';
lines[143] = '                  className={w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 }';
lines[149] = '                  className={max-w-[90%] md:max-w-[850px] }';

fs.writeFileSync('app/ask/page.tsx', lines.join('\n'));
console.log('Done replacement by line numbers.');
