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
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12">
        <Loader2 className="w-8 h-8 animate-spin accent-mark" />
        <p className="body-copy font-mono text-sm">Compiling exam score analysis...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="editorial-card p-12 text-center space-y-4 max-w-md mx-auto my-12">
        <AlertCircle className="w-10 h-10 mx-auto text-rose-500" />
        <h3 className="headline text-xl">Result Unavailable</h3>
        <p className="body-copy text-sm">{error || "Attempt record not found."}</p>
        <Link href="/mock-tests" className="brand-button text-xs font-mono px-4 py-2 inline-block">
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
    <div className="max-w-5xl mx-auto space-y-8">
      <BackButton fallbackHref="/mock-tests" />

      {/* Hero Scorecard */}
      <div className="editorial-card p-6 md:p-8 space-y-6 bg-gradient-to-br from-[var(--surface-elevated)] to-[var(--surface)] border-[var(--border-subtle)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b pb-6">
          <div className="space-y-1">
            <span className="eyebrow text-xs">OFFICIAL TEST RESULT</span>
            <h1 className="headline text-3xl md:text-4xl">Performance Summary</h1>
            <p className="body-copy text-sm">
              Submitted on {new Date(result.submitted_at).toLocaleDateString()} at{" "}
              {new Date(result.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[var(--surface)] p-4 rounded-2xl border shadow-sm self-start md:self-auto">
            <div className="w-14 h-14 rounded-xl brand-button flex items-center justify-center">
              <Award className="w-7 h-7" />
            </div>
            <div>
              <span className="text-xs font-mono text-[var(--text-secondary)] block">FINAL SCORE</span>
              <div className="text-3xl font-bold font-mono text-[var(--brand-primary)]">
                {result.score}
                <span className="text-base text-[var(--text-secondary)] font-normal"> / {totalQuestions}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono">
          <div className="p-4 rounded-xl bg-[var(--surface)] border">
            <span className="text-xs text-[var(--text-secondary)] block">ACCURACY</span>
            <span className="text-2xl font-bold text-emerald-600">{result.accuracy}%</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface)] border">
            <span className="text-xs text-[var(--text-secondary)] block">CORRECT ANSWERS</span>
            <span className="text-2xl font-bold text-emerald-600">{correctCount}</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface)] border">
            <span className="text-xs text-[var(--text-secondary)] block">INCORRECT</span>
            <span className="text-2xl font-bold text-rose-500">{result.incorrect_count}</span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--surface)] border">
            <span className="text-xs text-[var(--text-secondary)] block">TIME TAKEN</span>
            <span className="text-2xl font-bold text-[var(--text-primary)]">
              {minutesTaken}m {secondsTaken}s
            </span>
          </div>
        </div>

        {/* Quick action triggers */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t">
          <Link
            href="/revision"
            className="text-xs font-mono text-[var(--brand-primary)] hover:underline flex items-center gap-1.5"
          >
            <BookOpen className="w-4 h-4" />
            <span>View Mistakes in Mistake Book →</span>
          </Link>

          <Link
            href={`/mock-tests/${testId}`}
            className="brand-button text-xs font-mono px-4 py-2 flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retake This Test</span>
          </Link>
        </div>
      </div>

      {/* Answer Review Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="headline text-xl">Question-by-Question Review</h2>
          <span className="text-xs font-mono text-[var(--text-secondary)]">
            {result.review.length} Questions Scored
          </span>
        </div>

        <div className="space-y-6">
          {result.review.map((item, idx) => {
            return (
              <div
                key={item.question_id}
                className="editorial-card p-6 space-y-4 border-[var(--border-subtle)]"
              >
                {/* Status Indicator */}
                <div className="flex items-center justify-between font-mono text-xs border-b pb-3">
                  <span className="font-bold text-[var(--brand-primary)]">QUESTION {idx + 1}</span>

                  <span
                    className={`flex items-center gap-1.5 font-bold px-2.5 py-1 rounded-md ${
                      item.is_correct
                        ? "bg-emerald-500/10 text-emerald-600"
                        : item.selected_answer
                        ? "bg-rose-500/10 text-rose-600"
                        : "bg-amber-500/10 text-amber-600"
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
                        <HelpCircle className="w-3.5 h-3.5" /> Skipped / Unanswered
                      </>
                    )}
                  </span>
                </div>

                {/* Question Text */}
                <h3 className="text-base font-semibold text-[var(--text-primary)] leading-relaxed">
                  {item.question_text}
                </h3>

                {/* Options List with Evaluation Styling */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {item.options.map((opt, optIdx) => {
                    const letter = String.fromCharCode(65 + optIdx);
                    const isSelected = item.selected_answer === letter;
                    const isAnswer = item.correct_answer === letter;

                    let style = "bg-[var(--surface)] border text-[var(--text-secondary)]";
                    if (isAnswer) {
                      style = "bg-emerald-500/10 border-emerald-500 text-emerald-700 dark:text-emerald-300 font-semibold";
                    } else if (isSelected && !item.is_correct) {
                      style = "bg-rose-500/10 border-rose-500 text-rose-700 dark:text-rose-300 font-semibold";
                    }

                    return (
                      <div
                        key={optIdx}
                        className={`p-3.5 rounded-xl border flex items-start gap-3 transition-colors ${style}`}
                      >
                        <span className="font-mono text-xs mt-0.5 opacity-80">{letter})</span>
                        <span className="flex-1 leading-snug">{opt.replace(/^[A-D][.)]\s*/i, "")}</span>
                        {isAnswer && <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />}
                        {isSelected && !isAnswer && <XCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />}
                      </div>
                    );
                  })}
                </div>

                {/* Explanation */}
                {item.explanation && (
                  <div className="mt-4 p-4 rounded-xl bg-[var(--surface-elevated)] border border-[var(--border-subtle)] space-y-1.5 text-sm">
                    <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-[var(--brand-primary)]">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Explanation & Academic Rational</span>
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
