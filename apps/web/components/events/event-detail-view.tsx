"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Clock,
  ExternalLink,
  ShieldCheck,
  Database,
  Share2,
  Sparkles,
  GraduationCap,
  BookOpen,
  CheckCircle2,
  XCircle,
  Tag,
  MapPin,
  GitCommit,
} from "lucide-react";
import type { Event, EventExamIntelligence, MCQ, MCQResponse } from "@/types/event";
import type { EventLocationResponse, EventTimelineResponse } from "@/types/location";
import { DomainBadge } from "@/components/common/badge";
import { formatDate, formatDateTime } from "@/lib/utils";
import { EventCard } from "./event-card";
import { BackButton } from "@/components/navigation/back-button";
import { fetchEventExamRelevance, fetchEventMCQ } from "@/services/exams";
import { fetchEventLocations, fetchEventTimeline } from "@/services/locations";

interface EventDetailViewProps {
  event: Event;
  relatedEvents?: Event[];
}

export function EventDetailView({ event, relatedEvents = [] }: EventDetailViewProps) {
  const confidencePercent = Math.round((event.confidence_score || 1.0) * 100);

  const [examData, setExamData] = useState<EventExamIntelligence | null>(null);
  const [examLoading, setExamLoading] = useState(true);

  const [locationData, setLocationData] = useState<EventLocationResponse | null>(null);
  const [timelineData, setTimelineData] = useState<EventTimelineResponse | null>(null);

  const [mcqData, setMcqData] = useState<MCQResponse | null>(null);
  const [mcqLoading, setMcqLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [revealedAnswers, setRevealedAnswers] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setExamLoading(true);
    fetchEventExamRelevance(event.id)
      .then(setExamData)
      .catch(() => setExamData(null))
      .finally(() => setExamLoading(false));

    fetchEventLocations(event.id)
      .then(setLocationData)
      .catch(() => setLocationData(null));

    fetchEventTimeline(event.id)
      .then(setTimelineData)
      .catch(() => setTimelineData(null));
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
      alert("Event URL copied to clipboard.");
    }
  };

  const selectAnswer = (qIdx: number, letter: string) => {
    if (revealedAnswers[qIdx]) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIdx]: letter }));
  };

  const revealAnswer = (qIdx: number) => {
    setRevealedAnswers((prev) => ({ ...prev, [qIdx]: true }));
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <BackButton label="Back to Explore" fallbackHref="/explore" />
      </div>

      <article className="editorial-card p-6 md:p-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
          <div className="flex flex-wrap items-center gap-3">
            <DomainBadge domain={event.domain || "Technology"} className="text-xs py-1 px-3" />

            {locationData && locationData.locations.length > 0 && (
              <div className="flex items-center gap-1.5 font-mono text-xs text-[var(--brand-primary)] bg-[var(--brand-primary-soft)] px-2.5 py-1 rounded-md border border-[var(--brand-primary-border)]">
                <MapPin className="w-3.5 h-3.5" />
                <span>{locationData.locations.map((l) => l.name).join(" · ")}</span>
              </div>
            )}

            {event.event_type && (
              <span className="soft-badge text-xs px-2.5 py-1 rounded-md flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {event.event_type}
              </span>
            )}
            <span className="status-success flex items-center gap-1 text-xs font-mono px-2.5 py-1 rounded-md">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{confidencePercent}% Confidence</span>
            </span>
          </div>

          <button
            type="button"
            onClick={handleShare}
            className="button-base button-secondary icon-button flex items-center gap-1.5 px-3 py-1 text-xs"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share</span>
          </button>
        </div>

        <h1 className="headline text-3xl md:text-5xl">{event.title}</h1>

        <div className="editorial-panel flex flex-wrap items-center gap-6 text-xs font-mono p-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 accent-mark" />
            <div>
              <span className="meta-text uppercase block">Event Date</span>
              <span className="font-semibold text-[var(--text-primary)]">{formatDate(event.event_date)}</span>
            </div>
          </div>

          <div className="w-px h-8 bg-[var(--border)] hidden sm:block" />

          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[var(--brand-primary)]" />
            <div>
              <span className="meta-text uppercase block">Indexed At</span>
              <span className="font-semibold text-[var(--text-primary)]">{formatDateTime(event.published_at)}</span>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="eyebrow">Intelligence Summary</h2>
          <p className="body-copy text-base md:text-lg bg-[var(--surface-muted)] border p-5 rounded-lg">
            {event.summary}
          </p>
        </div>

        <div className="space-y-4">
          {event.why_it_matters && (
            <div>
              <h3 className="eyebrow">Why It Matters</h3>
              <p className="body-copy text-sm mt-2 bg-[var(--brand-primary-soft)] border border-[var(--brand-primary-border)] p-4 rounded-md">
                {event.why_it_matters}
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="editorial-panel p-4">
              <div className="meta-text">Importance Score</div>
              <div className="text-xl font-bold text-[var(--warning)]">{event.importance_score ?? "-"}</div>
            </div>

            <div className="editorial-panel p-4">
              <div className="meta-text">Classification Confidence</div>
              <div className="text-xl font-bold text-[var(--success)]">
                {Math.round((event.classification_confidence ?? 0) * 100)}%
              </div>
            </div>

            <div className="editorial-panel p-4">
              <div className="meta-text">Sources</div>
              <div className="text-sm mt-2">
                {event.sources && event.sources.length > 0 ? (
                  <ul className="list-disc ml-4">
                    {event.sources.map((source) => (
                      <li key={source.id}>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[var(--brand-primary)] hover:underline"
                        >
                          {source.name}
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-[var(--text-secondary)] break-all">{event.source_url}</div>
                )}
              </div>
            </div>
          </div>

          {event.entities && event.entities.length > 0 && (
            <div>
              <h3 className="eyebrow">Key Entities</h3>
              <div className="flex flex-wrap gap-2 mt-2">
                {event.entities.map((entity) => (
                  <span key={entity.id} className="soft-badge text-xs px-3 py-1">
                    {entity.name} <span className="text-[var(--text-muted)]">({entity.entity_type})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Event Timeline Section */}
        {timelineData && timelineData.timeline.length > 0 && (
          <div className="pt-4 border-t space-y-3">
            <div className="flex items-center gap-2">
              <GitCommit className="w-4 h-4 accent-mark" />
              <h3 className="eyebrow">Event Chronology & Context</h3>
            </div>
            <div className="space-y-2">
              {timelineData.timeline.map((node,index) => (
                <div
                   key={`${node.event_id}-${node.position}-${index}`}
                  className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between gap-3 ${
                    node.position === "CURRENT"
                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] font-bold text-[var(--text-primary)]"
                      : "bg-[var(--surface-muted)] text-[var(--text-secondary)]"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="soft-badge px-2 py-0.5 text-[10px] shrink-0">{node.position}</span>
                    <span className="truncate">{node.title}</span>
                  </div>
                  <span className="shrink-0 meta-text">{node.event_date}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {event.source_url && (
          <div className="p-4 rounded-lg border border-[var(--accent-border)] bg-[var(--accent-soft)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="space-y-1">
              <span className="eyebrow block">Primary Publication Source</span>
              <p className="text-xs text-[var(--text-secondary)] font-mono break-all max-w-lg">
                {event.source_url}
              </p>
            </div>
            <a
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="brand-button inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-semibold"
            >
              <span>Visit Source URL</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        )}

        <div className="pt-4 border-t">
          <details className="group">
            <summary className="cursor-pointer meta-text hover:text-[var(--text-primary)] flex items-center gap-2 select-none">
              <Database className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>Technical Provenance Metadata</span>
            </summary>
            <div className="mt-3 p-4 bg-[var(--surface-muted)] border rounded-lg space-y-2 font-mono text-[11px] text-[var(--text-secondary)]">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div>
                  <span>Database ID:</span>{" "}
                  <span className="text-[var(--text-primary)]">{event.id}</span>
                </div>
                <div>
                  <span>Source ID:</span>{" "}
                  <span className="text-[var(--text-primary)]">{event.source_id}</span>
                </div>
                <div className="col-span-1 sm:col-span-2">
                  <span>Deduplication Hash:</span>{" "}
                  <span className="text-[var(--text-primary)] break-all">{event.dedup_hash}</span>
                </div>
                <div>
                  <span>Record Created:</span>{" "}
                  <span className="text-[var(--text-primary)]">{formatDateTime(event.created_at)}</span>
                </div>
                <div>
                  <span>Record Updated:</span>{" "}
                  <span className="text-[var(--text-primary)]">{formatDateTime(event.updated_at)}</span>
                </div>
              </div>
            </div>
          </details>
        </div>
      </article>

      {/* Exam Relevance Section */}
      <section className="editorial-card p-6 space-y-4">
        <div className="flex items-center gap-2 border-b pb-3">
          <GraduationCap className="w-5 h-5 accent-mark" />
          <h2 className="headline text-xl">Competitive Exam Relevance</h2>
        </div>

        {examLoading ? (
          <div className="text-sm meta-text py-4">Analyzing exam relevance...</div>
        ) : examData && examData.relevant_exams.length > 0 ? (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {examData.relevant_exams.map((rel) => (
                <div
                  key={rel.exam_id}
                  className="editorial-panel p-3 flex-1 min-w-[180px]"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm font-bold text-[var(--text-primary)]">
                      {rel.exam_code}
                    </span>
                    <span className="text-xs font-mono text-[var(--brand-primary)]">
                      {rel.relevance_score}%
                    </span>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)]">{rel.section}</div>
                  {rel.reasons.length > 0 && (
                    <div className="text-[11px] text-[var(--text-muted)] mt-1">
                      {rel.reasons.slice(0, 2).join(" · ")}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {examData.key_points.length > 0 && (
              <div>
                <h3 className="eyebrow text-xs mb-2">Key Points for Exams</h3>
                <ul className="list-disc ml-4 space-y-1">
                  {examData.key_points.map((point, i) => (
                    <li key={i} className="body-copy text-sm">{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p className="meta-text text-sm py-2">No strong exam relevance detected for this event.</p>
        )}
      </section>

      {/* MCQ Practice Section */}
      <section className="editorial-card p-6 space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 accent-mark" />
            <h2 className="headline text-xl">Practice MCQ</h2>
          </div>
          <button
            type="button"
            onClick={loadMCQs}
            disabled={mcqLoading}
            className="brand-button px-4 py-2 text-xs font-mono font-semibold rounded-lg disabled:opacity-50"
          >
            {mcqLoading ? "Generating..." : mcqData ? "New Questions" : "Generate Questions"}
          </button>
        </div>

        {mcqLoading && (
          <div className="text-sm meta-text py-4">Generating practice questions from event content...</div>
        )}

        {mcqData && mcqData.mcqs.length > 0 && (
          <div className="space-y-6">
            {mcqData.used_fallback && (
              <div className="text-xs font-mono text-[var(--text-muted)] bg-[var(--surface-muted)] p-2 rounded">
                Source-grounded deterministic MCQ fallback (AI provider unavailable)
              </div>
            )}
            {mcqData.mcqs.map((mcq, qIdx) => (
              <MCQCard
                key={qIdx}
                mcq={mcq}
                qIdx={qIdx}
                selectedAnswer={selectedAnswers[qIdx]}
                revealed={!!revealedAnswers[qIdx]}
                onSelect={selectAnswer}
                onReveal={revealAnswer}
              />
            ))}
          </div>
        )}

        {mcqData && mcqData.mcqs.length === 0 && !mcqLoading && (
          <p className="meta-text text-sm py-2">
            Insufficient event data to generate practice questions safely.
          </p>
        )}
      </section>

      {/* Related Events */}
      <section className="space-y-4 pt-4">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="headline text-xl flex items-center gap-2">
            <Sparkles className="w-4 h-4 accent-mark" />
            <span>Related Intelligence ({event.domain})</span>
          </h2>
          <span className="meta-text">Categorical Cluster</span>
        </div>

        {relatedEvents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {relatedEvents.slice(0, 3).map((relatedEvent) => (
              <EventCard key={relatedEvent.id} event={relatedEvent} compact />
            ))}
          </div>
        ) : (
          <p className="meta-text italic">
            No additional related events indexed in this category yet.
          </p>
        )}
      </section>
    </div>
  );
}

// ─── MCQ Card Component ─────────────────────────────────
interface MCQCardProps {
  mcq: MCQ;
  qIdx: number;
  selectedAnswer?: string;
  revealed: boolean;
  onSelect: (qIdx: number, letter: string) => void;
  onReveal: (qIdx: number) => void;
}

function MCQCard({ mcq, qIdx, selectedAnswer, revealed, onSelect, onReveal }: MCQCardProps) {
  return (
    <div className="editorial-panel p-4 space-y-3">
      <p className="text-sm font-semibold text-[var(--text-primary)]">
        Q{qIdx + 1}. {mcq.question}
      </p>
      <div className="grid grid-cols-1 gap-2">
        {mcq.options.map((opt, oIdx) => {
          const letter = String.fromCharCode(65 + oIdx);
          const isSelected = selectedAnswer === letter;
          const isCorrect = mcq.correct_answer === letter;
          let optClass = "editorial-card p-3 text-sm cursor-pointer transition-all text-left";

          if (revealed) {
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
              onClick={() => onSelect(qIdx, letter)}
              className={optClass}
            >
              <div className="flex items-center gap-2">
                {revealed && isCorrect && <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0" />}
                {revealed && isSelected && !isCorrect && <XCircle className="w-4 h-4 text-[var(--danger)] shrink-0" />}
                <span>{opt}</span>
              </div>
            </button>
          );
        })}
      </div>
      <div className="flex items-center gap-3">
        {selectedAnswer && !revealed && (
          <button
            type="button"
            onClick={() => onReveal(qIdx)}
            className="brand-button px-4 py-1.5 text-xs font-mono font-semibold rounded-lg"
          >
            Check Answer
          </button>
        )}
        {revealed && (
          <div className="text-sm body-copy bg-[var(--surface-muted)] p-3 rounded-lg w-full">
            <span className="font-semibold text-[var(--text-primary)]">Explanation: </span>
            {mcq.explanation}
          </div>
        )}
      </div>
    </div>
  );
}
