"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  GraduationCap,
  Building2,
  Landmark,
  Coins,
  TrainTrack,
  CheckCircle2,
  Clock,
  BookOpen,
  ArrowRight,
  Sparkles,
  Loader2,
  ExternalLink,
  HelpCircle,
  XCircle,
} from "lucide-react";
import { fetchExams, fetchExamEvents, fetchEventMCQ, Exam } from "@/services/exams";
import { ExamEvent, MCQ, MCQResponse } from "@/types/event";
import { BackButton } from "@/components/navigation/back-button";
import { DomainBadge } from "@/components/common/badge";
import { formatDate } from "@/lib/utils";

const EXAM_ICON_MAP: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  "tnpsc-group-4": Building2,
  "tnpsc-group-2": Building2,
  "ssc-cgl": GraduationCap,
  "ssc-chsl": GraduationCap,
  "upsc-cse": Landmark,
  "rrb-ntpc": TrainTrack,
  banking: Coins,
};

export default function ExamsPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [loadingExams, setLoadingExams] = useState(true);

  const [examEvents, setExamEvents] = useState<ExamEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);

  // Active event for MCQ practice modal/drawer
  const [activePracticeEvent, setActivePracticeEvent] = useState<ExamEvent | null>(null);
  const [mcqData, setMcqData] = useState<MCQResponse | null>(null);
  const [mcqLoading, setMcqLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [revealedAnswers, setRevealedAnswers] = useState<Record<number, boolean>>({});

  useEffect(() => {
    async function loadExams() {
      try {
        const data = await fetchExams();
        setExams(data);
        if (data.length > 0) {
          setSelectedExam(data[0]);
        }
      } catch (err) {
        console.error("Failed to load exams", err);
      } finally {
        setLoadingExams(false);
      }
    }
    loadExams();
  }, []);

  useEffect(() => {
    if (!selectedExam) return;
    setLoadingEvents(true);
    fetchExamEvents(selectedExam.id, { limit: 20 })
      .then((res) => {
        setExamEvents(res.events || []);
      })
      .catch((err) => {
        console.error("Failed to load exam events", err);
        setExamEvents([]);
      })
      .finally(() => setLoadingEvents(false));
  }, [selectedExam]);

  const startPractice = (examEvent: ExamEvent) => {
    setActivePracticeEvent(examEvent);
    setMcqLoading(true);
    setSelectedAnswers({});
    setRevealedAnswers({});
    fetchEventMCQ(examEvent.event.id, selectedExam?.id)
      .then(setMcqData)
      .catch(() => setMcqData(null))
      .finally(() => setMcqLoading(false));
  };

  const selectAnswer = (qIdx: number, letter: string) => {
    if (revealedAnswers[qIdx]) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIdx]: letter }));
  };

  const revealAnswer = (qIdx: number) => {
    setRevealedAnswers((prev) => ({ ...prev, [qIdx]: true }));
  };

  return (
    <div className="space-y-7 max-w-6xl mx-auto">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b pb-5">
        <div className="eyebrow flex items-center gap-2 mb-2">
          <GraduationCap className="w-4 h-4" />
          <span>Competitive Exam Preparation</span>
        </div>

        <h1 className="headline text-3xl md:text-4xl">
          Exam Intelligence
        </h1>

        <p className="body-copy text-base mt-2 max-w-3xl">
          Turn live FlashFacts into focused exam preparation. Select your
          examination to see current-affairs events scored for relevance and practice source-grounded questions.
        </p>
      </div>

      {/* Exam Selection */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="headline text-xl">Choose your exam</h2>
            <p className="body-copy text-sm mt-1">
              Events are scored specifically for each target exam pattern.
            </p>
          </div>

          <div className="soft-badge hidden sm:flex items-center gap-2 text-sm font-mono px-3 py-2">
            <Clock className="w-4 h-4 accent-mark" />
            <span>Live Relevance Engine</span>
          </div>
        </div>

        {loadingExams ? (
          <div className="editorial-card p-8 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin accent-mark" />
            <span className="body-copy">Loading examinations...</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {exams.map((exam) => {
              const IconComponent = EXAM_ICON_MAP[exam.id] || BookOpen;
              const isSelected = selectedExam?.id === exam.id;

              return (
                <button
                  key={exam.id}
                  onClick={() => setSelectedExam(exam)}
                  aria-pressed={isSelected}
                  className={`editorial-card editorial-card-hover p-4 text-left transition-all ${
                    isSelected
                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)]"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                        isSelected ? "brand-button" : "soft-badge"
                      }`}
                    >
                      <IconComponent className="w-4 h-4" />
                    </div>

                    {isSelected && (
                      <CheckCircle2 className="w-4 h-4 text-[var(--brand-primary)]" />
                    )}
                  </div>

                  <h3 className="font-bold text-sm text-[var(--text-primary)] font-mono">
                    {exam.code}
                  </h3>

                  <p className="text-xs text-[var(--text-secondary)] font-mono mt-0.5 leading-snug">
                    {exam.name}
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Target Exam Details & Relevant Events */}
      {selectedExam && (
        <section className="space-y-6">
          <div className="editorial-card p-5 md:p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="eyebrow text-xs block mb-1">
                  TARGET EXAMINATION
                </span>

                <h2 className="headline text-2xl">
                  {selectedExam.name}
                  <span className="text-[var(--text-secondary)]">
                    {" "}
                    ({selectedExam.code})
                  </span>
                </h2>

                <p className="body-copy text-sm mt-2 max-w-3xl">
                  {selectedExam.description}
                </p>
              </div>

              <div className="flex items-center gap-2 soft-badge px-4 py-2 text-xs font-mono shrink-0">
                <Sparkles className="w-4 h-4 accent-mark" />
                <span>Section: {selectedExam.category.toUpperCase()}</span>
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="headline text-xl">Relevant Current Affairs</h3>
                <p className="body-copy text-sm mt-0.5">
                  High-yield events filtered and scored for {selectedExam.name}.
                </p>
              </div>
              <span className="meta-text text-xs">
                {examEvents.length} events loaded
              </span>
            </div>

            {loadingEvents ? (
              <div className="editorial-card p-8 flex items-center justify-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin accent-mark" />
                <span className="body-copy">Scoring and matching events...</span>
              </div>
            ) : examEvents.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {examEvents.map((item) => (
                  <div key={item.event.id} className="editorial-card editorial-card-hover p-5 flex flex-col justify-between space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <DomainBadge domain={item.event.domain || "General"} className="text-[10px]" />
                        <span className="status-success text-xs font-mono px-2 py-0.5 rounded">
                          {item.relevance_score}% Relevance
                        </span>
                      </div>

                      <Link href={`/event/${item.event.id}`} className="block group">
                        <h4 className="headline text-lg group-hover:text-[var(--brand-primary)] transition-colors">
                          {item.event.title}
                        </h4>
                      </Link>

                      <p className="body-copy text-xs line-clamp-3">
                        {item.event.summary}
                      </p>

                      {item.reasons.length > 0 && (
                        <div className="text-[11px] font-mono text-[var(--text-muted)] bg-[var(--surface-muted)] p-2 rounded">
                          <span className="font-semibold text-[var(--text-primary)]">Relevance signals: </span>
                          {item.reasons.join(" · ")}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t text-xs font-mono">
                      <span className="meta-text">{formatDate(item.event.event_date)}</span>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/event/${item.event.id}`}
                          className="button-base button-secondary text-xs px-2.5 py-1 flex items-center gap-1"
                        >
                          <span>Details</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>

                        <button
                          type="button"
                          onClick={() => startPractice(item)}
                          className="brand-button text-xs px-3 py-1 flex items-center gap-1 font-semibold rounded"
                        >
                          <HelpCircle className="w-3 h-3" />
                          <span>Practice MCQ</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="editorial-card p-8 text-center space-y-2">
                <p className="headline text-lg">No exam events matched</p>
                <p className="meta-text text-sm">Try selecting a different examination.</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* MCQ Practice Drawer / Modal */}
      {activePracticeEvent && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 overflow-y-auto">
          <div className="editorial-card max-w-2xl w-full p-6 space-y-5 bg-[var(--surface)] max-h-[90vh] overflow-y-auto border border-[var(--border)]">
            <div className="flex items-start justify-between border-b pb-4">
              <div>
                <span className="eyebrow text-xs">PRACTICE MODE · {selectedExam?.code}</span>
                <h3 className="headline text-xl mt-1">{activePracticeEvent.event.title}</h3>
              </div>
              <button
                type="button"
                onClick={() => setActivePracticeEvent(null)}
                className="button-base button-secondary icon-button p-1"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {mcqLoading ? (
              <div className="py-12 flex items-center justify-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin accent-mark" />
                <span className="body-copy">Generating source-grounded questions...</span>
              </div>
            ) : mcqData && mcqData.mcqs.length > 0 ? (
              <div className="space-y-6">
                {mcqData.used_fallback && (
                  <div className="text-xs font-mono text-[var(--text-muted)] bg-[var(--surface-muted)] p-2 rounded">
                    Questions generated using deterministic fallback (AI provider offline)
                  </div>
                )}
                {mcqData.mcqs.map((mcq, qIdx) => (
                  <div key={qIdx} className="editorial-panel p-4 space-y-3">
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                      Q{qIdx + 1}. {mcq.question}
                    </p>
                    <div className="grid grid-cols-1 gap-2">
                      {mcq.options.map((opt, oIdx) => {
                        const letter = String.fromCharCode(65 + oIdx);
                        const isSelected = selectedAnswers[qIdx] === letter;
                        const isCorrect = mcq.correct_answer === letter;
                        const isRevealed = !!revealedAnswers[qIdx];

                        let optClass = "editorial-card p-3 text-xs md:text-sm cursor-pointer transition-all text-left";
                        if (isRevealed) {
                          if (isCorrect) {
                            optClass += " border-[var(--success)] bg-[var(--success-soft)]";
                          } else if (isSelected && !isCorrect) {
                            optClass += " border-[var(--danger)] bg-[var(--danger-soft)]";
                          }
                        } else if (isSelected) {
                          optClass += " border-[var(--brand-primary)] bg-[var(--brand-primary-soft)]";
                        } else {
                          optClass += " editorial-card-hover";
                        }

                        return (
                          <button
                            key={oIdx}
                            type="button"
                            onClick={() => selectAnswer(qIdx, letter)}
                            className={optClass}
                          >
                            <div className="flex items-center gap-2">
                              {isRevealed && isCorrect && <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0" />}
                              {isRevealed && isSelected && !isCorrect && <XCircle className="w-4 h-4 text-[var(--danger)] shrink-0" />}
                              <span>{opt}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                    <div className="flex items-center gap-3">
                      {selectedAnswers[qIdx] && !revealedAnswers[qIdx] && (
                        <button
                          type="button"
                          onClick={() => revealAnswer(qIdx)}
                          className="brand-button px-4 py-1.5 text-xs font-mono font-semibold rounded"
                        >
                          Check Answer
                        </button>
                      )}
                      {revealedAnswers[qIdx] && (
                        <div className="text-xs body-copy bg-[var(--surface-muted)] p-3 rounded w-full">
                          <span className="font-semibold text-[var(--text-primary)]">Explanation: </span>
                          {mcq.explanation}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center meta-text text-sm">
                No questions could be safely generated for this event.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}