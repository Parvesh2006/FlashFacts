import React from "react";

export function SkeletonCard() {
  return (
    <div className="editorial-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="skeleton-shimmer h-5 w-24 rounded"></div>
        <div className="skeleton-shimmer h-4 w-16 rounded"></div>
      </div>
      <div className="skeleton-shimmer h-6 w-3/4 rounded"></div>
      <div className="space-y-2">
        <div className="skeleton-shimmer h-4 w-full rounded"></div>
        <div className="skeleton-shimmer h-4 w-5/6 rounded"></div>
      </div>
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="skeleton-shimmer h-4 w-28 rounded"></div>
        <div className="skeleton-shimmer h-4 w-20 rounded"></div>
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
