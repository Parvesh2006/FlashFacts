import React from "react";
import { Sparkles, Calendar } from "lucide-react";

export function WelcomeBanner() {
  const todayStr = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="editorial-card p-6 md:p-8 border-l-4 border-l-[var(--brand-primary)]">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-mono bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] border border-[var(--brand-primary-border)]">
            <Sparkles className="w-4 h-4" />
            <span>REAL-TIME CURRENT AFFAIRS INTELLIGENCE</span>
          </span>
          <span className="flex items-center gap-1.5 meta-text">
            <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            {todayStr}
          </span>
        </div>

        <h1 className="headline text-3xl md:text-4xl">
          Today&apos;s Current Affairs Overview
        </h1>

          <p className="body-copy text-base max-w-3xl">
          FlashFacts ingests, deduplicates, and categorizes breaking current affairs from permitted news feeds date-by-date across 13 major domains.
        </p>
      </div>
    </div>
  );
}
