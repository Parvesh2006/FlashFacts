const fs = require('fs');
let lines = fs.readFileSync('app/ask/page.tsx', 'utf8').split('\n');

lines[140] = '                className={`flex items-start gap-4 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}';
lines[143] = '                  className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${msg.sender === "user" ? "bg-[var(--text-primary)] text-[var(--background-primary)]" : "bg-[var(--brand-primary)] text-white shadow-lg shadow-[var(--brand-primary)]/20"}`}';
lines[149] = '                  className={`max-w-[90%] md:max-w-[850px] ${msg.sender === "user" ? "bg-[var(--surface-muted)] border border-[var(--surface-border)] rounded-2xl rounded-tr-sm p-4 md:p-5" : "pt-1"}`}';

fs.writeFileSync('app/ask/page.tsx', lines.join('\n'));
console.log('Done replacement by line numbers using literal single quotes.');
