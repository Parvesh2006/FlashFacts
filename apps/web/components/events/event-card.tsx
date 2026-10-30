import React from "react";
import Link from "next/link";
import {
  Calendar,
  ExternalLink,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  GraduationCap,
  MapPin,
} from "lucide-react";
import { Event } from "@/types/event";
import { DomainBadge } from "@/components/common/badge";
import { formatDate } from "@/lib/utils";

interface EventCardProps {
  event: Event;
  compact?: boolean;
  variant?: "standard" | "lead";
}

export function EventCard({ event, compact = false, variant = "standard" }: EventCardProps) {
  const confidencePercent = Math.round((event.confidence_score || 1.0) * 100);
  const examIntel = event.exam_intelligence;

  // Check if real event photo URL is available
  const hasValidPhoto =
    event.url &&
    (event.url.endsWith(".jpg") ||
      event.url.endsWith(".jpeg") ||
      event.url.endsWith(".png") ||
      event.url.endsWith(".webp"));

  // Prominent Lead Story Variant (Editorial Newspaper Style)
  if (variant === "lead") {
    return (
      <article className="editorial-card editorial-card-hover group/lead p-6 md:p-8 bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-strong)] flex flex-col justify-between transition-all shadow-xs">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--border)]">
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge-editorial text-xs font-mono font-bold text-[var(--brand-primary)] border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)]">
                LEAD STORY
              </span>
              <DomainBadge domain={event.domain || "Technology"} />
              {examIntel?.primary_state && (
                <span className="badge-editorial text-xs font-mono text-[var(--accent)] border-[var(--accent-border)] bg-[var(--accent-soft)] flex items-center gap-1 font-semibold">
                  <MapPin className="w-3 h-3" />
                  <span>{examIntel.primary_state}</span>
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)]">
              <Calendar className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span>{formatDate(event.event_date)}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {hasValidPhoto && (
              <div className="w-full h-56 sm:h-72 overflow-hidden rounded-xl border border-[var(--border)] relative bg-[var(--surface-muted)]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={event.url}
                  alt={event.title}
                  className="w-full h-full object-cover group-hover/lead:scale-102 transition-transform duration-300"
                  loading="lazy"
                />
                <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] bg-black/60 text-white font-mono backdrop-blur-xs">
                  {event.source}
                </span>
              </div>
            )}

            <div>
              <Link href={`/event/${event.id}`} className="block group">
                <h2 className="headline headline-lead text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
                  {event.title}
                </h2>
              </Link>

              <p className="body-copy text-base md:text-[1.0625rem] leading-relaxed text-[var(--text-secondary)] line-clamp-4 mt-3">
                {event.summary}
              </p>
            </div>
          </div>

          {examIntel && (
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-mono">
              <span className="px-2.5 py-1 rounded-md bg-[var(--surface-muted)] text-[var(--brand-primary)] border border-[var(--brand-primary-border)] font-semibold flex items-center gap-1.5">
                <GraduationCap className="w-3.5 h-3.5" />
                <span>{examIntel.geographic_level} Level</span>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-[var(--surface-muted)] text-[var(--warning)] border border-amber-200 font-semibold">
                Importance: {examIntel.exam_importance}
              </span>
              {event.syllabus_topic && (
                <span className="px-2.5 py-1 rounded-md bg-[var(--surface-muted)] text-[var(--text-secondary)] border border-[var(--border)]">
                  {event.syllabus_topic}
                </span>
              )}
            </div>
          )}
        </div>

        <div className="pt-5 mt-5 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-muted)]">
            <span>Source: <strong className="text-[var(--text-primary)]">{event.source || "News Registry"}</strong></span>
            <span className="flex items-center gap-1 text-[var(--success)]" title="Extraction Confidence">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{confidencePercent}% verified</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            {event.source_url && (
              <a
                href={event.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--brand-primary)] flex items-center gap-1 p-1.5 transition-colors"
                title="Open Original Source"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Original Source</span>
              </a>
            )}
            <Link
              href={`/event/${event.id}`}
              className="button-base button-primary px-4 py-2 text-xs font-semibold shadow-xs"
            >
              <span>Read Full Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </article>
    );
  }

  // Standard Modular Bento Grid Card (Warm White Editorial)
  return (
    <article className="editorial-card editorial-card-hover group/card p-5 flex flex-col justify-between h-full bg-[var(--surface)] border border-[var(--border)]">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <DomainBadge domain={event.domain || "Technology"} />
          <div className="flex items-center gap-1.5 meta-text text-[11px]">
            <Calendar className="w-3 h-3 text-[var(--accent)]" />
            <span>{formatDate(event.event_date)}</span>
          </div>
        </div>

        <p className="meta-text mb-2 truncate text-[11px]" title={event.source || undefined}>
          {event.source || "News Registry"}
        </p>

        {examIntel && (
          <div className="flex flex-wrap items-center gap-1.5 mb-2.5 text-[11px] font-mono">
            <span className="px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--brand-primary)] border border-[var(--brand-primary-border)] flex items-center gap-1 font-semibold text-[10px]">
              <GraduationCap className="w-3 h-3" />
              <span>{examIntel.geographic_level}</span>
            </span>
            <span className="px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--warning)] border border-amber-200 text-[10px]">
              {examIntel.exam_importance}
            </span>
            {examIntel.primary_state && (
              <span className="px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--accent)] border border-[var(--accent-border)] font-medium text-[10px]">
                {examIntel.primary_state}
              </span>
            )}
          </div>
        )}

        <Link href={`/event/${event.id}`} className="group block">
          <h3 className="headline headline-card text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors line-clamp-2 mb-2">
            {event.title}
          </h3>
        </Link>

        <p className={`body-copy-sm text-xs sm:text-[13px] ${compact ? "line-clamp-2" : "line-clamp-3"} mb-4 text-[var(--text-secondary)]`}>
          {event.summary}
        </p>
      </div>

      <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-3 font-mono text-[11px]">
          {typeof event.importance_score !== "undefined" && (
            <span className="flex items-center gap-1 text-[var(--warning)]" title="Importance Score">
              <Sparkles className="w-3 h-3" />
              <span>{event.importance_score}</span>
            </span>
          )}

          <span className="flex items-center gap-1 text-[var(--success)]" title="Extraction & Classification Confidence">
            <ShieldCheck className="w-3 h-3" />
            <span>{confidencePercent}%</span>
          </span>
        </div>

        <Link
          href={`/event/${event.id}`}
          className="text-xs font-semibold text-[var(--brand-primary)] hover:underline inline-flex items-center gap-1"
        >
          <span>Read Analysis</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </article>
  );
}
