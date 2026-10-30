"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  Award,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  RotateCcw,
  BookOpen,
  ArrowRight,
  Loader2,
  AlertCircle,
  Target,
  Check,
} from "lucide-react";
import { fetchAttemptReview, MockTestAttemptResult } from "@/services/mock-tests";
import { BackButton } from "@/components/navigation/back-button";

export default function TestResultPage({
  params,
}: {
  params: Promise<{ id: string; attemptId: string }>;
}) {
  const resolvedParams = use(params);
  const { id: testId, attemptId } = resolvedParams;

  const [result, setResult] = useState<MockTestAttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAttemptReview(testId, attemptId)
      .then(setResult)
      .catch((err) => {
        console.error("Failed to load result", err);
        setError("Unable to load test result review.");
      })
      .finally(() => setLoading(false));
  }, [testId, attemptId]);

  if (loading) {
    return (
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12 border border-[var(--border)]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
        <p className="text-sm font-medium text-[var(--text-secondary)]">Compiling official exam evaluation...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="editorial-card p-12 text-center space-y-4 max-w-md mx-auto my-12 border border-[var(--border)]">
        <AlertCircle className="w-10 h-10 mx-auto text-[var(--danger)]" />
        <h3 className="headline text-xl font-bold text-[var(--text-primary)]">Result Unavailable</h3>
        <p className="body-copy text-sm text-[var(--text-secondary)]">{error || "Attempt record not found."}</p>
        <Link href="/mock-tests" className="button-base button-primary text-xs px-4 py-2 inline-block font-semibold">
          Return to Mock Test Centre
        </Link>
      </div>
    );
  }

  const minutesTaken = Math.floor(result.time_taken_seconds / 60);
  const secondsTaken = result.time_taken_seconds % 60;
  const totalQuestions = result.review.length;
  const correctCount = totalQuestions - result.incorrect_count - result.unanswered_count;

  return (
    <div className="max-w-5xl mx-auto space-y-8 page-enter">
      <BackButton fallbackHref="/mock-tests" />

      {/* Hero Scorecard */}
      <div className="editorial-card p-6 md:p-8 space-y-6 border border-[var(--border)] shadow-xs bg-[var(--surface)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[var(--border)] pb-6">
          <div className="space-y-1.5">
            <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
              EXAMINATION RESULTS
            </span>
            <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
              Performance Summary
            </h1>
            <p className="body-copy text-xs text-[var(--text-muted)]">
              Completed on {new Date(result.submitted_at).toLocaleDateString()} at{" "}
              {new Date(result.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[var(--surface-muted)] p-4 rounded-2xl border border-[var(--border)] self-start md:self-auto shadow-xs">
            <div className="w-14 h-14 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-xs">
              <Award className="w-7 h-7" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                Final Score
              </span>
              <div className="text-3xl font-bold font-serif text-[var(--accent)]">
                {result.score}
                <span className="text-base text-[var(--text-secondary)] font-normal"> / {totalQuestions}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Bento KPI Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)]">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">
              Accuracy
            </span>
            <span className="text-2xl font-bold text-[var(--success)] font-serif">{result.accuracy}%</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)]">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">
              Correct
            </span>
            <span className="text-2xl font-bold text-[var(--success)] font-serif">{correctCount}</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)]">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">
              Incorrect
            </span>
            <span className="text-2xl font-bold text-[var(--danger)] font-serif">{result.incorrect_count}</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)]">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">
              Time Taken
            </span>
            <span className="text-2xl font-bold text-[var(--text-primary)] font-serif">
              {minutesTaken}m {secondsTaken}s
            </span>
          </div>
        </div>

        {/* Quick action triggers */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-[var(--border)]">
          <Link
            href="/revision"
            className="text-xs font-semibold text-[var(--accent)] hover:underline flex items-center gap-1.5"
          >
            <BookOpen className="w-4 h-4" />
            <span>Review Missed Concepts in Mistake Book</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          <Link
            href={`/mock-tests/${testId}`}
            className="button-base button-secondary text-xs px-4 py-2 flex items-center gap-1.5 font-semibold"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retake Test</span>
          </Link>
        </div>
      </div>

      {/* Answer Review Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <h2 className="headline text-xl font-bold text-[var(--text-primary)]">
            Detailed Solution Review
          </h2>
          <span className="text-xs text-[var(--text-muted)]">
            {result.review.length} Questions Evaluated
          </span>
        </div>

        <div className="space-y-6">
          {result.review.map((item, idx) => {
            return (
              <div
                key={item.question_id}
                className="editorial-card p-6 space-y-4 border border-[var(--border)] bg-[var(--surface)] shadow-xs"
              >
                {/* Status Indicator */}
                <div className="flex items-center justify-between text-xs border-b border-[var(--border)] pb-3">
                  <span className="font-bold text-[var(--accent)] font-mono">
                    QUESTION {idx + 1}
                  </span>

                  <span
                    className={`flex items-center gap-1.5 font-semibold text-xs px-2.5 py-1 rounded-md ${
                      item.is_correct
                        ? "bg-[var(--success-soft)] text-[var(--success)] border border-[color-mix(in_srgb,var(--success)_30%,var(--border))]"
                        : item.selected_answer
                        ? "bg-[var(--danger-soft)] text-[var(--danger)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))]"
                        : "bg-[var(--warning-soft)] text-amber-700 border border-amber-300"
                    }`}
                  >
                    {item.is_correct ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" /> Correct (+1.0)
                      </>
                    ) : item.selected_answer ? (
                      <>
                        <XCircle className="w-3.5 h-3.5" /> Incorrect
                      </>
                    ) : (
                      <>
                        <HelpCircle className="w-3.5 h-3.5" /> Unanswered / Skipped
                      </>
                    )}
                  </span>
                </div>

                {/* Question Text */}
                <h3 className="text-base font-bold text-[var(--text-primary)] leading-relaxed">
                  {item.question_text}
                </h3>

                {/* Options List */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {item.options.map((opt, optIdx) => {
                    const letter = String.fromCharCode(65 + optIdx);
                    const isSelected = item.selected_answer === letter;
                    const isAnswer = item.correct_answer === letter;

                    let style = "bg-[var(--surface-muted)] border-[var(--border)] text-[var(--text-secondary)]";
                    if (isAnswer) {
                      style = "bg-[var(--success-soft)] border-[color-mix(in_srgb,var(--success)_40%,var(--border))] text-[var(--success)] font-semibold";
                    } else if (isSelected && !item.is_correct) {
                      style = "bg-[var(--danger-soft)] border-[color-mix(in_srgb,var(--danger)_40%,var(--border))] text-[var(--danger)] font-semibold";
                    }

                    return (
                      <div
                        key={optIdx}
                        className={`p-3.5 rounded-xl border flex items-start gap-3 transition-colors ${style}`}
                      >
                        <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 bg-[var(--surface)] border border-[var(--border)]">
                          {letter}
                        </span>
                        <span className="flex-1 leading-snug pt-0.5">
                          {opt.replace(/^[A-D][.)]\s*/i, "")}
                        </span>
                        {isAnswer && <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0 mt-0.5" />}
                        {isSelected && !isAnswer && <XCircle className="w-4 h-4 text-[var(--danger)] shrink-0 mt-0.5" />}
                      </div>
                    );
                  })}
                </div>

                {/* Academic Rationale Explanation */}
                {item.explanation && (
                  <div className="mt-4 p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] space-y-1.5 text-xs md:text-sm">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-[var(--accent)]">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Academic Rationale & Verification</span>
                    </div>
                    <p className="text-[var(--text-secondary)] leading-relaxed">{item.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
