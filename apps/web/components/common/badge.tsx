import React from "react";
import { getDomainColor } from "@/lib/utils";

interface DomainBadgeProps {
  domain: string;
  className?: string;
}

export function DomainBadge({ domain, className = "" }: DomainBadgeProps) {
  const styles = getDomainColor(domain);
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-mono font-semibold tracking-normal border ${styles.bg} ${styles.text} ${styles.border} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5" style={{ backgroundColor: styles.accent }} />
      {domain}
    </span>
  );
}
