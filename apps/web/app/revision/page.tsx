"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RotateCcw,
  Trash2,
  Calendar,
  Filter,
  Sparkles,
  Loader2,
  AlertCircle,
  Clock,
  ArrowRight,
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
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

export default function RevisionPage() {
  const { user, isGuest } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [items, setItems] = useState<RevisionItem[]>([]);
  const [summary, setSummary] = useState<RevisionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "revised">("pending");
  const [subjectFilter, setSubjectFilter] = useState("");

  // Retry interaction state
  const [retrySelected, setRetrySelected] = useState<Record<string, string>>({});
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryFeedback, setRetryFeedback] = useState<Record<string, { is_correct: boolean; explanation?: string }>>({});

  useEffect(() => {
    loadData();
  }, [statusFilter, subjectFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [itemList, summaryData] = await Promise.all([
        fetchRevisionItems({
          status: statusFilter,
          subject: subjectFilter || undefined,
          limit: 100,
        }),
        fetchRevisionSummary().catch(() => null),
      ]);
      setItems(itemList);
      setSummary(summaryData);
    } catch (err) {
      console.error("Failed to load revision items", err);
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
    <div className="max-w-6xl mx-auto space-y-7">
      <BackButton fallbackHref="/exams" />

      {/* Header */}
      <div className="border-b pb-5">
        <div className="eyebrow flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4" />
          <span>Intelligent Error Correction & Spaced Repetition</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">Mistake Book & Smart Revision</h1>
        <p className="body-copy text-base mt-2 max-w-3xl">
          Questions you missed or skipped across mock tests and practice sessions are automatically tracked here.
          Use active retrieval and spaced-repetition intervals to permanently overcome persistent conceptual mistakes.
        </p>
      </div>

      {/* Guest info banner */}
      {isGuest && (
        <div className="p-4 rounded-xl border border-[color-mix(in_srgb,var(--brand-primary)_35%,transparent)] bg-[color-mix(in_srgb,var(--brand-primary)_8%,transparent)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-[var(--text-primary)]">
            <Sparkles className="w-4 h-4 text-[var(--brand-primary)] flex-shrink-0" />
            <span>
              <strong>Guest Mistake Book:</strong> Mistakes stored locally. Sign in with Google or Email to link your questions and sync spaced repetition across devices.
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

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-3 gap-4 font-mono text-center">
          <div className="editorial-card p-4">
            <span className="text-xs text-[var(--text-secondary)] block">TOTAL LOGGED</span>
            <span className="text-2xl font-bold text-[var(--text-primary)]">{summary.total_count}</span>
          </div>
          <div className="editorial-card p-4 border-rose-500/30">
            <span className="text-xs text-rose-500 block">PENDING REVISION</span>
            <span className="text-2xl font-bold text-rose-600">{summary.pending_count}</span>
          </div>
          <div className="editorial-card p-4 border-emerald-500/30">
            <span className="text-xs text-emerald-600 block">MASTERED / REVISED</span>
            <span className="text-2xl font-bold text-emerald-600">{summary.revised_count}</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="editorial-card p-4 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex gap-2">
          {(["pending", "revised", "all"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg capitalize transition-colors ${
                statusFilter === st
                  ? "bg-[var(--brand-primary)] text-white font-bold"
                  : "bg-[var(--surface)] border text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {st === "pending" ? "Pending Review" : st === "revised" ? "Mastered" : "All Items"}
            </button>
          ))}
        </div>

        {summary && summary.subjects.length > 0 && (
          <select
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)]"
          >
            <option value="">All Subjects</option>
            {summary.subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="editorial-card p-12 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin accent-mark" />
          <span className="body-copy text-sm font-mono">Loading Mistake Book entries...</span>
        </div>
      ) : items.length === 0 ? (
        <div className="editorial-card p-12 text-center space-y-4">
          <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-500 opacity-80" />
          <h3 className="headline text-xl">
            {statusFilter === "pending"
              ? "All caught up! No pending mistakes."
              : "No questions logged in this category."}
          </h3>
          <p className="body-copy text-sm max-w-md mx-auto">
            {statusFilter === "pending"
              ? "Awesome work! Any future incorrect answers from mock tests or question banks will automatically appear here."
              : "Complete a mock test or bookmark questions to populate your mistake records."}
          </p>
          <Link href="/mock-tests" className="brand-button text-xs font-mono px-4 py-2 inline-block">
            Take a Practice Test
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {items.map((item, idx) => {
            const feedback = retryFeedback[item.id];
            const currentSelected = retrySelected[item.id];

            return (
              <div
                key={item.id}
                className={`editorial-card p-6 md:p-7 space-y-5 transition-all ${
                  item.is_revised ? "opacity-75 bg-[var(--surface-elevated)]/50" : ""
                }`}
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono border-b pb-3">
                  <div className="flex items-center gap-2">
                    <span className="soft-badge px-2.5 py-1 text-[var(--brand-primary)] font-bold">
                      {item.exam_name}
                    </span>
                    {item.subject && (
                      <span className="soft-badge px-2.5 py-1 text-[var(--text-secondary)]">
                        {item.subject}
                      </span>
                    )}
                    <span
                      className={`px-2 py-0.5 rounded font-semibold ${
                        item.mistake_count > 1
                          ? "bg-rose-500/10 text-rose-600"
                          : "bg-amber-500/10 text-amber-600"
                      }`}
                    >
                      Missed {item.mistake_count}x
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {item.next_review_at && !item.is_revised && (
                      <span className="text-[11px] text-amber-600 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Due for Review
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() => handleToggleStatus(item)}
                      className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                        item.is_revised
                          ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                          : "hover:bg-[var(--surface-elevated)] text-[var(--text-secondary)]"
                      }`}
                    >
                      {item.is_revised ? "✓ Mastered" : "Mark as Mastered"}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDeleteItem(item.id)}
                      className="text-[var(--text-secondary)] hover:text-rose-500 p-1"
                      title="Remove from Mistake Book"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Question Text */}
                <h3 className="text-base font-semibold text-[var(--text-primary)] leading-relaxed">
                  <span className="text-[var(--brand-primary)] mr-2 font-mono">Q{idx + 1}.</span>
                  {item.question_text}
                </h3>

                {/* Interactive Retry Mode Options */}
                <div className="space-y-2.5">
                  <span className="text-xs font-mono text-[var(--text-secondary)] block">
                    ACTIVE RETRIEVAL RETRY:
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
                          className={`p-3 rounded-xl border text-left flex items-start gap-3 transition-colors ${
                            isSelected
                              ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] font-semibold"
                              : "bg-[var(--surface)] hover:bg-[var(--surface-elevated)] text-[var(--text-primary)]"
                          }`}
                        >
                          <span className="font-mono text-xs mt-0.5 opacity-70">{letter})</span>
                          <span className="flex-1 leading-snug">{opt.replace(/^[A-D][.)]\s*/i, "")}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Retry Submit Action */}
                <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleRetrySubmit(item)}
                      disabled={!currentSelected || retryingId === item.id}
                      className="brand-button text-xs font-mono px-4 py-2 flex items-center gap-1.5 disabled:opacity-40"
                    >
                      {retryingId === item.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3.5 h-3.5" />
                      )}
                      <span>Submit Retry</span>
                    </button>

                    {feedback && (
                      <span
                        className={`text-xs font-mono font-bold flex items-center gap-1.5 ${
                          feedback.is_correct ? "text-emerald-600" : "text-rose-600"
                        }`}
                      >
                        {feedback.is_correct ? (
                          <>
                            <CheckCircle2 className="w-4 h-4" /> Correct! Rescheduled for +3 days.
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4" /> Still incorrect. Review explanation below.
                          </>
                        )}
                      </span>
                    )}
                  </div>

                  <span className="text-[11px] font-mono text-[var(--text-secondary)]">
                    Correct: <strong>{item.correct_answer}</strong>
                  </span>
                </div>

                {/* Explanation Box */}
                {(feedback || item.explanation) && (
                  <div className="p-4 rounded-xl bg-[var(--surface-elevated)] border border-[var(--border-subtle)] space-y-1 text-sm leading-relaxed">
                    <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-[var(--brand-primary)]">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Academic Rational & Concept Review</span>
                    </div>
                    <p className="text-[var(--text-secondary)]">{item.explanation || "No explanation recorded."}</p>
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
        subtitle="Sign in with Google or Email to preserve your missed questions, sync spaced repetition, and review on any device."
      />
    </div>
  );
}
