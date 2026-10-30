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
    <div className="space-y-6 text-sm leading-relaxed text-[var(--text-primary)] w-full">
      <div className="border-b border-[var(--border)] pb-2.5 mb-4 flex items-center justify-between">
        <span className="badge-editorial text-xs font-semibold text-[var(--accent)] border-[var(--accent)]">
          PRACTICE COMPREHENSION DRILL
        </span>
        <span className="text-xs text-[var(--text-muted)] font-mono">{questions.length} Questions</span>
      </div>

      <div className="space-y-5">
        {questions.map((q, idx) => {
          const lines = q.split('\n').map(l => l.trim()).filter(Boolean);
          const firstLine = lines[0];
          const questionText = firstLine.replace(/\*\*$/, '').trim();

          const options: string[] = [];
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
            <div key={idx} className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 shadow-xs space-y-4">
              <h4 className="font-bold text-[var(--text-primary)] text-sm md:text-base leading-snug">
                <span className="text-[var(--accent)] font-mono mr-2">Q{idx + 1}.</span>
                {questionText.replace(/^\d+[\.\)]\s*/, '')}
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {options.map((opt, oIdx) => {
                  const letter = String.fromCharCode(65 + oIdx);
                  const cleanText = opt.replace(/^[A-D]\)\s*/, '');
                  return (
                    <div key={oIdx} className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] flex items-start gap-2.5 text-xs">
                      <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-[var(--surface)] border border-[var(--border)] shrink-0 text-[var(--text-secondary)]">
                        {letter}
                      </span>
                      <span className="text-[var(--text-primary)] leading-snug pt-0.5">{cleanText}</span>
                    </div>
                  );
                })}
              </div>

              {(correctAnswer || explanation) && (
                <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-2">
                  {correctAnswer && (
                    <div className="text-xs">
                      <span className="font-semibold text-[var(--success)] uppercase tracking-wider text-[11px]">Correct Answer: </span>
                      <span className="font-bold text-[var(--text-primary)]">{correctAnswer}</span>
                    </div>
                  )}
                  {explanation && (
                    <div className="p-3 rounded-lg bg-[var(--surface-muted)] border border-[var(--border)] text-xs text-[var(--text-secondary)] leading-relaxed">
                      <span className="font-semibold text-[var(--accent)] block mb-1">Academic Rationale</span>
                      <p>{explanation}</p>
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
      <div className="space-y-3 text-sm leading-relaxed text-[var(--text-primary)]">
        {content.split('\n\n').map((para, i) => {
          if (para.startsWith('###')) {
            return (
              <h3 key={i} className="text-base font-bold text-[var(--accent)] uppercase tracking-wider mb-2">
                {para.replace(/### /, '')}
              </h3>
            );
          }
          return <p key={i} className="whitespace-pre-wrap leading-relaxed">{para}</p>;
        })}
      </div>
    );
  }

  return (
    <div className="space-y-5 text-sm leading-relaxed text-[var(--text-primary)] w-full">
      {title && (
        <div className="border-b border-[var(--border)] pb-2.5 mb-3 flex items-center justify-between">
          <h3 className="headline text-base font-bold text-[var(--text-primary)] tracking-tight">
            {title.replace(/\(.*\)/, '').trim()}
          </h3>
          {priorityLabel && (
            <span className="badge-editorial text-[10px] text-[var(--danger)] border-[var(--danger)] font-semibold">
              {priorityLabel}
            </span>
          )}
        </div>
      )}

      <div className="space-y-4">
        {eventBlocks.map((block, idx) => {
          const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
          const headline = lines[0].replace(/^\*\*\d+\.\s*/, '').replace(/\*\*$/, '');

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
            <div key={idx} className="bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden shadow-xs">
              <div className="p-5 space-y-4">
                <h4 className="headline font-bold text-base text-[var(--text-primary)] leading-snug">
                  {headline}
                </h4>

                {whatHappened && (
                  <div>
                    <h5 className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                      Event Summary
                    </h5>
                    <p className="text-[var(--text-secondary)] text-xs md:text-sm leading-relaxed">{whatHappened}</p>
                  </div>
                )}

                {whyItMatters && (
                  <div>
                    <h5 className="text-[10px] font-semibold text-[var(--accent)] uppercase tracking-wider mb-1">
                      Exam Relevance & Why It Matters
                    </h5>
                    <p className="text-[var(--text-secondary)] text-xs md:text-sm leading-relaxed">{whyItMatters}</p>
                  </div>
                )}
              </div>

              {(examFact || relevantExams || source) && (
                <div className="bg-[var(--surface-muted)] border-t border-[var(--border)] px-5 py-3 flex flex-wrap items-center gap-3 justify-between text-xs text-[var(--text-secondary)]">
                  <div className="flex flex-wrap items-center gap-2">
                    {examFact && (
                      <span className="badge-editorial text-[10px] text-[var(--text-primary)] border-[var(--border)] bg-[var(--surface)] font-medium">
                        {examFact.replace('Domain: ', '').replace(' | Category: ', ' · ')}
                      </span>
                    )}
                    {relevantExams && (
                      <span className="badge-editorial text-[10px] text-[var(--accent)] border-[var(--accent)]">
                        {relevantExams}
                      </span>
                    )}
                  </div>
                  {source && (
                    <span className="text-[11px] text-[var(--text-muted)] font-mono">
                      📰 {source}
                    </span>
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
