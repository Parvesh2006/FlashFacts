"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import {
  Clock,
  AlertTriangle,
  Flag,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Send,
  Loader2,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import {
  fetchMockTest,
  submitMockTestAttempt,
  MockTestDetails,
} from "@/services/mock-tests";

export default function ActiveMockTestPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const resolvedParams = use(params);
  const testId = resolvedParams.id;

  const [test, setTest] = useState<MockTestDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Test session state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [reviewMarked, setReviewMarked] = useState<Record<number, boolean>>({});
  const [timeLeftSeconds, setTimeLeftSeconds] = useState<number>(1800); // default 30 min
  const [submitting, setSubmitting] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  // 1. Fetch test
  useEffect(() => {
    fetchMockTest(testId)
      .then((data) => {
        setTest(data);
        const totalSecs = (data.time_limit_minutes || 30) * 60;
        setTimeLeftSeconds(totalSecs);

        // Restore draft from local storage if available
        const draftKey = `draft_attempt_${testId}`;
        const savedDraft = localStorage.getItem(draftKey);
        if (savedDraft) {
          try {
            const parsed = JSON.parse(savedDraft);
            if (parsed.answers) setAnswers(parsed.answers);
            if (parsed.reviewMarked) setReviewMarked(parsed.reviewMarked);
          } catch (e) {
            console.error("Failed to parse draft", e);
          }
        }
      })
      .catch((err) => {
        console.error("Failed to load mock test", err);
        setError("Test not found or generation in progress.");
      })
      .finally(() => setLoading(false));
  }, [testId]);

  // 2. Countdown timer
  useEffect(() => {
    if (!test || timeLeftSeconds <= 0 || submitting) return;

    const timer = setInterval(() => {
      setTimeLeftSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleFinalSubmit(); // Auto-submit when time expires
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [test, timeLeftSeconds, submitting]);

  // 3. Draft persistence
  const saveDraft = (newAnswers: Record<string, string>, newReview: Record<number, boolean>) => {
    const draftKey = `draft_attempt_${testId}`;
    localStorage.setItem(
      draftKey,
      JSON.stringify({ answers: newAnswers, reviewMarked: newReview })
    );
  };

  const handleSelectAnswer = (qId: number, letter: string) => {
    setAnswers((prev) => {
      const updated = { ...prev, [qId.toString()]: letter };
      saveDraft(updated, reviewMarked);
      return updated;
    });
  };

  const handleClearAnswer = (qId: number) => {
    setAnswers((prev) => {
      const updated = { ...prev };
      delete updated[qId.toString()];
      saveDraft(updated, reviewMarked);
      return updated;
    });
  };

  const handleToggleReview = (qId: number) => {
    setReviewMarked((prev) => {
      const updated = { ...prev, [qId]: !prev[qId] };
      saveDraft(answers, updated);
      return updated;
    });
  };

  const handleFinalSubmit = async () => {
    setSubmitting(true);
    setShowSubmitModal(false);

    const totalSeconds = (test?.time_limit_minutes || 30) * 60;
    const timeTaken = Math.max(1, totalSeconds - timeLeftSeconds);

    const reviewIds = Object.entries(reviewMarked)
      .filter(([_, marked]) => marked)
      .map(([id]) => parseInt(id, 10));

    try {
      const result = await submitMockTestAttempt(testId, {
        answers,
        time_taken_seconds: timeTaken,
        review_marked: reviewIds,
      });

      // Clear draft
      localStorage.removeItem(`draft_attempt_${testId}`);
      router.push(`/mock-tests/${testId}/result/${result.id}`);
    } catch (err: any) {
      console.error("Submission failed", err);
      alert(err.message || "Submission failed. Please check your network and retry.");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12">
        <Loader2 className="w-8 h-8 animate-spin accent-mark" />
        <p className="body-copy font-mono text-sm">Preparing official exam interface...</p>
      </div>
    );
  }

  if (error || !test || !test.questions || test.questions.length === 0) {
    return (
      <div className="editorial-card p-12 text-center space-y-4 max-w-md mx-auto my-12">
        <AlertCircle className="w-10 h-10 mx-auto text-rose-500" />
        <h3 className="headline text-xl">Test Unavailable</h3>
        <p className="body-copy text-sm">{error || "No questions found in this test."}</p>
        <button
          onClick={() => router.push("/mock-tests")}
          className="brand-button text-xs font-mono px-4 py-2"
        >
          Return to Mock Test Centre
        </button>
      </div>
    );
  }

  const currentQ = test.questions[currentIndex];
  const totalQuestions = test.questions.length;
  const answeredCount = Object.keys(answers).length;
  const unansweredCount = totalQuestions - answeredCount;
  const markedReviewCount = Object.values(reviewMarked).filter(Boolean).length;

  const minutes = Math.floor(timeLeftSeconds / 60);
  const seconds = timeLeftSeconds % 60;
  const isTimeCritical = timeLeftSeconds < 300; // < 5 minutes

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Bar */}
      <div className="editorial-card p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4 sticky top-16 z-20 shadow-sm border-[var(--border-subtle)]">
        <div>
          <span className="eyebrow text-xs block">{test.exam_name}</span>
          <h2 className="headline text-lg sm:text-xl font-bold">
            {test.domain || "Full Syllabus"} Examination
          </h2>
        </div>

        {/* Timer Display */}
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-sm font-bold border transition-colors ${
            isTimeCritical
              ? "bg-rose-500/10 border-rose-500/30 text-rose-600 animate-pulse"
              : "bg-[var(--surface-elevated)] border-[var(--border-subtle)] text-[var(--text-primary)]"
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>
            {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
          </span>
        </div>

        {/* Submit Test Trigger */}
        <button
          type="button"
          onClick={() => setShowSubmitModal(true)}
          disabled={submitting}
          className="brand-button text-xs font-mono px-5 py-2 flex items-center gap-2"
        >
          {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          <span>Submit Test</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Main Question Panel (3 cols) */}
        <div className="lg:col-span-3 editorial-card p-6 md:p-8 space-y-6">
          {/* Question Header */}
          <div className="flex items-center justify-between border-b pb-4">
            <span className="font-mono text-xs font-bold text-[var(--brand-primary)]">
              QUESTION {currentIndex + 1} OF {totalQuestions}
            </span>

            <button
              type="button"
              onClick={() => handleToggleReview(currentQ.id)}
              className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg border transition-all ${
                reviewMarked[currentQ.id]
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-600 font-semibold"
                  : "hover:bg-[var(--surface-elevated)] text-[var(--text-secondary)]"
              }`}
            >
              <Flag className={`w-3.5 h-3.5 ${reviewMarked[currentQ.id] ? "fill-current" : ""}`} />
              <span>{reviewMarked[currentQ.id] ? "Marked for Review" : "Mark for Review"}</span>
            </button>
          </div>

          {/* Question Text */}
          <div>
            <h3 className="text-base md:text-xl font-semibold text-[var(--text-primary)] leading-relaxed">
              {currentQ.question_text}
            </h3>
          </div>

          {/* Options List */}
          <div className="space-y-3 pt-2">
            {currentQ.options.map((opt, optIdx) => {
              const letter = String.fromCharCode(65 + optIdx);
              const isSelected = answers[currentQ.id.toString()] === letter;

              return (
                <button
                  key={optIdx}
                  type="button"
                  onClick={() => handleSelectAnswer(currentQ.id, letter)}
                  className={`w-full p-4 rounded-xl text-left text-sm transition-all flex items-start gap-3 border ${
                    isSelected
                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] font-semibold shadow-sm"
                      : "bg-[var(--surface)] hover:bg-[var(--surface-elevated)] text-[var(--text-primary)]"
                  }`}
                >
                  <span className="font-mono text-xs mt-0.5 opacity-70 px-2 py-0.5 rounded bg-[var(--surface-elevated)] border">
                    {letter}
                  </span>
                  <span className="flex-1 leading-snug">{opt.replace(/^[A-D][.)]\s*/i, "")}</span>
                </button>
              );
            })}
          </div>

          {/* Footer Navigation */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t font-mono text-xs">
            <button
              type="button"
              onClick={() => handleClearAnswer(currentQ.id)}
              disabled={!answers[currentQ.id.toString()]}
              className="text-[var(--text-secondary)] hover:text-rose-500 disabled:opacity-30 transition-colors"
            >
              Clear Response
            </button>

            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((prev) => prev - 1)}
                className="px-4 py-2 rounded-lg border text-[var(--text-primary)] disabled:opacity-30 hover:bg-[var(--surface-elevated)] flex items-center gap-1.5"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <button
                type="button"
                disabled={currentIndex === totalQuestions - 1}
                onClick={() => setCurrentIndex((prev) => prev + 1)}
                className="brand-button px-5 py-2 flex items-center gap-1.5 disabled:opacity-30"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Question Palette Sidebar (1 col) */}
        <div className="editorial-card p-5 space-y-5">
          <div className="border-b pb-3">
            <h4 className="font-mono text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
              Question Palette
            </h4>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-[var(--text-secondary)]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Answered ({answeredCount})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
              <span>Unanswered ({unansweredCount})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span>Review ({markedReviewCount})</span>
            </div>
          </div>

          {/* Grid of question buttons */}
          <div className="grid grid-cols-5 gap-2 pt-2">
            {test.questions.map((q, idx) => {
              const hasAns = !!answers[q.id.toString()];
              const isMarked = !!reviewMarked[q.id];
              const isCurrent = idx === currentIndex;

              let btnBg = "bg-[var(--surface-elevated)] text-[var(--text-secondary)]";
              if (isMarked) {
                btnBg = "bg-amber-500/20 text-amber-600 font-bold border-amber-500/40";
              } else if (hasAns) {
                btnBg = "bg-emerald-500/20 text-emerald-600 font-bold border-emerald-500/40";
              }

              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => setCurrentIndex(idx)}
                  className={`h-9 w-full rounded-lg font-mono text-xs transition-all border flex items-center justify-center ${btnBg} ${
                    isCurrent ? "ring-2 ring-[var(--brand-primary)] font-bold scale-105" : ""
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Final Submit Confirmation Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="editorial-card max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="border-b pb-3">
              <h3 className="headline text-xl">Confirm Test Submission</h3>
              <p className="body-copy text-xs mt-1">
                Are you sure you want to complete your test and compute results?
              </p>
            </div>

            <div className="space-y-2.5 font-mono text-sm bg-[var(--surface-elevated)] p-4 rounded-xl">
              <div className="flex justify-between">
                <span>Total Questions:</span>
                <strong>{totalQuestions}</strong>
              </div>
              <div className="flex justify-between text-emerald-600">
                <span>Questions Answered:</span>
                <strong>{answeredCount}</strong>
              </div>
              <div className="flex justify-between text-rose-500">
                <span>Unanswered Questions:</span>
                <strong>{unansweredCount}</strong>
              </div>
              <div className="flex justify-between text-amber-600">
                <span>Marked for Review:</span>
                <strong>{markedReviewCount}</strong>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowSubmitModal(false)}
                className="px-4 py-2 rounded-lg border text-xs font-mono text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
              >
                Continue Test
              </button>
              <button
                type="button"
                onClick={handleFinalSubmit}
                disabled={submitting}
                className="brand-button px-5 py-2 text-xs font-mono flex items-center gap-2"
              >
                {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>{submitting ? "Scoring..." : "Yes, Submit Test"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
