"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RotateCcw,
  Trash2,
  Sparkles,
  Loader2,
  Clock,
  ArrowRight,
  BookmarkCheck,
  Check,
} from "lucide-react";
import {
  fetchRevisionItems,
  fetchRevisionSummary,
  retryRevisionQuestion,
  updateRevisionStatus,
  deleteRevisionItem,
  RevisionItem,
  RevisionSummary,
} from "@/services/revision";
import { BackButton } from "@/components/navigation/back-button";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyBookmarksIllustration } from "@/components/illustrations/educational-illustrations";
import { useAuth, ensureAuthSession } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

export default function RevisionPage() {
  const router = useRouter();
  const { user, isGuest } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [items, setItems] = useState<RevisionItem[]>([]);
  const [summary, setSummary] = useState<RevisionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "revised">("pending");
  const [subjectFilter, setSubjectFilter] = useState("");

  // Retry interaction state
  const [retrySelected, setRetrySelected] = useState<Record<string, string>>({});
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryFeedback, setRetryFeedback] = useState<Record<string, { is_correct: boolean; explanation?: string }>>({});

  useEffect(() => {
    loadData();
  }, [statusFilter, subjectFilter, user?.id]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await ensureAuthSession();

      const [itemList, summaryData] = await Promise.all([
        fetchRevisionItems({
          status: statusFilter,
          subject: subjectFilter || undefined,
          limit: 100,
        }),
        fetchRevisionSummary(),
      ]);
      setItems(itemList);
      setSummary(summaryData);
    } catch (err) {
      console.error("Failed to load revision items", err);
      setError("Unable to load Mistake Book records. Please check your network connection and retry.");
    } finally {
      setLoading(false);
    }
  };

  const handleRetrySubmit = async (item: RevisionItem) => {
    const selected = retrySelected[item.id];
    if (!selected) return;

    setRetryingId(item.id);
    try {
      const res = await retryRevisionQuestion(item.id, selected);
      setRetryFeedback((prev) => ({
        ...prev,
        [item.id]: {
          is_correct: res.is_correct,
          explanation: res.explanation,
        },
      }));

      // Update item in list
      setItems((prev) =>
        prev.map((it) =>
          it.id === item.id
            ? {
                ...it,
                mistake_count: res.mistake_count,
                is_revised: res.is_revised,
                next_review_at: res.next_review_at,
              }
            : it
        )
      );

      // Refresh summary counts
      fetchRevisionSummary().then(setSummary).catch(() => {});
    } catch (err) {
      console.error("Retry failed", err);
    } finally {
      setRetryingId(null);
    }
  };

  const handleToggleStatus = async (item: RevisionItem) => {
    try {
      const updated = await updateRevisionStatus(item.id, !item.is_revised);
      setItems((prev) => prev.map((it) => (it.id === item.id ? updated : it)));
      fetchRevisionSummary().then(setSummary).catch(() => {});
    } catch (err) {
      console.error("Status update failed", err);
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!confirm("Are you sure you want to remove this question from your Mistake Book?")) return;
    try {
      await deleteRevisionItem(itemId);
      setItems((prev) => prev.filter((it) => it.id !== itemId));
      fetchRevisionSummary().then(setSummary).catch(() => {});
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-7 page-enter">
      <BackButton fallbackHref="/" />

      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] pb-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
            ERROR RECOVERY & REVISION
          </span>
          <span className="text-xs text-[var(--text-muted)]">• Spaced Repetition Engine</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
          Mistake Book & Smart Revision
        </h1>
        <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-3xl leading-relaxed">
          Questions you missed or skipped across mock tests and practice drills are automatically cataloged here.
          Engage in active retrieval and targeted re-testing to convert persistent weak spots into reliable marks.
        </p>
      </div>

      {/* Guest info banner */}
      {isGuest && user && (
        <div className="p-4 rounded-xl border border-[color-mix(in_srgb,var(--accent)_30%,var(--border))] bg-[var(--accent-soft)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5 text-[var(--text-primary)]">
            <Sparkles className="w-4 h-4 text-[var(--accent)] flex-shrink-0" />
            <span>
              <strong>Guest Session Active:</strong> Questions missed during this session are saved for review. Sign in anytime to link your mistake history across devices.
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

      {/* Bento Summary KPI Cards - Only show when data has finished loading to prevent stale counts */}
      {!loading && summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="editorial-card p-5 border border-[var(--border)] text-center shadow-xs">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">
              Total Logged
            </span>
            <span className="text-3xl font-bold text-[var(--text-primary)] font-serif">
              {summary.total_count}
            </span>
            <span className="text-[11px] text-[var(--text-muted)] block mt-1">Across all syllabus topics</span>
          </div>

          <div className="editorial-card p-5 border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] bg-[var(--danger-soft)] text-center shadow-xs">
            <span className="text-[11px] font-semibold text-[var(--danger)] uppercase tracking-wider block mb-1">
              Pending Revision
            </span>
            <span className="text-3xl font-bold text-[var(--danger)] font-serif">
              {summary.pending_count}
            </span>
            <span className="text-[11px] text-[var(--text-muted)] block mt-1">Needs immediate active retrieval</span>
          </div>

          <div className="editorial-card p-5 border border-[color-mix(in_srgb,var(--success)_30%,var(--border))] bg-[var(--success-soft)] text-center shadow-xs">
            <span className="text-[11px] font-semibold text-[var(--success)] uppercase tracking-wider block mb-1">
              Mastered & Verified
            </span>
            <span className="text-3xl font-bold text-[var(--success)] font-serif">
              {summary.revised_count}
            </span>
            <span className="text-[11px] text-[var(--text-muted)] block mt-1">Concept successfully reinforced</span>
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="editorial-card p-4 flex flex-wrap items-center justify-between gap-4 border border-[var(--border)] shadow-xs">
        <div className="flex items-center gap-2">
          {(["pending", "revised", "all"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                statusFilter === st
                  ? "bg-[var(--accent)] text-white shadow-xs"
                  : "bg-[var(--surface-muted)] text-[var(--text-secondary)] border border-[var(--border)] hover:text-[var(--text-primary)] hover:border-[var(--text-muted)]"
              }`}
            >
              {st === "pending" ? "Pending Review" : st === "revised" ? "Mastered" : "All Items"}
            </button>
          ))}
        </div>

        {summary && summary.subjects.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-muted)]">Subject:</span>
            <select
              value={subjectFilter}
              onChange={(e) => setSubjectFilter(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[var(--accent)]"
            >
              <option value="">All Subjects</option>
              {summary.subjects.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="editorial-card p-12 flex flex-col items-center justify-center gap-3 border border-[var(--border)]">
          <Loader2 className="w-6 h-6 animate-spin text-[var(--accent)]" />
          <span className="text-xs font-medium text-[var(--text-secondary)]">Retrieving Mistake Book entries...</span>
        </div>
      ) : error ? (
        <ErrorState
          title="Mistake Book Unavailable"
          message={error}
          onRetry={loadData}
        />
      ) : items.length === 0 ? (
        <div className="space-y-4">
          <EmptyState
            illustration={<EmptyBookmarksIllustration size={110} />}
            title={
              !summary || summary.total_count === 0
                ? "Your Mistake Book is ready!"
                : statusFilter === "pending"
                ? "All Caught Up! No Pending Mistakes"
                : "No Questions Logged Yet"
            }
            description={
              !summary || summary.total_count === 0
                ? "Complete a practice question or mock test, and questions you get wrong will appear here for revision."
                : statusFilter === "pending"
                ? "Outstanding performance. You have mastered every question in your spaced repetition queue. Any future missed questions will appear here automatically."
                : "Complete a full-length mock test or question bank drill to begin tracking conceptual areas that need reinforcement."
            }
            actionLabel="Take a Mock Test"
            onAction={() => router.push("/mock-tests")}
          />
          {isGuest && (!summary || summary.total_count === 0) && (
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setIsAuthOpen(true)}
                className="text-xs font-mono font-medium text-[var(--accent)] hover:underline"
              >
                Already have an account? Sign In to Sync your saved mistake history →
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {items.map((item, idx) => {
            const feedback = retryFeedback[item.id];
            const currentSelected = retrySelected[item.id];

            return (
              <div
                key={item.id}
                className={`editorial-card p-6 md:p-7 space-y-5 border border-[var(--border)] shadow-xs transition-all ${
                  item.is_revised ? "opacity-85 bg-[var(--surface-muted)]" : "bg-[var(--surface)]"
                }`}
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-[var(--border)] pb-3">
                  <div className="flex items-center gap-2">
                    <span className="badge-editorial text-xs font-semibold text-[var(--accent)] border-[var(--accent)]">
                      {item.exam_name}
                    </span>
                    {item.subject && (
                      <span className="badge-editorial text-xs text-[var(--text-secondary)] border-[var(--border)]">
                        {item.subject}
                      </span>
                    )}
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                        item.mistake_count > 1
                          ? "bg-[var(--danger-soft)] text-[var(--danger)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))]"
                          : "bg-[var(--warning-soft)] text-amber-700 border border-amber-300"
                      }`}
                    >
                      Missed {item.mistake_count}x
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {item.next_review_at && !item.is_revised && (
                      <span className="text-[11px] text-amber-700 font-medium flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Due for Review
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() => handleToggleStatus(item)}
                      className={`text-xs px-3 py-1 rounded-lg border font-medium transition-all ${
                        item.is_revised
                          ? "bg-[var(--success-soft)] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,var(--border))]"
                          : "bg-[var(--surface)] hover:bg-[var(--surface-muted)] text-[var(--text-secondary)] border-[var(--border)]"
                      }`}
                    >
                      {item.is_revised ? "✓ Mastered" : "Mark as Mastered"}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDeleteItem(item.id)}
                      className="text-[var(--text-muted)] hover:text-[var(--danger)] p-1 rounded-md transition-colors"
                      title="Remove from Mistake Book"
                      aria-label="Remove item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Question Text */}
                <h3 className="text-base font-bold text-[var(--text-primary)] leading-relaxed">
                  <span className="text-[var(--accent)] mr-2 font-mono">Q{idx + 1}.</span>
                  {item.question_text}
                </h3>

                {/* Active Retrieval Options */}
                <div className="space-y-2.5">
                  <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                    Active Retrieval Practice:
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    {item.options.map((opt, optIdx) => {
                      const letter = String.fromCharCode(65 + optIdx);
                      const isSelected = currentSelected === letter;

                      return (
                        <button
                          key={optIdx}
                          type="button"
                          onClick={() =>
                            setRetrySelected((prev) => ({
                              ...prev,
                              [item.id]: letter,
                            }))
                          }
                          className={`p-3.5 rounded-xl border text-left flex items-start gap-3 transition-all ${
                            isSelected
                              ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)] font-semibold shadow-xs"
                              : "bg-[var(--surface-muted)] hover:bg-[var(--surface)] text-[var(--text-primary)] border-[var(--border)]"
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                              isSelected
                                ? "bg-[var(--accent)] text-white"
                                : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)]"
                            }`}
                          >
                            {letter}
                          </span>
                          <span className="flex-1 leading-snug pt-0.5">
                            {opt.replace(/^[A-D][.)]\s*/i, "")}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Retry Submit Action */}
                <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-[var(--border)]">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleRetrySubmit(item)}
                      disabled={!currentSelected || retryingId === item.id}
                      className="button-base button-primary px-4 py-2 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40"
                    >
                      {retryingId === item.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3.5 h-3.5" />
                      )}
                      <span>Submit Answer</span>
                    </button>

                    {feedback && (
                      <span
                        className={`text-xs font-semibold flex items-center gap-1.5 ${
                          feedback.is_correct ? "text-[var(--success)]" : "text-[var(--danger)]"
                        }`}
                      >
                        {feedback.is_correct ? (
                          <>
                            <CheckCircle2 className="w-4 h-4" /> Correct! Scheduled for review in 3 days.
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4" /> Incorrect. Study the rationale below.
                          </>
                        )}
                      </span>
                    )}
                  </div>

                  <span className="text-xs text-[var(--text-muted)]">
                    Official Key: <strong className="text-[var(--text-primary)]">{item.correct_answer}</strong>
                  </span>
                </div>

                {/* Academic Rationale Explanation Box */}
                {(feedback || item.explanation) && (
                  <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] space-y-1.5 text-sm leading-relaxed">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-[var(--accent)]">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Academic Rationale & Concept Review</span>
                    </div>
                    <p className="text-[var(--text-secondary)] text-xs md:text-sm">
                      {item.explanation || "No additional explanation recorded."}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        title="Sync Your Mistake Book"
        subtitle="Sign in to preserve your missed questions, sync spaced repetition intervals, and review across your devices."
      />
    </div>
  );
}
