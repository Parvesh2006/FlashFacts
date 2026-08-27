import React from "react";

export function LoadingSpinner({ label = "Loading FlashFacts intelligence..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-[var(--brand-primary-border)]"></div>
        <div className="absolute inset-0 rounded-full border-2 border-[var(--brand-primary)] border-t-transparent animate-spin"></div>
      </div>
      <p className="eyebrow">{label}</p>
    </div>
  );
}
