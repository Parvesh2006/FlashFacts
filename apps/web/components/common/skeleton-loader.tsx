import React from "react";

export function SkeletonCard() {
  return (
    <div className="editorial-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="skeleton-shimmer h-5 w-24 rounded-full"></div>
        <div className="skeleton-shimmer h-4 w-16 rounded-sm"></div>
      </div>
      <div className="space-y-2">
        <div className="skeleton-shimmer h-6 w-5/6 rounded"></div>
        <div className="skeleton-shimmer h-4 w-3/4 rounded"></div>
      </div>
      <div className="space-y-2 pt-1">
        <div className="skeleton-shimmer h-3.5 w-full rounded"></div>
        <div className="skeleton-shimmer h-3.5 w-11/12 rounded"></div>
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-[var(--border)]">
        <div className="skeleton-shimmer h-4 w-28 rounded"></div>
        <div className="skeleton-shimmer h-4 w-20 rounded"></div>
      </div>
    </div>
  );
}

export function SkeletonLeadCard() {
  return (
    <div className="editorial-card p-6 md:p-8 space-y-5">
      <div className="flex items-center justify-between">
        <div className="skeleton-shimmer h-6 w-32 rounded-full"></div>
        <div className="skeleton-shimmer h-4 w-24 rounded"></div>
      </div>
      <div className="skeleton-shimmer h-8 md:h-10 w-4/5 rounded"></div>
      <div className="space-y-2.5">
        <div className="skeleton-shimmer h-4 w-full rounded"></div>
        <div className="skeleton-shimmer h-4 w-11/12 rounded"></div>
        <div className="skeleton-shimmer h-4 w-4/5 rounded"></div>
      </div>
      <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
        <div className="skeleton-shimmer h-5 w-32 rounded"></div>
        <div className="skeleton-shimmer h-9 w-28 rounded-lg"></div>
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
