import os

markdown_renderer_code = \"\"\"import React from 'react';

export function MarkdownRenderer({ content }: { content: string }) {
  // If no content, just return empty
  if (!content) return null;

  // We want to detect MCQ format vs Standard Event format
  const isQuiz = content.includes("### Current Affairs Practice Quiz");

  if (isQuiz) {
    return <QuizRenderer content={content} />;
  }

  return <EventRenderer content={content} />;
}

function QuizRenderer({ content }: { content: string }) {
  // Split by questions: "**Q"
  const parts = content.split('**Q').filter(Boolean);
  
  const headerPart = parts[0];
  const questions = parts.slice(1);

  return (
    <div className="space-y-6 text-[15px] leading-relaxed text-[var(--text-primary)]">
      {/* Title */}
      <h3 className="text-xl font-semibold text-[var(--brand-primary)] border-b border-[var(--brand-primary-border)] pb-3 mb-6 uppercase tracking-wider text-sm">
        Current Affairs Practice
      </h3>

      <div className="space-y-6">
        {questions.map((q, idx) => {
          // Parse question block
          // Looks like: 1. Which of the following...?**\nA) ...\nB) ...\nC) ...\nD) ...\n**Correct Answer: A**\n**Explanation:** ...
          const lines = q.split('\\n').map(l => l.trim()).filter(Boolean);
          const firstLine = lines[0]; // e.g., "1. Which of the following...?**"
          
          let questionText = firstLine.replace(/\\*\\*$/, '').trim();
          
          const options = [];
          let correctAnswer = '';
          let explanation = '';
          
          for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            if (line.match(/^[A-D]\\)/)) {
              options.push(line);
            } else if (line.startsWith('**Correct Answer:')) {
              correctAnswer = line.replace(/\\*\\*Correct Answer:\\s*/i, '').replace(/\\*\\*$/, '').trim();
            } else if (line.startsWith('**Explanation:**')) {
              explanation = line.replace(/\\*\\*Explanation:\\*\\*\\s*/i, '').trim();
            } else if (explanation !== '') {
              explanation += ' ' + line;
            }
          }

          return (
            <div key={idx} className="bg-[var(--surface-muted)] border border-[var(--brand-primary-border)] rounded-xl p-5 md:p-6 shadow-sm">
              <h4 className="font-semibold text-[var(--text-primary)] mb-4 text-base">
                Question {questionText}
              </h4>
              <div className="space-y-3 mb-5">
                {options.map((opt, oIdx) => (
                  <div key={oIdx} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full border border-[var(--text-muted)] flex-shrink-0 mt-0.5 flex items-center justify-center">
                       {/* empty circle */}
                    </div>
                    <span className="text-[var(--text-secondary)]">{opt}</span>
                  </div>
                ))}
              </div>
              
              {(correctAnswer || explanation) && (
                <div className="mt-4 pt-4 border-t border-[var(--brand-primary-border)] border-opacity-50">
                  {correctAnswer && (
                    <div className="mb-2">
                      <span className="font-semibold text-[var(--brand-primary)] uppercase text-xs tracking-wider">Answer: </span>
                      <span className="font-medium">{correctAnswer}</span>
                    </div>
                  )}
                  {explanation && (
                    <div>
                      <span className="font-semibold text-[var(--brand-primary)] uppercase text-xs tracking-wider block mb-1">Explanation</span>
                      <p className="text-[var(--text-secondary)] text-sm">{explanation}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EventRenderer({ content }: { content: string }) {
  // Try to split into events. The backend uses "**1.", "**2." etc.
  const blocks = content.split(/(?=\\n\\*\\*\\d+\\.)/);
  
  const headerBlock = blocks[0];
  const eventBlocks = blocks.slice(1);

  // Parse header
  let title = "Current Affairs Response";
  const titleMatch = headerBlock.match(/### (.*)/);
  if (titleMatch) {
    title = titleMatch[1];
  }
  
  let priorityLabel = null;
  if (headerBlock.includes("?? **HIGH PRIORITY**")) {
    priorityLabel = "HIGH PRIORITY";
  } else if (headerBlock.includes("?? **IMPORTANT DEVELOPMENTS**")) {
    priorityLabel = "IMPORTANT DEVELOPMENTS";
  }

  // If no structured event blocks were found, fallback to basic text rendering
  if (eventBlocks.length === 0) {
    return (
      <div className="space-y-4 text-[15px] leading-relaxed text-[var(--text-primary)]">
        {content.split('\\n\\n').map((para, i) => {
          if (para.startsWith('###')) return <h3 key={i} className="text-xl font-semibold text-[var(--brand-primary)] uppercase tracking-wider text-sm mb-2">{para.replace(/### /, '')}</h3>;
          return <p key={i}>{para}</p>;
        })}
      </div>
    );
  }

  return (
    <div className="space-y-6 text-[15px] leading-relaxed text-[var(--text-primary)]">
      {title && (
        <h3 className="text-xl font-semibold text-[var(--brand-primary)] border-b border-[var(--brand-primary-border)] pb-3 mb-6 uppercase tracking-wider text-sm">
          {title}
        </h3>
      )}

      {priorityLabel && (
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] rounded-full text-xs font-semibold tracking-widest uppercase mb-4">
          <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-pulse"></span>
          {priorityLabel}
        </div>
      )}

      <div className="space-y-6">
        {eventBlocks.map((block, idx) => {
          const lines = block.split('\\n').map(l => l.trim()).filter(Boolean);
          
          let headline = lines[0].replace(/^\\*\\*\\d+\\.\\s*/, '').replace(/\\*\\*$/, '');
          
          let whatHappened = '';
          let whyItMatters = '';
          let examFact = '';
          let relevantExams = '';
          let source = '';

          for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            if (line.startsWith('**What happened:**')) {
              whatHappened = line.replace('**What happened:**', '').trim();
            } else if (line.startsWith('**Why it matters:**')) {
              whyItMatters = line.replace('**Why it matters:**', '').trim();
            } else if (line.startsWith('**Exam Fact:**')) {
              examFact = line.replace('**Exam Fact:**', '').trim();
            } else if (line.startsWith('**Relevant exams:**')) {
              relevantExams = line.replace('**Relevant exams:**', '').trim();
            } else if (line.startsWith('**Source:**')) {
              source = line.replace('**Source:**', '').trim();
            } else if (line.startsWith('*Category:')) {
               // Fallback short format
               const catMatch = line.match(/\\*Category: (.*?) \\| Date: (.*?)\\*/);
               if (catMatch) {
                 examFact = catMatch[1];
                 source = catMatch[2];
               }
            } else {
               // multiline fallback for What Happened if it's the second line and doesn't match prefixes
               if (!whatHappened && !line.startsWith('**')) {
                 whatHappened = line;
               }
            }
          }

          return (
            <div key={idx} className="bg-[var(--surface-muted)] border border-[var(--brand-primary-border)] rounded-xl overflow-hidden shadow-sm">
              <div className="p-5 md:p-6 space-y-5">
                <h4 className="font-semibold text-lg text-[var(--text-primary)] leading-snug">
                  {headline}
                </h4>

                {whatHappened && (
                  <div>
                    <h5 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">What Happened</h5>
                    <p className="text-[var(--text-secondary)] text-sm">{whatHappened}</p>
                  </div>
                )}

                {whyItMatters && (
                  <div>
                    <h5 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">Why It Matters</h5>
                    <p className="text-[var(--text-secondary)] text-sm">{whyItMatters}</p>
                  </div>
                )}
              </div>

              {/* Footer info area */}
              {(examFact || relevantExams || source) && (
                <div className="bg-[var(--background-secondary)] border-t border-[var(--brand-primary-border)] border-opacity-50 px-5 py-3.5 flex flex-col md:flex-row md:items-center gap-3 text-xs justify-between">
                  
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[var(--text-muted)] font-medium">
                    {examFact && (
                      <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-primary)]"></span>
                        {examFact.replace('Domain: ', '').replace(' | Category: ', ' · ')}
                      </span>
                    )}
                    {relevantExams && (
                      <span className="flex items-center gap-1.5">
                         <span className="opacity-50">|</span> 
                         {relevantExams}
                      </span>
                    )}
                  </div>

                  {source && (
                    <div className="flex items-center gap-2 text-[var(--brand-primary)] font-medium bg-[var(--brand-primary-soft)] px-2.5 py-1 rounded-md">
                      <span>?? {source}</span>
                    </div>
                  )}

                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
\"\"\"

with open('apps/web/app/ask/MarkdownRenderer.tsx', 'w', encoding='utf-8') as f:
    f.write(markdown_renderer_code)
