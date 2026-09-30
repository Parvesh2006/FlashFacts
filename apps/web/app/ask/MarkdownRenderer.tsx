import React from 'react';

export function MarkdownRenderer({ content }: { content: string }) {
  if (!content) return null;

  const isQuiz = content.includes("### Current Affairs Practice Quiz");

  if (isQuiz) {
    return <QuizRenderer content={content} />;
  }

  return <EventRenderer content={content} />;
}

function QuizRenderer({ content }: { content: string }) {
  const parts = content.split('**Q').filter(Boolean);
  const questions = parts.slice(1);

  return (
    <div className="space-y-6 text-[15px] leading-relaxed text-[var(--text-primary)] w-full">
      <h3 className="text-xl font-semibold text-[var(--brand-primary)] border-b border-[var(--brand-primary-border)] pb-3 mb-6 uppercase tracking-wider text-sm">
        Current Affairs Practice Quiz
      </h3>

      <div className="space-y-6">
        {questions.map((q, idx) => {
          const lines = q.split('\n').map(l => l.trim()).filter(Boolean);
          const firstLine = lines[0]; 
          let questionText = firstLine.replace(/\*\*$/, '').trim();
          
          const options = [];
          let correctAnswer = '';
          let explanation = '';
          
          for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            if (line.match(/^[A-D]\)/)) {
              options.push(line);
            } else if (line.startsWith('**Correct Answer:')) {
              correctAnswer = line.replace(/\*\*Correct Answer:\s*/i, '').replace(/\*\*$/, '').trim();
            } else if (line.startsWith('**Explanation:**')) {
              explanation = line.replace(/\*\*Explanation:\*\*\s*/i, '').trim();
            } else if (explanation !== '') {
              explanation += ' ' + line;
            }
          }

          return (
            <div key={idx} className="bg-[var(--surface-muted)] border border-[var(--surface-border)] rounded-xl p-5 md:p-6 shadow-sm">
              <h4 className="font-semibold text-[var(--text-primary)] mb-4 text-base">
                Question {questionText}
              </h4>
              <div className="space-y-3 mb-5">
                {options.map((opt, oIdx) => (
                  <div key={oIdx} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full border border-[var(--surface-border)] flex-shrink-0 mt-0.5 flex items-center justify-center bg-[var(--background-primary)]">
                    </div>
                    <span className="text-[var(--text-secondary)]">{opt}</span>
                  </div>
                ))}
              </div>
              
              {(correctAnswer || explanation) && (
                <div className="mt-4 pt-4 border-t border-[var(--surface-border)]">
                  {correctAnswer && (
                    <div className="mb-2">
                      <span className="font-semibold text-[var(--brand-primary)] uppercase text-xs tracking-wider">Answer: </span>
                      <span className="font-medium text-[var(--text-primary)]">{correctAnswer}</span>
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
  const blocks = content.split(/(?=\n\*\*\d+\.)/);
  const headerBlock = blocks[0];
  const eventBlocks = blocks.slice(1);

  let title = "Current Affairs Response";
  const titleMatch = headerBlock.match(/### (.*)/);
  if (titleMatch) {
    title = titleMatch[1];
  }
  
  let priorityLabel = null;
  if (headerBlock.includes("🔴 **HIGH PRIORITY**")) {
    priorityLabel = "HIGH PRIORITY";
  } else if (headerBlock.includes("🟠 **IMPORTANT DEVELOPMENTS**")) {
    priorityLabel = "IMPORTANT DEVELOPMENTS";
  }

  if (eventBlocks.length === 0) {
    return (
      <div className="space-y-4 text-[15px] leading-relaxed text-[var(--text-primary)]">
        {content.split('\n\n').map((para, i) => {
          if (para.startsWith('###')) return <h3 key={i} className="text-xl font-semibold text-[var(--brand-primary)] uppercase tracking-wider text-sm mb-2">{para.replace(/### /, '')}</h3>;
          return <p key={i} className="whitespace-pre-wrap">{para}</p>;
        })}
      </div>
    );
  }

  return (
    <div className="space-y-6 text-[15px] leading-relaxed text-[var(--text-primary)] w-full">
      {title && (
        <h3 className="text-xl font-semibold text-[var(--text-primary)] border-b border-[var(--surface-border)] pb-3 mb-6 uppercase tracking-wider text-sm">
          {title.replace(/\(.*\)/, '').trim()}
        </h3>
      )}

      <div className="space-y-6">
        {eventBlocks.map((block, idx) => {
          const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
          let headline = lines[0].replace(/^\*\*\d+\.\s*/, '').replace(/\*\*$/, '');
          
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
               const catMatch = line.match(/\*Category: (.*?) \| Date: (.*?)\*/);
               if (catMatch) {
                 examFact = catMatch[1];
                 source = catMatch[2];
               }
            } else {
               if (!whatHappened && !line.startsWith('**')) {
                 whatHappened += (whatHappened ? ' ' : '') + line;
               }
            }
          }

          return (
            <div key={idx} className="bg-[var(--surface-muted)] border border-[var(--surface-border)] rounded-xl overflow-hidden shadow-sm">
              
              {priorityLabel && idx === 0 && (
                <div className="bg-[var(--brand-primary-soft)] border-b border-[var(--brand-primary-border)] px-5 py-2.5 flex items-center gap-2">
                   <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-pulse"></span>
                   <span className="text-[10px] font-bold text-[var(--brand-primary)] tracking-widest uppercase">{priorityLabel}</span>
                </div>
              )}

              <div className="p-5 md:p-6 space-y-5">
                <h4 className="font-semibold text-lg text-[var(--text-primary)] leading-snug">
                  {headline}
                </h4>

                {whatHappened && (
                  <div>
                    <h5 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">What Happened</h5>
                    <p className="text-[var(--text-secondary)] text-[15px]">{whatHappened}</p>
                  </div>
                )}

                {whyItMatters && (
                  <div>
                    <h5 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">Why It Matters</h5>
                    <p className="text-[var(--text-secondary)] text-[15px]">{whyItMatters}</p>
                  </div>
                )}
              </div>

              {(examFact || relevantExams || source) && (
                <div className="bg-[var(--background-secondary)] border-t border-[var(--surface-border)] px-5 py-3.5 flex flex-col md:flex-row md:items-center gap-3 justify-between">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-[var(--text-secondary)] font-medium text-[13px]">
                    {examFact && (
                      <span className="flex items-center gap-1.5 bg-[var(--surface-muted)] px-2.5 py-1 rounded-md border border-[var(--surface-border)]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-primary)]"></span>
                        {examFact.replace('Domain: ', '').replace(' | Category: ', ' · ')}
                      </span>
                    )}
                    {relevantExams && (
                      <span className="flex items-center gap-1.5">
                         {relevantExams}
                      </span>
                    )}
                  </div>
                  {source && (
                    <div className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer text-[13px] font-medium bg-[var(--surface-hover)] px-2.5 py-1 rounded-md border border-[var(--surface-border)]">
                      <span>📰 {source}</span>
                      <span className="text-[10px] opacity-70">↗</span>
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
