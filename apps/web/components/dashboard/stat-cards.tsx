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
      value: totalEvents,
      icon: Activity,
      color: "text-[var(--brand-primary)]",
      bgColor: "bg-[var(--brand-primary-soft)]",
      borderColor: "border-[var(--brand-primary-border)]",
    },
    {
      label: "Domain Categories",
      value: domainCount,
      icon: Layers,
      color: "text-[var(--accent)]",
      bgColor: "bg-[var(--accent-soft)]",
      borderColor: "border-[var(--accent-border)]",
    },
    {
      label: "Permitted Sources",
      value: sourceCount,
      icon: Rss,
      color: "text-[var(--success)]",
      bgColor: "bg-[var(--success-soft)]",
      borderColor: "border-[color-mix(in_srgb,var(--success)_35%,var(--border))]",
    },
    {
      label: "Engine Status",
      value: "100% Operational",
      icon: ShieldCheck,
      color: "text-[var(--warning)]",
      bgColor: "bg-[var(--warning-soft)]",
      borderColor: "border-[color-mix(in_srgb,var(--warning)_35%,var(--border))]",
      isText: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <div
            key={i}
            className="editorial-card p-4 flex items-center justify-between"
          >
            <div>
              <p className="meta-text uppercase font-semibold">
                {stat.label}
              </p>
              <p className={`mt-1 font-bold text-[var(--text-primary)] ${stat.isText ? "text-sm" : "text-2xl font-mono"}`}>
                {stat.value}
              </p>
            </div>
            <div className={`w-10 h-10 rounded-lg ${stat.bgColor} border ${stat.borderColor} flex items-center justify-center ${stat.color}`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
}
