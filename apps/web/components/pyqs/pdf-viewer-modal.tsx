"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Download,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  HardDriveDownload,
  Trash2,
  Loader2,
  AlertCircle,
  FileText,
  Maximize2,
} from "lucide-react";
import { PYQPaper, getPYQPaperPdfUrl, getPYQPaperDownloadUrl } from "@/services/pyqs";
import {
  savePaperToOffline,
  isPaperSavedOffline,
  removeOfflinePaper,
  getOfflinePaperBlob,
} from "@/lib/offline-pdf-storage";

interface PDFViewerModalProps {
  paper: PYQPaper | null;
  isOpen: boolean;
  onClose: () => void;
  onOfflineStatusChange?: () => void;
}

export function PDFViewerModal({
  paper,
  isOpen,
  onClose,
  onOfflineStatusChange,
}: PDFViewerModalProps) {
  const [isSavedOffline, setIsSavedOffline] = useState(false);
  const [savingOffline, setSavingOffline] = useState(false);
  const [offlineObjectUrl, setOfflineObjectUrl] = useState<string | null>(null);
  const [loadingPdf, setLoadingPdf] = useState(true);
  const [pdfError, setPdfError] = useState<string | null>(null);

  useEffect(() => {
    if (!paper || !isOpen) {
      if (offlineObjectUrl) {
        URL.revokeObjectURL(offlineObjectUrl);
        setOfflineObjectUrl(null);
      }
      return;
    }

    setLoadingPdf(true);
    setPdfError(null);

    // Check if paper is saved in offline IndexedDB
    isPaperSavedOffline(paper.id).then(async (saved) => {
      setIsSavedOffline(saved);
      if (saved) {
        const blob = await getOfflinePaperBlob(paper.id);
        if (blob) {
          const url = URL.createObjectURL(blob);
          setOfflineObjectUrl(url);
        }
      }
    });

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [paper, isOpen]);

  if (!isOpen || !paper) return null;

  const pdfSourceUrl = offlineObjectUrl || getPYQPaperPdfUrl(paper.id);
  const downloadUrl = getPYQPaperDownloadUrl(paper.id);

  const handleToggleOffline = async () => {
    if (isSavedOffline) {
      setSavingOffline(true);
      try {
        await removeOfflinePaper(paper.id);
        setIsSavedOffline(false);
        if (offlineObjectUrl) {
          URL.revokeObjectURL(offlineObjectUrl);
          setOfflineObjectUrl(null);
        }
        onOfflineStatusChange?.();
      } catch (err) {
        console.error("Failed to remove offline paper", err);
      } finally {
        setSavingOffline(false);
      }
    } else {
      setSavingOffline(true);
      try {
        const res = await fetch(getPYQPaperPdfUrl(paper.id));
        if (!res.ok) throw new Error("Failed to fetch PDF for offline storage");
        const blob = await res.blob();
        await savePaperToOffline(paper, blob);
        setIsSavedOffline(true);
        const objUrl = URL.createObjectURL(blob);
        setOfflineObjectUrl(objUrl);
        onOfflineStatusChange?.();
      } catch (err) {
        console.error("Failed to save paper offline", err);
        alert("Unable to save PDF offline. Check your network or device storage.");
      } finally {
        setSavingOffline(false);
      }
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/75 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-5xl h-[92vh] bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-5 py-3.5 border-b border-[var(--border)] bg-[var(--surface-muted)]/70">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="soft-badge px-2 py-0.5 text-[10px] font-mono font-bold text-[var(--brand-primary)] uppercase">
                {paper.exam_category}
              </span>
              <span className="soft-badge px-2 py-0.5 text-[10px] font-mono">
                {paper.year}
              </span>
              <span className="soft-badge px-2 py-0.5 text-[10px] font-mono uppercase">
                {paper.language}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-600 font-semibold">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{paper.verification_status}</span>
              </span>
            </div>
            <h2 className="text-sm font-bold text-[var(--text-primary)] truncate font-mono">
              {paper.title}
            </h2>
            <div className="text-[11px] text-[var(--text-secondary)] font-mono truncate">
              {paper.authority} &bull; {paper.subject} {paper.paper_code ? `(${paper.paper_code})` : ""}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 self-end sm:self-center flex-shrink-0 font-mono text-xs">
            <button
              onClick={handleToggleOffline}
              disabled={savingOffline}
              className={`btn px-3 py-1.5 flex items-center gap-1.5 transition-colors ${
                isSavedOffline
                  ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 hover:bg-emerald-500/20"
                  : "btn-secondary text-[var(--text-primary)]"
              }`}
              title={isSavedOffline ? "Remove from offline storage" : "Save for offline study"}
            >
              {savingOffline ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : isSavedOffline ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Offline Ready</span>
                </>
              ) : (
                <>
                  <HardDriveDownload className="w-3.5 h-3.5" />
                  <span>Save Offline</span>
                </>
              )}
            </button>

            <a
              href={downloadUrl}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download</span>
            </a>

            <a
              href={paper.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary px-2.5 py-1.5"
              title="Open Official Source"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-muted)] transition-colors"
              aria-label="Close PDF viewer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Embedded PDF Viewer Viewport */}
        <div className="flex-1 bg-zinc-900 relative flex items-center justify-center overflow-hidden">
          {loadingPdf && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[var(--surface)] text-[var(--text-secondary)] font-mono text-xs z-10">
              <Loader2 className="w-7 h-7 animate-spin text-[var(--brand-primary)]" />
              <span>Streaming authentic examination question paper...</span>
            </div>
          )}

          {pdfError ? (
            <div className="p-8 text-center space-y-4 max-w-md bg-[var(--surface)] rounded-2xl border border-[var(--border)] m-4">
              <AlertCircle className="w-8 h-8 mx-auto text-rose-500" />
              <h3 className="font-bold text-sm text-[var(--text-primary)]">Preview Not Supported in Browser</h3>
              <p className="text-xs text-[var(--text-secondary)]">
                {pdfError}
              </p>
              <div className="flex justify-center gap-3">
                <a href={downloadUrl} className="btn btn-primary px-4 py-2 text-xs">
                  Download PDF
                </a>
                <a href={paper.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary px-4 py-2 text-xs">
                  Official Source
                </a>
              </div>
            </div>
          ) : (
            <iframe
              src={`${pdfSourceUrl}#toolbar=1&navpanes=0`}
              className="w-full h-full border-0"
              title={paper.title}
              onLoad={() => setLoadingPdf(false)}
              onError={() => {
                setLoadingPdf(false);
                setPdfError("This browser blocked inline PDF rendering. You can download or view it directly on the official source portal.");
              }}
            />
          )}
        </div>

        {/* Footer Meta & Attribution */}
        <div className="px-5 py-2.5 border-t border-[var(--border)] bg-[var(--surface)] flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[var(--text-secondary)]">
          <div className="flex items-center gap-3">
            <span>SHA-256: {paper.checksum_sha256 ? `${paper.checksum_sha256.slice(0, 16)}...` : "Verified"}</span>
            {paper.file_size_bytes && (
              <span>Size: {(paper.file_size_bytes / 1024).toFixed(1)} KB</span>
            )}
          </div>
          <div>
            <span>Redistribution: {paper.redistribution_status} &bull; FlashFacts Archive</span>
          </div>
        </div>
      </div>
    </div>
  );
}
