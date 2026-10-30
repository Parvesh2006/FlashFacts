"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Clock,
  ExternalLink,
  ShieldCheck,
  Share2,
  GraduationCap,
  BookOpen,
  CheckCircle2,
  XCircle,
  Tag,
  MapPin,
  Check,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import type { Event, EventExamIntelligence, MCQ, MCQResponse } from "@/types/event";
import type { EventLocationResponse } from "@/types/location";
import { DomainBadge } from "@/components/common/badge";
import { formatDate, formatDateTime } from "@/lib/utils";
import { EventCard } from "./event-card";
import { BackButton } from "@/components/navigation/back-button";
import { fetchEventExamRelevance, fetchEventMCQ } from "@/services/exams";
import { fetchEventLocations } from "@/services/locations";

interface EventDetailViewProps {
  event: Event;
  relatedEvents?: Event[];
}

export function EventDetailView({ event, relatedEvents = [] }: EventDetailViewProps) {
  const confidencePercent = Math.round((event.confidence_score || 1.0) * 100);

  const [examData, setExamData] = useState<EventExamIntelligence | null>(null);
  const [examLoading, setExamLoading] = useState(true);

  const [locationData, setLocationData] = useState<EventLocationResponse | null>(null);

  const [mcqData, setMcqData] = useState<MCQResponse | null>(null);
  const [mcqLoading, setMcqLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [revealedAnswers, setRevealedAnswers] = useState<Record<number, boolean>>({});
  const [copiedLink, setCopiedLink] = useState(false);
  const [fontSize, setFontSize] = useState<"normal" | "large">("normal");

  useEffect(() => {
    setExamLoading(true);
    fetchEventExamRelevance(event.id)
      .then(setExamData)
      .catch(() => setExamData(null))
      .finally(() => setExamLoading(false));

    fetchEventLocations(event.id)
      .then(setLocationData)
      .catch(() => setLocationData(null));
  }, [event.id]);

  const loadMCQs = () => {
    setMcqLoading(true);
    setSelectedAnswers({});
    setRevealedAnswers({});
    fetchEventMCQ(event.id)
      .then(setMcqData)
      .catch(() => setMcqData(null))
      .finally(() => setMcqLoading(false));
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: event.title,
        text: event.summary,
        url: window.location.href,
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  };

  const selectAnswer = (qIdx: number, letter: string) => {
    if (revealedAnswers[qIdx]) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIdx]: letter }));
  };

  const revealAnswer = (qIdx: number) => {
    setRevealedAnswers((prev) => ({ ...prev, [qIdx]: true }));
  };

  const hasValidPhoto =
    event.url &&
    (event.url.endsWith(".jpg") ||
      event.url.endsWith(".jpeg") ||
      event.url.endsWith(".png") ||
      event.url.endsWith(".webp"));

  return (
    <div className="space-y-8 max-w-4xl mx-auto page-enter">
      <div className="flex items-center justify-between">
        <BackButton label="Back to Current Affairs" fallbackHref="/explore" />
        <div className="flex items-center gap-2">
          {/* Reading Font Size Toggle */}
          <div className="hidden sm:flex items-center gap-1 border border-[var(--border)] rounded-lg p-1 bg-[var(--surface)] text-xs font-mono text-[var(--text-muted)]">
            <button
              onClick={() => setFontSize("normal")}
              className={`px-2 py-0.5 rounded ${fontSize === "normal" ? "bg-[var(--surface-muted)] text-[var(--text-primary)] font-bold" : "hover:text-[var(--text-primary)]"}`}
              title="Standard reading text"
            >
              A
            </button>
            <button
              onClick={() => setFontSize("large")}
              className={`px-2 py-0.5 rounded text-sm ${fontSize === "large" ? "bg-[var(--surface-muted)] text-[var(--text-primary)] font-bold" : "hover:text-[var(--text-primary)]"}`}
              title="Larger reading text for extended study"
            >
              A+
            </button>
          </div>

          <button
            type="button"
            onClick={handleShare}
            className="button-base button-secondary px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-xs"
          >
            {copiedLink ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-emerald-600 font-semibold">Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5" />
                <span>Share</span>
              </>
            )}
          </button>
        </div>
      </div>

      <article className="editorial-card p-6 md:p-10 space-y-6 bg-[var(--surface)] border border-[var(--border)] shadow-xs">
        {/* Category & Status Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
          <div className="flex flex-wrap items-center gap-2.5">
            <DomainBadge domain={event.domain || "Technology"} className="text-xs py-1 px-3" />

            {locationData && locationData.locations.length > 0 && (
              <div className="badge-editorial text-xs font-mono text-[var(--brand-primary)] border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)]">
                <MapPin className="w-3 h-3" />
                <span>{locationData.locations.map((l) => l.name).join(" · ")}</span>
              </div>
            )}

            {event.event_type && (
              <span className="badge-editorial text-xs flex items-center gap-1">
                <Tag className="w-3 h-3 text-[var(--accent)]" />
                <span>{event.event_type}</span>
              </span>
            )}

            <span className="badge-editorial text-xs text-emerald-600 border-[color-mix(in_srgb,var(--success)_30%,var(--border))] bg-[var(--success-soft)]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{confidencePercent}% Verified</span>
            </span>
          </div>
        </div>

        {/* Real News Image Container if available */}
        {hasValidPhoto && (
          <div className="w-full h-64 sm:h-80 overflow-hidden rounded-xl border border-[var(--border)] relative bg-[var(--surface-muted)]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={event.url}
              alt={event.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            <span className="absolute bottom-2 right-2 px-2.5 py-1 rounded text-xs bg-black/70 text-white font-mono backdrop-blur-xs">
              Photo: {event.source}
            </span>
          </div>
        )}

        {/* Editorial Headline */}
        <h1 className="headline text-2xl sm:text-3xl md:text-4xl lg:text-[2.6rem] leading-tight text-[var(--text-primary)] font-bold">
          {event.title}
        </h1>

        {/* Temporal & Metadata Panel */}
        <div className="p-4 border border-[var(--border)] rounded-xl bg-[var(--surface-muted)] flex flex-wrap items-center gap-6 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[var(--accent)]" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">Event Date</span>
              <span className="font-semibold text-[var(--text-primary)]">{formatDate(event.event_date)}</span>
            </div>
          </div>

          <div className="w-px h-8 bg-[var(--border)] hidden sm:block" />

          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[var(--brand-primary)]" />
            <div>
              <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">Indexed At</span>
              <span className="font-semibold text-[var(--text-primary)]">{formatDateTime(event.published_at)}</span>
            </div>
          </div>

          <div className="w-px h-8 bg-[var(--border)] hidden sm:block" />

          <div>
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">Source Provenance</span>
            <span className="font-semibold text-[var(--text-primary)]">{event.source || "Official Gazette"}</span>
          </div>
        </div>

        {/* Focused Reading Column (Natural warm-white editorial text) */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
            <span className="badge-editorial text-xs text-[var(--brand-primary)] border-[var(--brand-primary-border)] font-semibold">
              EXAMINATION DISPATCH
            </span>
            {event.syllabus_topic && (
              <span className="badge-editorial text-xs font-mono">
                {event.syllabus_topic}
              </span>
            )}
          </div>

          <div
            className={`body-copy text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap ${
              fontSize === "large" ? "text-lg md:text-xl leading-loose" : "text-base md:text-[1.0625rem] leading-relaxed"
            }`}
          >
            {event.summary}
          </div>

          {event.inclusion_reason && (
            <p className="text-xs text-[var(--text-muted)] italic pt-1">
              Curriculum Grounding: {event.inclusion_reason}
            </p>
          )}
        </div>

        {/* Key Takeaway / Significance Panel */}
        {event.why_it_matters && (
          <div className="p-5 rounded-xl border border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] space-y-2">
            <span className="badge-editorial text-[10px] text-[var(--brand-primary)] border-[var(--brand-primary-border)] font-bold">
              WHY IT MATTERS FOR EXAMS
            </span>
            <p className="body-copy text-sm sm:text-base leading-relaxed text-[var(--text-primary)]">
              {event.why_it_matters}
            </p>
          </div>
        )}

        {/* Key Entities */}
        {event.entities && event.entities.length > 0 && (
          <div className="space-y-2 pt-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
              Key Syllabus Entities
            </span>
            <div className="flex flex-wrap gap-2">
              {event.entities.map((entity) => (
                <span key={entity.id} className="badge-editorial text-xs font-mono">
                  {entity.name} <span className="text-[var(--text-muted)] font-normal">({entity.entity_type})</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Original Source Reference */}
        {event.source_url && (
          <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="space-y-1 min-w-0">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
                Primary Publication Source
              </span>
              <p className="text-xs text-[var(--text-secondary)] font-mono truncate max-w-lg">
                {event.source_url}
              </p>
            </div>
            <a
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="button-base button-secondary px-3.5 py-1.5 text-xs font-semibold shrink-0"
            >
              <span>Visit Official Source</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        )}
      </article>

      {/* Target Exam Relevance Matrix */}
      {examLoading ? (
        <div className="editorial-card p-6 flex items-center justify-center gap-3 border border-[var(--border)]">
          <span className="text-xs text-[var(--text-secondary)]">Analyzing syllabus mapping...</span>
        </div>
      ) : examData && examData.relevant_exams && examData.relevant_exams.length > 0 ? (
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
            <h2 className="headline text-xl font-bold flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-[var(--accent)]" />
              <span>Target Examination Scoring Matrix</span>
            </h2>
            <span className="text-xs font-mono text-[var(--text-muted)]">
              {examData.relevant_exams.length} Exam Patterns Evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examData.relevant_exams.map((rel, idx) => (
              <div key={idx} className="editorial-card p-5 space-y-3 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
                  <span className="font-bold text-sm text-[var(--text-primary)]">{rel.exam_name}</span>
                  <span className="badge-editorial text-xs text-[var(--brand-primary)] border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] font-bold">
                    {rel.relevance_score}% Relevance
                  </span>
                </div>
                <div className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1">
                  {rel.section && (
                    <p className="font-medium text-[var(--text-primary)]">Section: {rel.section}</p>
                  )}
                  {rel.reasons && rel.reasons.length > 0 && (
                    <p>{rel.reasons.join(". ")}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {/* Comprehension Drill MCQs */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <div>
            <h2 className="headline text-xl font-bold flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-[var(--brand-primary)]" />
              <span>Comprehension Practice Drill</span>
            </h2>
            <p className="body-copy-sm text-xs text-[var(--text-secondary)]">
              Test your grasp of this development with curriculum-aligned questions
            </p>
          </div>

          {!mcqData && (
            <button
              onClick={loadMCQs}
              disabled={mcqLoading}
              className="button-base button-primary px-4 py-2 text-xs font-semibold shadow-xs"
            >
              {mcqLoading ? "Generating Drill..." : "Start Question Drill"}
            </button>
          )}
        </div>

        {mcqData && mcqData.mcqs.length > 0 && (
          <div className="space-y-5">
            {mcqData.mcqs.map((mcq, qIdx) => {
              const selected = selectedAnswers[qIdx];
              const revealed = revealedAnswers[qIdx];
              const isCorrect = selected === mcq.correct_answer;

              return (
                <div key={qIdx} className="editorial-card p-6 space-y-4 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
                  <h3 className="headline text-base font-bold text-[var(--text-primary)] leading-relaxed">
                    <span className="text-[var(--brand-primary)] font-mono mr-2">Q{qIdx + 1}.</span>
                    {mcq.question}
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    {mcq.options.map((opt, oIdx) => {
                      const letter = String.fromCharCode(65 + oIdx);
                      const isOptionSelected = selected === letter;
                      const cleanText = opt.replace(/^[A-D][.)]\s*/i, "").trim();

                      let btnStyle = "bg-[var(--surface-muted)] border-[var(--border)] text-[var(--text-primary)]";
                      if (revealed) {
                        if (letter === mcq.correct_answer) {
                          btnStyle = "bg-[var(--success-soft)] border-[color-mix(in_srgb,var(--success)_40%,var(--border))] text-[var(--success)] font-semibold";
                        } else if (isOptionSelected) {
                          btnStyle = "bg-[var(--danger-soft)] border-[color-mix(in_srgb,var(--danger)_40%,var(--border))] text-[var(--danger)] font-semibold";
                        }
                      } else if (isOptionSelected) {
                        btnStyle = "bg-[var(--brand-primary-soft)] border-[var(--brand-primary)] text-[var(--brand-primary)] font-semibold shadow-xs";
                      }

                      return (
                        <button
                          key={oIdx}
                          type="button"
                          onClick={() => selectAnswer(qIdx, letter)}
                          className={`p-3.5 rounded-xl border text-left flex items-start gap-3 transition-all ${btnStyle}`}
                        >
                          <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 bg-[var(--surface)] border border-[var(--border)]">
                            {letter}
                          </span>
                          <span className="flex-1 leading-snug pt-0.5">{cleanText}</span>
                          {revealed && letter === mcq.correct_answer && (
                            <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0 mt-0.5" />
                          )}
                          {revealed && isOptionSelected && !isCorrect && (
                            <XCircle className="w-4 h-4 text-[var(--danger)] shrink-0 mt-0.5" />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-[var(--border)] text-xs">
                    {selected && !revealed && (
                      <button
                        type="button"
                        onClick={() => revealAnswer(qIdx)}
                        className="button-base button-primary px-4 py-1.5 text-xs font-semibold"
                      >
                        Check Answer
                      </button>
                    )}

                    {revealed && (
                      <div className="w-full space-y-2">
                        <div className="flex items-center gap-2">
                          {isCorrect ? (
                            <span className="text-[var(--success)] font-bold flex items-center gap-1.5 text-xs">
                              <CheckCircle2 className="w-4 h-4" /> Correct Answer!
                            </span>
                          ) : (
                            <span className="text-[var(--danger)] font-bold flex items-center gap-1.5 text-xs">
                              <XCircle className="w-4 h-4" /> Incorrect. Correct option is {mcq.correct_answer}
                            </span>
                          )}
                        </div>
                        {mcq.explanation && (
                          <div className="p-3.5 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] text-xs text-[var(--text-secondary)] leading-relaxed">
                            <span className="font-semibold text-[var(--text-primary)] block mb-1">Academic Rationale:</span>
                            {mcq.explanation}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Related Events Section */}
      {relatedEvents.length > 0 && (
        <section className="space-y-4 pt-4 border-t border-[var(--border)]">
          <div className="flex items-center justify-between">
            <h2 className="headline text-xl font-bold flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-[var(--brand-primary)]" />
              <span>Related Current Affairs</span>
            </h2>
            <Link
              href="/explore"
              className="text-xs font-semibold text-[var(--brand-primary)] hover:underline"
            >
              Browse All Archive →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {relatedEvents.slice(0, 3).map((rel) => (
              <EventCard key={rel.id} event={rel} compact />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
