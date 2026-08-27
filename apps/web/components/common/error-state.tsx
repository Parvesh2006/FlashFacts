import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Failed to load current affairs intelligence",
  message = "Could not connect to the backend server. Please verify NEXT_PUBLIC_API_URL and ensure FastAPI is running.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="editorial-card p-8 text-center flex flex-col items-center justify-center border-[color-mix(in_srgb,var(--danger)_28%,var(--border))] bg-[var(--danger-soft)] my-4">
      <div className="w-12 h-12 rounded-full bg-[var(--surface)] border flex items-center justify-center text-[var(--danger)] mb-4">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="headline text-lg mb-1">{title}</h3>
      <p className="meta-text max-w-lg mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="control inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-semibold"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
}
