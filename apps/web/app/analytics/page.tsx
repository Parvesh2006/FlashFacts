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
  Clock,
  Compass,
} from "lucide-react";
import { fetchPerformanceAnalytics, PerformanceAnalytics } from "@/services/analytics";
import { BackButton } from "@/components/navigation/back-button";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { CompletedTestIllustration } from "@/components/illustrations/educational-illustrations";
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

export default function AnalyticsPage() {
  const { user, isGuest } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [data, setData] = useState<PerformanceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = () => {
    setLoading(true);
    setError(null);
    fetchPerformanceAnalytics()
      .then(setData)
      .catch((err) => {
        console.error("Failed to fetch analytics", err);
        setError("Unable to compute performance analytics from current session. Please verify your connection.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12 border border-[var(--border)]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
        <p className="text-sm font-medium text-[var(--text-secondary)]">Computing exam readiness diagnostics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto my-10 space-y-4">
        <BackButton fallbackHref="/" />
        <ErrorState
          title="Performance Diagnostics Unavailable"
          message={error}
          onRetry={loadAnalytics}
        />
      </div>
    );
  }

  if (!data || data.total_tests_completed === 0) {
    return (
      <div className="max-w-5xl mx-auto space-y-7 page-enter">
        <BackButton fallbackHref="/" />

        <div className="border-b border-[var(--border)] pb-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
              PERFORMANCE INTELLIGENCE
            </span>
            <span className="text-xs text-[var(--text-muted)]">• Diagnostic Engine</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
            Performance Analytics & Weakness Map
          </h1>
          <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-3xl leading-relaxed">
            Monitor your genuine test mastery, subject-wise accuracy, speed benchmarks, and curriculum-driven recommendations.
          </p>
        </div>

        <div className="editorial-card p-12 text-center space-y-6 max-w-lg mx-auto my-8 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <div className="mx-auto flex justify-center">
            <CompletedTestIllustration className="w-24 h-24" />
          </div>
          <div className="space-y-2">
            <h3 className="headline text-xl font-bold text-[var(--text-primary)]">
              {isGuest ? "No Guest Tests Completed Yet" : "No Account Mock Tests Recorded"}
            </h3>
            <p className="body-copy text-xs text-[var(--text-secondary)] leading-relaxed">
              Complete your first mock test or practice set to generate verified accuracy scores, time metrics, and topic-wise weakness analysis.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/mock-tests" className="button-base button-primary px-5 py-2 text-xs font-semibold w-full sm:w-auto">
              Take a Mock Test
            </Link>
            {isGuest && (
              <button
                type="button"
                onClick={() => setIsAuthOpen(true)}
                className="button-base button-secondary px-5 py-2 text-xs font-semibold w-full sm:w-auto"
              >
                Sign In to Sync
              </button>
            )}
          </div>
          <AuthModal
            isOpen={isAuthOpen}
            onClose={() => setIsAuthOpen(false)}
            title="Sign In for Performance Analytics"
            subtitle="Sign in to track verified test accuracy, score progression, and topic-wise mastery across devices."
          />
        </div>
      </div>
    );
  }

  const hasTests = data.total_tests_completed > 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8 page-enter">
      <BackButton fallbackHref="/" />

      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] pb-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
            PERFORMANCE INTELLIGENCE
          </span>
          <span className="text-xs text-[var(--text-muted)]">• Continuous Diagnostic Engine</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
          Performance Analytics & Weakness Map
        </h1>
        <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-3xl leading-relaxed">
          Monitor your genuine test mastery, subject-wise accuracy, speed benchmarks, and curriculum-driven recommendations
          derived directly from your scored mock tests.
        </p>
      </div>

      {/* Guest info banner */}
      {isGuest && (
        <div className="p-4 rounded-xl border border-[color-mix(in_srgb,var(--accent)_30%,var(--border))] bg-[var(--accent-soft)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-[var(--text-primary)]">
            <Sparkles className="w-4 h-4 text-[var(--accent)] flex-shrink-0" />
            <span>
              <strong>Guest Performance:</strong> Metrics are recorded for this session. Sign in to preserve your history and sync progression.
            </span>
          </div>
          <button
            onClick={() => setIsAuthOpen(true)}
            className="button-base button-primary px-3 py-1.5 text-xs flex-shrink-0 whitespace-nowrap"
          >
            Sign In to Sync
          </button>
        </div>
      )}

      {/* Top Level Bento Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="editorial-card p-5 space-y-1 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
            Tests Completed
          </span>
          <div className="text-3xl font-bold font-serif text-[var(--text-primary)]">{data.total_tests_completed}</div>
          <span className="text-[11px] text-[var(--text-muted)] block">Scored test sessions</span>
        </div>

        <div className="editorial-card p-5 space-y-1 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
            Questions Attempted
          </span>
          <div className="text-3xl font-bold font-serif text-[var(--text-primary)]">{data.total_questions_attempted}</div>
          <span className="text-[11px] text-[var(--text-muted)] block">Total MCQs evaluated</span>
        </div>

        <div className="editorial-card p-5 space-y-1 border border-[color-mix(in_srgb,var(--success)_30%,var(--border))] bg-[var(--success-soft)] shadow-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--success)] block">
            Overall Accuracy
          </span>
          <div className="text-3xl font-bold font-serif text-[var(--success)]">{data.overall_accuracy}%</div>
          <span className="text-[11px] text-[var(--text-muted)] block">Positive scoring ratio</span>
        </div>

        <div className="editorial-card p-5 space-y-1 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
            Avg Speed / Question
          </span>
          <div className="text-3xl font-bold font-serif text-[var(--accent)]">
            {data.average_time_per_question_seconds}s
          </div>
          <span className="text-[11px] text-[var(--text-muted)] block">Speed target: &lt;60s</span>
        </div>
      </div>

      {!hasTests ? (
        <EmptyState
          illustration={<CompletedTestIllustration size={110} />}
          title="Establish Your Baseline Performance"
          description="Take your first practice mock test or solve previous-year question sets to activate subject-wise breakdown, weakness diagnostics, and revision scheduling."
          actionLabel="Take a Mock Test"
          onAction={() => window.location.assign("/mock-tests")}
          secondaryActionLabel="Explore PYQs"
          onSecondaryAction={() => window.location.assign("/pyqs")}
        />
      ) : (
        <>
          {/* Answer Breakdown & Strong/Weak Areas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Accuracy & Answer Breakdown */}
            <div className="editorial-card p-6 space-y-5 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
              <h3 className="headline text-lg font-bold text-[var(--text-primary)]">
                Question Outcome Breakdown
              </h3>

              <div className="space-y-4 text-xs">
                {/* Visual Bar */}
                <div className="w-full h-3 rounded-full overflow-hidden flex bg-[var(--surface-muted)] border border-[var(--border)]">
                  <div
                    style={{
                      width: `${(data.total_correct / (data.total_questions_attempted || 1)) * 100}%`,
                    }}
                    className="bg-[var(--success)] transition-all duration-500"
                    title={`Correct: ${data.total_correct}`}
                  />
                  <div
                    style={{
                      width: `${(data.total_incorrect / (data.total_questions_attempted || 1)) * 100}%`,
                    }}
                    className="bg-[var(--danger)] transition-all duration-500"
                    title={`Incorrect: ${data.total_incorrect}`}
                  />
                </div>

                <div className="grid grid-cols-3 gap-3 text-center pt-2">
                  <div className="p-3 rounded-xl bg-[var(--success-soft)] border border-[color-mix(in_srgb,var(--success)_30%,var(--border))]">
                    <span className="text-[var(--success)] font-bold text-lg font-serif block">
                      {data.total_correct}
                    </span>
                    <span className="text-[11px] text-[var(--text-muted)] font-medium">Correct</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--danger-soft)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))]">
                    <span className="text-[var(--danger)] font-bold text-lg font-serif block">
                      {data.total_incorrect}
                    </span>
                    <span className="text-[11px] text-[var(--text-muted)] font-medium">Incorrect</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)]">
                    <span className="text-[var(--text-primary)] font-bold text-lg font-serif block">
                      {data.total_unanswered}
                    </span>
                    <span className="text-[11px] text-[var(--text-muted)] font-medium">Unanswered</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Diagnostics: Strong vs Weak Topics */}
            <div className="editorial-card p-6 space-y-5 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
              <h3 className="headline text-lg font-bold text-[var(--text-primary)]">
                Topic Diagnostics
              </h3>

              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[var(--success)] block mb-1.5 font-semibold flex items-center gap-1.5 text-xs">
                    <CheckCircle2 className="w-4 h-4" /> Strong Subject Areas (≥ 70% Accuracy)
                  </span>
                  {data.strong_topics.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {data.strong_topics.map((t) => (
                        <span key={t} className="px-2.5 py-1 rounded-md bg-[var(--success-soft)] text-[var(--success)] font-medium border border-[color-mix(in_srgb,var(--success)_30%,var(--border))]">
                          {t}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[var(--text-muted)] italic text-xs">
                      Continue taking tests to build subject areas above 70% accuracy.
                    </span>
                  )}
                </div>

                <div className="pt-3 border-t border-[var(--border)]">
                  <span className="text-[var(--danger)] block mb-1.5 font-semibold flex items-center gap-1.5 text-xs">
                    <XCircle className="w-4 h-4" /> High-Priority Focus Areas (&lt; 50% Accuracy)
                  </span>
                  {data.weak_topics.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {data.weak_topics.map((t) => (
                        <span key={t} className="px-2.5 py-1 rounded-md bg-[var(--danger-soft)] text-[var(--danger)] font-medium border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))]">
                          {t}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[var(--text-muted)] italic text-xs">
                      No weak subject areas identified below 50%. Excellent foundation.
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Subject Performance Breakdown Table */}
          {data.subject_performance.length > 0 && (
            <div className="editorial-card p-6 space-y-4 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
              <h3 className="headline text-lg font-bold text-[var(--text-primary)]">
                Subject-Wise Performance Breakdown
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                      <th className="pb-3 font-semibold uppercase tracking-wider">Subject / Domain</th>
                      <th className="pb-3 font-semibold text-center uppercase tracking-wider">Questions</th>
                      <th className="pb-3 font-semibold text-center uppercase tracking-wider">Correct</th>
                      <th className="pb-3 font-semibold text-right uppercase tracking-wider">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {data.subject_performance.map((s) => (
                      <tr key={s.subject} className="hover:bg-[var(--surface-muted)] transition-colors">
                        <td className="py-3 font-semibold text-[var(--text-primary)]">{s.subject}</td>
                        <td className="py-3 text-center text-[var(--text-secondary)]">{s.total_questions}</td>
                        <td className="py-3 text-center text-[var(--success)] font-bold">{s.correct_count}</td>
                        <td className="py-3 text-right">
                          <span
                            className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                              s.accuracy >= 70
                                ? "bg-[var(--success-soft)] text-[var(--success)]"
                                : s.accuracy < 50
                                ? "bg-[var(--danger-soft)] text-[var(--danger)]"
                                : "bg-[var(--surface-muted)] text-[var(--text-secondary)]"
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
            <div className="editorial-card p-6 space-y-5 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
              <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3">
                <Sparkles className="w-5 h-5 text-[var(--accent)]" />
                <h3 className="headline text-lg font-bold text-[var(--text-primary)]">
                  Actionable Revision Recommendations
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] space-y-2.5 flex flex-col justify-between"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[var(--accent)]">
                          {rec.subject}
                        </span>
                        <span
                          className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded ${
                            rec.priority === "high"
                              ? "bg-[var(--danger-soft)] text-[var(--danger)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))]"
                              : "bg-[var(--surface)] text-[var(--text-secondary)] border border-[var(--border)]"
                          }`}
                        >
                          {rec.priority} Priority
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">{rec.topic}</h4>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{rec.reason}</p>
                    </div>

                    <div className="pt-2.5 text-xs font-medium text-[var(--text-primary)] flex items-center gap-1.5 border-t border-[var(--border)]">
                      <ArrowRight className="w-3.5 h-3.5 text-[var(--accent)]" />
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
