import React from "react";
import { Layers, Rss, ShieldCheck, Activity } from "lucide-react";

interface StatCardsProps {
  totalEvents: number;
  domainCount: number;
  sourceCount: number;
}

export function StatCards({ totalEvents, domainCount, sourceCount }: StatCardsProps) {
  const stats = [
    {
      label: "Total Events Indexed",
      value: totalEvents.toLocaleString(),
      icon: Activity,
      color: "text-[var(--brand-primary)]",
      bgColor: "bg-[var(--brand-primary-soft)]",
      borderColor: "border-[var(--brand-primary-border)]",
      description: "Deduplicated real-world stories",
    },
    {
      label: "Domain Categories",
      value: domainCount,
      icon: Layers,
      color: "text-[var(--accent)]",
      bgColor: "bg-[var(--accent-soft)]",
      borderColor: "border-[var(--accent-border)]",
      description: "Classified for exam syllabus",
    },
    {
      label: "Permitted Sources",
      value: sourceCount,
      icon: Rss,
      color: "text-[var(--success)]",
      bgColor: "bg-[var(--success-soft)]",
      borderColor: "border-[color-mix(in_srgb,var(--success)_35%,var(--border))]",
      description: "Verified national & TN feeds",
    },
    {
      label: "Intelligence Engine",
      value: "Live",
      icon: ShieldCheck,
      color: "text-[var(--brand-primary)]",
      bgColor: "bg-[var(--brand-primary-soft)]",
      borderColor: "border-[var(--brand-primary-border)]",
      description: "FastAPI + PG active",
      isBadge: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <div
            key={i}
            className="editorial-card p-4 md:p-5 flex flex-col justify-between hover:border-[var(--border-strong)] transition-all"
          >
            <div className="flex items-center justify-between gap-3 mb-2">
              <span className="text-xs font-mono font-medium text-[var(--text-muted)] uppercase tracking-wider">
                {stat.label}
              </span>
              <div className={`p-2 rounded-lg ${stat.bgColor} ${stat.color} border ${stat.borderColor}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="flex items-baseline gap-2">
              {stat.isBadge ? (
                <div className="flex items-center gap-1.5 py-1 text-base font-bold text-[var(--success)] font-mono">
                  <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
                  <span>100% Operational</span>
                </div>
              ) : (
                <div className="text-2xl font-bold font-mono text-[var(--text-primary)]">
                  {stat.value}
                </div>
              )}
            </div>

            <div className="text-[11px] text-[var(--text-muted)] font-mono mt-1">
              {stat.description}
            </div>
          </div>
        );
      })}
    </div>
  );
}
