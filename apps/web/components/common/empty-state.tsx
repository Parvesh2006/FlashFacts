import React from "react";
import { BookOpen, RefreshCw, ArrowRight } from "lucide-react";
import { EmptyBookmarksIllustration } from "@/components/illustrations/educational-illustrations";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  illustration?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  onRetry?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export function EmptyState({
  title = "No current affairs records found",
  description = "No items match your active filters or syllabus query. Check back shortly or reset your parameters to explore more.",
  icon,
  illustration,
  actionLabel,
  onAction,
  onRetry,
  secondaryActionLabel,
  onSecondaryAction,
}: EmptyStateProps) {
  return (
    <div className="editorial-card page-enter p-8 md:p-12 text-center flex flex-col items-center justify-center my-6 border border-dashed border-[var(--border)] bg-[var(--surface)] shadow-xs">
      {illustration ? (
        <div className="mb-4">{illustration}</div>
      ) : icon ? (
        <div className="relative mb-5">
          <div className="w-16 h-16 rounded-2xl bg-[var(--surface-muted)] border border-[var(--border)] flex items-center justify-center text-[var(--accent)] shadow-xs">
            {icon}
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[var(--surface)] border border-[var(--border)] flex items-center justify-center text-xs">
            ✨
          </div>
        </div>
      ) : (
        <div className="mb-4">
          <EmptyBookmarksIllustration size={100} />
        </div>
      )}

      <h3 className="headline text-xl font-bold tracking-tight mb-2 text-[var(--text-primary)]">
        {title}
      </h3>
      <p className="body-copy text-sm max-w-md mb-6 text-[var(--text-secondary)] leading-relaxed">
        {description}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="button-base button-secondary px-4 py-2 text-xs font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Feed</span>
          </button>
        )}
        {actionLabel && onAction && (
          <button
            onClick={onAction}
            className="button-base button-primary px-5 py-2 text-xs font-semibold"
          >
            <span>{actionLabel}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
        {secondaryActionLabel && onSecondaryAction && (
          <button
            onClick={onSecondaryAction}
            className="button-base button-ghost px-4 py-2 text-xs"
          >
            <span>{secondaryActionLabel}</span>
          </button>
        )}
      </div>
    </div>
  );
}
