"use client";

import React from "react";
import { Filter, RotateCcw, Calendar, Tag } from "lucide-react";
import { DomainStat } from "@/types/domain";

interface EventFiltersProps {
  domains: DomainStat[];
  selectedDomain?: string;
  selectedDate?: string;
  startDate?: string;
  endDate?: string;
  limit?: number;
  onDomainChange: (domain: string | undefined) => void;
  onDateChange: (date: string | undefined) => void;
  onDateRangeChange: (start: string | undefined, end: string | undefined) => void;
  onReset: () => void;
}

export function EventFilters({
  domains,
  selectedDomain,
  selectedDate,
  startDate,
  endDate,
  onDomainChange,
  onDateChange,
  onDateRangeChange,
  onReset,
}: EventFiltersProps) {
  const hasActiveFilters = Boolean(selectedDomain || selectedDate || startDate || endDate);

  return (
    <div className="editorial-card p-4 space-y-4 mb-6">
      <div className="flex items-center justify-between border-b pb-3">
        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[var(--text-primary)]">
          <Filter className="w-4 h-4 accent-mark" />
          <span>EVENT INTELLIGENCE FILTERS</span>
        </div>

        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 text-xs font-mono text-[var(--brand-primary)] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Filters</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        <div>
          <label className="block meta-text mb-1 flex items-center gap-1">
            <Tag className="w-3 h-3 accent-mark" />
            <span>Domain Category</span>
          </label>
          <select
            value={selectedDomain || ""}
            onChange={(e) => onDomainChange(e.target.value || undefined)}
            className="control-input w-full px-3 py-2 focus:outline-none focus:border-[var(--brand-primary)]"
          >
            <option value="">All Domains</option>
            {domains.map((d) => (
              <option key={d.domain} value={d.domain}>
                {d.domain} ({d.count})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block meta-text mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 accent-mark" />
            <span>Exact Event Date</span>
          </label>
          <input
            type="date"
            value={selectedDate || ""}
            onChange={(e) => onDateChange(e.target.value || undefined)}
            className="control-input w-full px-3 py-1.5 focus:outline-none focus:border-[var(--brand-primary)]"
          />
        </div>

        <div>
          <label className="block meta-text mb-1">From Date</label>
          <input
            type="date"
            value={startDate || ""}
            onChange={(e) => onDateRangeChange(e.target.value || undefined, endDate)}
            className="control-input w-full px-3 py-1.5 focus:outline-none focus:border-[var(--brand-primary)]"
          />
        </div>

        <div>
          <label className="block meta-text mb-1">To Date</label>
          <input
            type="date"
            value={endDate || ""}
            onChange={(e) => onDateRangeChange(startDate, e.target.value || undefined)}
            className="control-input w-full px-3 py-1.5 focus:outline-none focus:border-[var(--brand-primary)]"
          />
        </div>
      </div>
    </div>
  );
}
