import React from "react";
import Link from "next/link";
import { ArrowUpRight, Layers } from "lucide-react";
import { DomainStat } from "@/types/domain";
import { getDomainColor } from "@/lib/utils";

interface DomainCardProps {
  domainStat: DomainStat;
}

export function DomainCard({ domainStat }: DomainCardProps) {
  const styles = getDomainColor(domainStat.domain);

  return (
    <Link
      href={`/explore?domain=${encodeURIComponent(domainStat.domain)}`}
      className="group block"
    >
      <div className="editorial-card editorial-card-hover p-4 flex flex-col justify-between h-full">
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full shadow-sm"
              style={{ backgroundColor: styles.accent }}
            />
            <h4 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
              {domainStat.domain}
            </h4>
          </div>
          <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand-primary)] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>

        <div className="flex items-baseline justify-between pt-2 border-t text-xs font-mono">
          <span className="text-[var(--text-secondary)] flex items-center gap-1">
            <Layers className="w-3 h-3 text-[var(--text-muted)]" />
            Events
          </span>
          <span className="text-sm font-bold text-[var(--text-primary)]">
            {domainStat.count}
          </span>
        </div>
      </div>
    </Link>
  );
}
