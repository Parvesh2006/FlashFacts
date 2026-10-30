import React from "react";
import { AlertCircle, RefreshCw, Terminal } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  details?: string;
}

export function ErrorState({
  title = "Intelligence Feed Unavailable",
  message = "Could not establish a connection to the FlashFacts backend API at http://localhost:8000. Please ensure the service container is active.",
  onRetry,
  details,
}: ErrorStateProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div className="editorial-card page-enter p-8 md:p-10 text-center flex flex-col items-center justify-center border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] bg-[var(--danger-soft)] my-6">
      <div className="w-14 h-14 rounded-2xl bg-[var(--surface)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] flex items-center justify-center text-[var(--danger)] mb-4 shadow-xs">
        <AlertCircle className="w-7 h-7" />
      </div>
      <span className="badge-editorial text-[10px] text-[var(--danger)] border-[color-mix(in_srgb,var(--danger)_35%,var(--border))] mb-2">
        Service Notice
      </span>
      <h3 className="headline text-lg font-bold text-[var(--text-primary)] mb-2">
        {title}
      </h3>
      <p className="body-copy text-sm max-w-lg mb-6 text-[var(--text-secondary)] leading-relaxed">
        {message}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3 mb-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="button-base button-primary px-4 py-2 text-xs font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Request
          </button>
        )}
        {details && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="button-base button-secondary px-3 py-2 text-xs font-mono"
          >
            <Terminal className="w-3 h-3" />
            {showDetails ? "Hide Diagnostics" : "View Diagnostics"}
          </button>
        )}
      </div>

      {showDetails && details && (
        <pre className="mt-4 p-3 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-left font-mono text-[11px] text-[var(--text-muted)] max-w-xl overflow-x-auto whitespace-pre-wrap">
          {details}
        </pre>
      )}
    </div>
  );
}
