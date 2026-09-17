import React from "react";
import Link from "next/link";
import { Calendar, ExternalLink, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { Event } from "@/types/event";
import { DomainBadge } from "@/components/common/badge";
import { formatDate } from "@/lib/utils";

interface EventCardProps {
  event: Event;
  compact?: boolean;
}

export function EventCard({ event, compact = false }: EventCardProps) {
  const confidencePercent = Math.round((event.confidence_score || 1.0) * 100);

  return (
    <div className="editorial-card editorial-card-hover group/card p-5 flex flex-col justify-between h-full">
      <div>
          <div className="flex items-center justify-between gap-2 mb-3">
          <DomainBadge domain={event.domain || "General"} />
          <div className="flex items-center gap-1.5 meta-text">
            <Calendar className="w-3.5 h-3.5 accent-mark" />
            <span>{formatDate(event.event_date)}</span>
          </div>

        <p className="meta-text mb-2 truncate" title={event.source || undefined}>
          {event.source || "Unknown source"}
        </p>
        </div>

        <Link href={`/event/${event.id}`} className="group">
          <h3 className="headline text-lg group-hover:text-[var(--brand-primary)] transition-colors line-clamp-2 mb-2">
            {event.title}
          </h3>
        </Link>

        <p className={`body-copy text-sm ${compact ? "line-clamp-2" : "line-clamp-3"} mb-4`}>
          {event.summary}
        </p>
      </div>

      <div className="pt-3 border-t flex items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-3 font-mono text-[11px]">
          {typeof event.importance_score !== "undefined" && (
            <span className="flex items-center gap-1 text-[var(--warning)]" title="Importance Score">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{event.importance_score}</span>
            </span>
          )}

          <span className="flex items-center gap-1 text-[var(--success)]" title="Extraction & Classification Confidence">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{confidencePercent}%</span>
          </span>

          {event.source_url && (
            <a
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--text-secondary)] hover:text-[var(--brand-primary)] transition-colors flex items-center gap-1"
              title="View Original Source"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="w-3 h-3" />
              <span className="hidden sm:inline">Source</span>
            </a>
          )}
        </div>

        {/* View Details Link */}
        <Link
          href={`/event/${event.id}`}
          className="inline-flex items-center gap-1 text-xs font-mono font-semibold text-[var(--brand-primary)] transition-colors"
        >
          <span>Details</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover/card:translate-x-0.5" />
        </Link>
      </div>
    </div>
  );
}
