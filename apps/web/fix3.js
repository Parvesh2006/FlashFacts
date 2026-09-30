const fs = require('fs');
let content = fs.readFileSync('app/ask/page.tsx', 'utf8');

content = content.replace(/className=\{[\s\S]*?lex items-start gap-4 \}/g, 'className={lex items-start gap-4 \}');
content = content.replace(/className=\{w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 \}/g, 'className={w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 \}');
content = content.replace(/className=\{max-w-\[90%\] md:max-w-\[850px\] \}/g, 'className={max-w-[90%] md:max-w-[850px] \}');

fs.writeFileSync('app/ask/page.tsx', content);
console.log('Done replacement using regex.');
