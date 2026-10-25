"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  CheckCircle2,
  XCircle,
  Sparkles,
  ArrowRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { fetchPerformanceAnalytics, PerformanceAnalytics } from "@/services/analytics";
import { BackButton } from "@/components/navigation/back-button";
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

export default function AnalyticsPage() {
  const { user, isGuest, createGuestSession } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [data, setData] = useState<PerformanceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPerformanceAnalytics()
      .then(setData)
      .catch((err) => {
        console.error("Failed to fetch analytics", err);
        setError("Unable to compute performance analytics.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12">
        <Loader2 className="w-8 h-8 animate-spin accent-mark" />
        <p className="body-copy font-mono text-sm">Computing database analytics metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="editorial-card p-12 text-center space-y-6 max-w-lg mx-auto my-12">
        <div className="w-12 h-12 rounded-2xl bg-[var(--surface-muted)] flex items-center justify-center mx-auto text-[var(--brand-primary)]">
          <BarChart3 className="w-6 h-6" />
        </div>
        <div className="space-y-2">
          <h3 className="headline text-xl">Aspirant Performance Analytics</h3>
          <p className="body-copy text-sm">
            Complete your first mock test or sign in to compute verified exam readiness, score progressions, and weakness maps.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 font-mono text-xs">
          <Link href="/mock-tests" className="btn btn-primary px-4 py-2 w-full sm:w-auto">
            Browse Mock Tests
          </Link>
          <button
            onClick={() => setIsAuthOpen(true)}
            className="btn btn-secondary px-4 py-2 w-full sm:w-auto"
          >
            Sign In / Register
          </button>
        </div>
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          title="Sign In for Performance Analytics"
          subtitle="Sign in to track verified test accuracy, score progression, and topic-wise mastery."
        />
      </div>
    );
  }

  const hasTests = data.total_tests_completed > 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <BackButton fallbackHref="/exams" />

      {/* Header */}
      <div className="border-b pb-5">
        <div className="eyebrow flex items-center gap-2 mb-2">
          <BarChart3 className="w-4 h-4" />
          <span>Real-Time Performance Engine</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">Performance Analytics</h1>
        <p className="body-copy text-base mt-2 max-w-3xl">
          Track verified mastery, score progression, topic accuracy, and actionable revision targets
          derived exclusively from your actual test submissions and mistake patterns.
        </p>
      </div>

      {/* Guest info banner */}
      {isGuest && (
        <div className="p-4 rounded-xl border border-[color-mix(in_srgb,var(--brand-primary)_35%,transparent)] bg-[color-mix(in_srgb,var(--brand-primary)_8%,transparent)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-[var(--text-primary)]">
            <Sparkles className="w-4 h-4 text-[var(--brand-primary)] flex-shrink-0" />
            <span>
              <strong>Guest Performance:</strong> Test metrics are saved for this local session. Sign in with Google or Email to link your analytics and track continuous improvement.
            </span>
          </div>
          <button
            onClick={() => setIsAuthOpen(true)}
            className="btn btn-primary px-3 py-1.5 text-xs flex-shrink-0 whitespace-nowrap"
          >
            Sign In to Sync
          </button>
        </div>
      )}

      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
        <div className="editorial-card p-5 space-y-1">
          <span className="text-xs text-[var(--text-secondary)] block">TESTS COMPLETED</span>
          <div className="text-3xl font-bold text-[var(--text-primary)]">{data.total_tests_completed}</div>
          <span className="text-[11px] text-[var(--text-secondary)]">Verified test attempts</span>
        </div>

        <div className="editorial-card p-5 space-y-1">
          <span className="text-xs text-[var(--text-secondary)] block">QUESTIONS ATTEMPTED</span>
          <div className="text-3xl font-bold text-[var(--text-primary)]">{data.total_questions_attempted}</div>
          <span className="text-[11px] text-[var(--text-secondary)]">Answered questions</span>
        </div>

        <div className="editorial-card p-5 space-y-1">
          <span className="text-xs text-[var(--text-secondary)] block">OVERALL ACCURACY</span>
          <div className="text-3xl font-bold text-emerald-600">{data.overall_accuracy}%</div>
          <span className="text-[11px] text-[var(--text-secondary)]">Correct answer ratio</span>
        </div>

        <div className="editorial-card p-5 space-y-1">
          <span className="text-xs text-[var(--text-secondary)] block">AVG TIME / QUESTION</span>
          <div className="text-3xl font-bold text-[var(--brand-primary)]">
            {data.average_time_per_question_seconds}s
          </div>
          <span className="text-[11px] text-[var(--text-secondary)]">Speed benchmark</span>
        </div>
      </div>

      {!hasTests ? (
        /* Empty State */
        <div className="editorial-card p-12 text-center space-y-4">
          <TrendingUp className="w-12 h-12 mx-auto text-[var(--text-secondary)] opacity-50" />
          <h3 className="headline text-xl">Establish Your Exam Performance Baseline</h3>
          <p className="body-copy text-sm max-w-md mx-auto">
            You haven&apos;t completed any mock tests yet. Take your first practice test or solve previous-year questions to activate in-depth topic breakdown, weakness diagnostics, and revision scheduling.
          </p>
          <div className="flex justify-center gap-4 pt-2">
            <Link href="/mock-tests" className="brand-button text-xs font-mono px-5 py-2.5">
              Take a Mock Test
            </Link>
            <Link href="/pyqs" className="px-5 py-2.5 rounded-xl border text-xs font-mono hover:bg-[var(--surface-elevated)]">
              Practice PYQs
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Answer Breakdown & Strong/Weak Areas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Accuracy & Answer Breakdown */}
            <div className="editorial-card p-6 space-y-5">
              <h3 className="headline text-lg font-bold">Question Outcome Breakdown</h3>

              <div className="space-y-4 font-mono text-xs">
                {/* Visual Bar */}
                <div className="w-full h-4 rounded-full overflow-hidden flex bg-slate-200 dark:bg-slate-800">
                  <div
                    style={{
                      width: `${(data.total_correct / (data.total_questions_attempted || 1)) * 100}%`,
                    }}
                    className="bg-emerald-500 transition-all duration-500"
                    title={`Correct: ${data.total_correct}`}
                  />
                  <div
                    style={{
                      width: `${(data.total_incorrect / (data.total_questions_attempted || 1)) * 100}%`,
                    }}
                    className="bg-rose-500 transition-all duration-500"
                    title={`Incorrect: ${data.total_incorrect}`}
                  />
                </div>

                <div className="grid grid-cols-3 gap-2 text-center pt-2">
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <span className="text-emerald-700 dark:text-emerald-300 font-bold text-base block">
                      {data.total_correct}
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">Correct</span>
                  </div>

                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                    <span className="text-rose-700 dark:text-rose-300 font-bold text-base block">
                      {data.total_incorrect}
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">Incorrect</span>
                  </div>

                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <span className="text-amber-700 dark:text-amber-300 font-bold text-base block">
                      {data.total_unanswered}
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">Unanswered</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Diagnostics: Strong vs Weak Topics */}
            <div className="editorial-card p-6 space-y-5">
              <h3 className="headline text-lg font-bold">Topic Diagnostics</h3>

              <div className="space-y-4 text-xs font-mono">
                <div>
                  <span className="text-[var(--text-secondary)] block mb-1 font-semibold text-emerald-600 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Strong Subject Areas (&gt;= 70% Accuracy)
                  </span>
                  {data.strong_topics.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {data.strong_topics.map((t) => (
                        <span key={t} className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-600 font-medium">
                          {t}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[var(--text-secondary)] italic">
                      Keep practicing to build your 70%+ mastery subjects.
                    </span>
                  )}
                </div>

                <div className="pt-2 border-t">
                  <span className="text-[var(--text-secondary)] block mb-1 font-semibold text-rose-500 flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5" /> High-Priority Focus Areas (&lt; 50% Accuracy)
                  </span>
                  {data.weak_topics.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {data.weak_topics.map((t) => (
                        <span key={t} className="px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-600 font-medium">
                          {t}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[var(--text-secondary)] italic">
                      No weak subject areas identified below 50%.
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Subject Performance Breakdown Table */}
          {data.subject_performance.length > 0 && (
            <div className="editorial-card p-6 space-y-4">
              <h3 className="headline text-lg font-bold">Subject-Wise Performance Breakdown</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b text-[var(--text-secondary)]">
                      <th className="pb-3 font-semibold">SUBJECT / DOMAIN</th>
                      <th className="pb-3 font-semibold text-center">QUESTIONS</th>
                      <th className="pb-3 font-semibold text-center">CORRECT</th>
                      <th className="pb-3 font-semibold text-right">ACCURACY</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)]">
                    {data.subject_performance.map((s) => (
                      <tr key={s.subject} className="hover:bg-[var(--surface-elevated)] transition-colors">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{s.subject}</td>
                        <td className="py-3 text-center">{s.total_questions}</td>
                        <td className="py-3 text-center text-emerald-600">{s.correct_count}</td>
                        <td className="py-3 text-right">
                          <span
                            className={`font-bold px-2 py-0.5 rounded ${
                              s.accuracy >= 70
                                ? "bg-emerald-500/10 text-emerald-600"
                                : s.accuracy < 50
                                ? "bg-rose-500/10 text-rose-600"
                                : "text-[var(--text-secondary)]"
                            }`}
                          >
                            {s.accuracy}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Actionable Study Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="editorial-card p-6 space-y-5">
              <div className="flex items-center gap-2 border-b pb-3">
                <Sparkles className="w-5 h-5 text-[var(--brand-primary)]" />
                <h3 className="headline text-lg font-bold">Actionable Revision Recommendations</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-xl border bg-[var(--surface-elevated)] space-y-2 flex flex-col justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-[var(--brand-primary)]">
                          {rec.subject}
                        </span>
                        <span
                          className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${
                            rec.priority === "high"
                              ? "bg-rose-500/10 text-rose-600 font-semibold"
                              : "bg-[var(--surface)] text-[var(--text-secondary)]"
                          }`}
                        >
                          {rec.priority} Priority
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)]">{rec.topic}</h4>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{rec.reason}</p>
                    </div>

                    <div className="pt-2 text-xs font-mono text-[var(--text-primary)] flex items-center gap-1.5 border-t">
                      <ArrowRight className="w-3.5 h-3.5 text-[var(--brand-primary)]" />
                      <span>{rec.action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        title="Sync Your Exam Analytics"
        subtitle="Sign in with Google or Email to link your mock test scores, topic mastery, and recommendations across devices."
      />
    </div>
  );
}
