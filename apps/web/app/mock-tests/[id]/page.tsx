"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import {
  Clock,
  Flag,
  ChevronLeft,
  ChevronRight,
  Send,
  Loader2,
  AlertCircle,
  ShieldAlert,
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
  const [timeLeftSeconds, setTimeLeftSeconds] = useState<number>(1800);
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
        setError("Test session not found or generation failed.");
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
          handleFinalSubmit();
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
      alert(err.message || "Submission failed. Please check network and retry.");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="editorial-card p-16 flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12 border border-[var(--border)]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
        <p className="text-sm font-medium text-[var(--text-secondary)]">Preparing examination environment...</p>
      </div>
    );
  }

  if (error || !test || !test.questions || test.questions.length === 0) {
    return (
      <div className="editorial-card p-12 text-center space-y-4 max-w-md mx-auto my-12 border border-[var(--border)]">
        <AlertCircle className="w-10 h-10 mx-auto text-[var(--danger)]" />
        <h3 className="headline text-xl font-bold text-[var(--text-primary)]">Test Session Unavailable</h3>
        <p className="body-copy text-sm text-[var(--text-secondary)]">{error || "No questions found in this test."}</p>
        <button
          onClick={() => router.push("/mock-tests")}
          className="button-base button-primary text-xs px-4 py-2 font-semibold"
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
  const isTimeCritical = timeLeftSeconds < 300;

  return (
    <div className="max-w-6xl mx-auto space-y-6 page-enter">
      {/* Sticky Exam Bar */}
      <div className="editorial-card p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4 sticky top-16 z-20 shadow-md border border-[var(--border)] bg-[var(--surface)]">
        <div>
          <span className="badge-editorial text-[10px] text-[var(--accent)] border-[var(--accent)] mb-1">
            {test.exam_name}
          </span>
          <h2 className="headline text-base sm:text-lg font-bold text-[var(--text-primary)]">
            {test.domain || "Comprehensive Syllabus"} Examination
          </h2>
        </div>

        {/* Timer Display */}
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold font-mono border transition-all ${
            isTimeCritical
              ? "bg-[var(--danger-soft)] border-[color-mix(in_srgb,var(--danger)_40%,var(--border))] text-[var(--danger)] animate-pulse"
              : "bg-[var(--surface-muted)] border-[var(--border)] text-[var(--text-primary)]"
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
          className="button-base button-primary text-xs px-5 py-2 flex items-center gap-2 font-semibold shadow-xs"
        >
          {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          <span>Finish & Submit</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Main Question Column */}
        <div className="lg:col-span-3 editorial-card p-6 md:p-8 space-y-6 border border-[var(--border)] shadow-xs bg-[var(--surface)]">
          {/* Question Header */}
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <span className="text-xs font-bold font-mono text-[var(--accent)] uppercase tracking-wider">
              Question {currentIndex + 1} of {totalQuestions}
            </span>

            <button
              type="button"
              onClick={() => handleToggleReview(currentQ.id)}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                reviewMarked[currentQ.id]
                  ? "bg-[var(--warning-soft)] border-amber-300 text-amber-700 font-semibold"
                  : "bg-[var(--surface)] hover:bg-[var(--surface-muted)] text-[var(--text-secondary)] border-[var(--border)]"
              }`}
            >
              <Flag className={`w-3.5 h-3.5 ${reviewMarked[currentQ.id] ? "fill-current" : ""}`} />
              <span>{reviewMarked[currentQ.id] ? "Marked for Review" : "Mark for Review"}</span>
            </button>
          </div>

          {/* Question Text */}
          <div>
            <h3 className="text-base md:text-lg font-bold text-[var(--text-primary)] leading-relaxed">
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
                  className={`w-full p-4 rounded-xl text-left text-sm transition-all flex items-start gap-3.5 border ${
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

          {/* Footer Navigation */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-[var(--border)] text-xs">
            <button
              type="button"
              onClick={() => handleClearAnswer(currentQ.id)}
              disabled={!answers[currentQ.id.toString()]}
              className="text-[var(--text-secondary)] hover:text-[var(--danger)] disabled:opacity-30 transition-colors font-medium"
            >
              Clear Choice
            </button>

            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((prev) => prev - 1)}
                className="button-base button-secondary px-4 py-2 text-xs font-semibold disabled:opacity-30 flex items-center gap-1.5"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <button
                type="button"
                disabled={currentIndex === totalQuestions - 1}
                onClick={() => setCurrentIndex((prev) => prev + 1)}
                className="button-base button-primary px-5 py-2 text-xs font-semibold disabled:opacity-30 flex items-center gap-1.5"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Question Palette Sidebar */}
        <div className="editorial-card p-5 space-y-5 border border-[var(--border)] shadow-xs bg-[var(--surface)]">
          <div className="border-b border-[var(--border)] pb-3">
            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
              Question Palette
            </h4>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-1 gap-2 text-[11px] text-[var(--text-secondary)]">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[var(--success)]" />
              <span>Answered ({answeredCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[var(--border)]" />
              <span>Unanswered ({unansweredCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-amber-500" />
              <span>Marked for Review ({markedReviewCount})</span>
            </div>
          </div>

          {/* Question buttons grid */}
          <div className="grid grid-cols-5 gap-2 pt-2">
            {test.questions.map((q, idx) => {
              const hasAns = !!answers[q.id.toString()];
              const isMarked = !!reviewMarked[q.id];
              const isCurrent = idx === currentIndex;

              let btnStyle = "bg-[var(--surface-muted)] text-[var(--text-secondary)] border-[var(--border)]";
              if (isMarked) {
                btnStyle = "bg-[var(--warning-soft)] text-amber-700 font-bold border-amber-300";
              } else if (hasAns) {
                btnStyle = "bg-[var(--success-soft)] text-[var(--success)] font-bold border-[color-mix(in_srgb,var(--success)_30%,var(--border))]";
              }

              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => setCurrentIndex(idx)}
                  className={`h-9 w-full rounded-lg text-xs font-semibold transition-all border flex items-center justify-center ${btnStyle} ${
                    isCurrent ? "ring-2 ring-[var(--accent)] font-bold scale-105" : ""
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="editorial-card max-w-md w-full p-6 space-y-5 shadow-xl border border-[var(--border)] bg-[var(--surface)]">
            <div className="border-b border-[var(--border)] pb-3">
              <span className="badge-editorial text-[10px] text-[var(--accent)] border-[var(--accent)] mb-1">
                CONFIRMATION
              </span>
              <h3 className="headline text-xl font-bold text-[var(--text-primary)]">
                Submit Test Session?
              </h3>
              <p className="body-copy text-xs text-[var(--text-secondary)] mt-1">
                Your responses will be evaluated against the official answer keys and scored with negative marking.
              </p>
            </div>

            <div className="space-y-2.5 text-xs bg-[var(--surface-muted)] p-4 rounded-xl border border-[var(--border)]">
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Total Questions:</span>
                <strong className="text-[var(--text-primary)] font-bold">{totalQuestions}</strong>
              </div>
              <div className="flex justify-between text-[var(--success)]">
                <span>Questions Answered:</span>
                <strong className="font-bold">{answeredCount}</strong>
              </div>
              <div className="flex justify-between text-[var(--danger)]">
                <span>Unanswered:</span>
                <strong className="font-bold">{unansweredCount}</strong>
              </div>
              <div className="flex justify-between text-amber-700">
                <span>Marked for Review:</span>
                <strong className="font-bold">{markedReviewCount}</strong>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowSubmitModal(false)}
                className="button-base button-ghost px-4 py-2 text-xs"
              >
                Continue Test
              </button>
              <button
                type="button"
                onClick={handleFinalSubmit}
                disabled={submitting}
                className="button-base button-primary px-5 py-2 text-xs font-semibold flex items-center gap-2"
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
