import React from "react";
import { Inbox, RefreshCw } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export function EmptyState({
  title = "No current affairs have been indexed yet.",
  description = "Connect permitted sources or trigger feed ingestion to populate real-time current affairs events.",
  onRetry,
}: EmptyStateProps) {
  return (
    <div className="editorial-card page-enter p-10 text-center flex flex-col items-center justify-center my-4">
      <div className="w-14 h-14 rounded-full bg-[var(--surface-muted)] border flex items-center justify-center text-[var(--text-muted)] mb-4">
        <Inbox className="w-7 h-7" />
      </div>
      <h3 className="headline text-xl mb-2">{title}</h3>
      <p className="body-copy text-sm max-w-md mb-6">{description}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="button-base button-secondary px-4 py-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Data
        </button>
      )}
    </div>
  );
}
