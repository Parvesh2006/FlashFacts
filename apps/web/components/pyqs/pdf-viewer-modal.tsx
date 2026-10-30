"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Download,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  HardDriveDownload,
  Loader2,
  AlertCircle,
  FileText,
  Maximize2,
  RotateCcw,
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
  const [liveObjectUrl, setLiveObjectUrl] = useState<string | null>(null);
  const [loadingPdf, setLoadingPdf] = useState(true);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const canUseLocalPdf = Boolean(
    paper &&
    paper.verification_status === "verified_official" &&
    paper.availability_status === "available" &&
    paper.has_local_file === true
  );

  const canDownload = Boolean(
    canUseLocalPdf && paper?.redistribution_status === "official_open_access"
  );

  const canSaveOffline = Boolean(
    canUseLocalPdf && paper?.redistribution_status === "official_open_access"
  );

  useEffect(() => {
    let isCancelled = false;

    // Reset and cleanup previous object URLs
    if (offlineObjectUrl) {
      URL.revokeObjectURL(offlineObjectUrl);
      setOfflineObjectUrl(null);
    }
    if (liveObjectUrl) {
      URL.revokeObjectURL(liveObjectUrl);
      setLiveObjectUrl(null);
    }

    if (!paper || !isOpen) {
      setLoadingPdf(false);
      setPdfError(null);
      return;
    }

    setLoadingPdf(true);
    setPdfError(null);

    async function loadDocument() {
      if (!paper) return;

      // 1. Check if paper exists in offline IndexedDB cache
      try {
        const saved = await isPaperSavedOffline(paper.id);
        if (!isCancelled) setIsSavedOffline(saved);

        if (saved) {
          const blob = await getOfflinePaperBlob(paper.id);
          if (blob && !isCancelled) {
            const url = URL.createObjectURL(blob);
            setOfflineObjectUrl(url);
            setLoadingPdf(false);
            return;
          }
        }
      } catch (err) {
        console.error("Offline lookup error:", err);
      }

      // 2. If genuine local PDF is available, fetch via authenticated stream
      if (canUseLocalPdf) {
        try {
          const token =
            typeof window !== "undefined"
              ? localStorage.getItem("flashfacts_auth_token")
              : null;
          const headers: HeadersInit = token
            ? { Authorization: `Bearer ${token}` }
            : {};

          const res = await fetch(getPYQPaperPdfUrl(paper.id), {
            headers,
          });

          if (isCancelled) return;

          if (!res.ok) {
            if (res.status === 401) {
              setPdfError("Your authentication session has expired. Please sign in again.");
            } else if (res.status === 403) {
              setPdfError("Access to view this question paper is restricted.");
            } else if (res.status === 404) {
              setPdfError("This verified paper is not currently available in the local archive.");
            } else if (res.status === 503) {
              setPdfError("The official commission document is temporarily unreachable.");
            } else {
              setPdfError(`Unable to stream question paper (HTTP ${res.status}).`);
            }
            setLoadingPdf(false);
            return;
          }

          const blob = await res.blob();
          const signature = await blob.slice(0, 5).text();
          if (signature !== "%PDF-") {
            setPdfError("The received document could not be verified as a valid PDF.");
            setLoadingPdf(false);
            return;
          }

          const url = URL.createObjectURL(blob);
          if (!isCancelled) {
            setLiveObjectUrl(url);
            setLoadingPdf(false);
          } else {
            URL.revokeObjectURL(url);
          }
        } catch (err: any) {
          if (!isCancelled) {
            console.error("PDF stream error:", err);
            setPdfError(err.message || "Failed to stream question paper from archive.");
            setLoadingPdf(false);
          }
        }
      } else {
        setLoadingPdf(false);
      }
    }

    loadDocument();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      isCancelled = true;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [paper?.id, isOpen, canUseLocalPdf]);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (offlineObjectUrl) URL.revokeObjectURL(offlineObjectUrl);
      if (liveObjectUrl) URL.revokeObjectURL(liveObjectUrl);
    };
  }, [offlineObjectUrl, liveObjectUrl]);

  if (!isOpen || !paper) return null;

  const displayPdfUrl = offlineObjectUrl || liveObjectUrl || getPYQPaperPdfUrl(paper.id);
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
      if (!canSaveOffline) {
        alert("This paper is not eligible for offline local redistribution.");
        return;
      }
      setSavingOffline(true);
      try {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("flashfacts_auth_token")
            : null;
        const headers: HeadersInit = token
          ? { Authorization: `Bearer ${token}` }
          : {};

        const res = await fetch(getPYQPaperPdfUrl(paper.id), { headers });
        if (!res.ok) throw new Error("Failed to fetch PDF for offline storage");
        const blob = await res.blob();
        const signature = await blob.slice(0, 5).text();
        if (signature !== "%PDF-") {
          throw new Error("The server did not return a valid PDF document.");
        }
        await savePaperToOffline(paper, blob);
        setIsSavedOffline(true);
        const objUrl = URL.createObjectURL(blob);
        setOfflineObjectUrl(objUrl);
        onOfflineStatusChange?.();
      } catch (err: any) {
        console.error("Failed to save paper offline", err);
        alert(err.message || "Unable to save PDF offline. Check your network or device storage.");
      } finally {
        setSavingOffline(false);
      }
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in"
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
                <span>
                  {paper.verification_status === "verified_official"
                    ? "Verified Official"
                    : "Unverified"}
                </span>
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
            {/* Open in full browser tab */}
            {canUseLocalPdf && (displayPdfUrl || paper) && (
              <a
                href={displayPdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary px-2.5 py-1.5 flex items-center gap-1.5"
                title="Open PDF in a full browser tab"
              >
                <Maximize2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Open in Tab</span>
              </a>
            )}

            {/* Offline save toggle */}
            {(canSaveOffline || isSavedOffline) && (
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
            )}

            {/* Download button - strictly triggers attachment download */}
            {canDownload && (
              <a
                href={downloadUrl}
                download
                className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5"
                title="Download official PDF to device"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Download</span>
              </a>
            )}

            {/* Official Source Link */}
            <a
              href={paper.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary px-2.5 py-1.5"
              title="Open Official Commission Source"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            {/* Close Button */}
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
        <div className="flex-1 bg-zinc-950 relative flex items-center justify-center overflow-hidden">
          {canUseLocalPdf && loadingPdf && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[var(--surface)] text-[var(--text-secondary)] font-mono text-xs z-10">
              <Loader2 className="w-7 h-7 animate-spin text-[var(--brand-primary)]" />
              <span>Streaming authentic examination question paper...</span>
            </div>
          )}

          {paper.availability_status === "external_pdf" ? (
            <div className="p-8 text-center space-y-4 max-w-xl bg-[var(--surface)] rounded-2xl border border-[var(--border)] m-4 font-mono">
              <ShieldCheck className="w-10 h-10 mx-auto text-emerald-500" />
              <h3 className="font-bold text-base text-[var(--text-primary)]">
                Verified Official External PDF
              </h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                This genuine examination question booklet is hosted directly on the official {paper.authority} server. FlashFacts has verified its HTTP status (200 OK), PDF header signature, and document structure.
              </p>
              <div className="p-3 bg-[var(--surface-muted)] rounded-xl text-[11px] text-left space-y-1">
                <div className="truncate"><strong>Official PDF:</strong> <span className="text-emerald-600">{paper.pdf_url}</span></div>
                <div className="truncate"><strong>Master Archive:</strong> <span className="text-[var(--text-muted)]">{paper.source_url}</span></div>
                {paper.file_size_bytes && (
                  <div>
                    <strong>Verified Size:</strong>{" "}
                    {paper.file_size_bytes > 1024 * 1024
                      ? `${(paper.file_size_bytes / (1024 * 1024)).toFixed(2)} MB`
                      : `${(paper.file_size_bytes / 1024).toFixed(1)} KB`}
                  </div>
                )}
                {paper.last_verified_at && (
                  <div className="text-[10px] text-[var(--text-muted)]"><strong>Last Verified:</strong> {new Date(paper.last_verified_at).toLocaleString()}</div>
                )}
              </div>
              <div className="pt-2 flex flex-wrap justify-center gap-3 text-xs">
                <a
                  href={paper.pdf_url!}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary px-4 py-2 inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Official PDF Document</span>
                </a>
                <a
                  href={paper.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary px-4 py-2 inline-flex items-center gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Official Archive Listing</span>
                </a>
              </div>
            </div>
          ) : paper.availability_status === "unavailable" ? (
            <div className="p-8 text-center space-y-4 max-w-lg bg-[var(--surface)] rounded-2xl border border-[var(--border)] m-4 font-mono">
              <AlertCircle className="w-10 h-10 mx-auto text-rose-500" />
              <h3 className="font-bold text-base text-[var(--text-primary)]">
                PDF Currently Unavailable
              </h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                The authentic question paper PDF for <strong>{paper.exam_name} {paper.year}</strong> ({paper.shift_session || paper.subject}) is not hosted as an open public master document on the official {paper.authority} portal. This examination was conducted via computer-based test (CBT) and distributed exclusively via candidate login response sheets during time-limited challenge windows.
              </p>
              <div className="p-3 bg-[var(--surface-muted)] rounded-xl text-[11px] text-left space-y-1">
                <div className="truncate"><strong>Authority:</strong> {paper.authority}</div>
                <div className="truncate"><strong>Official Portal:</strong> <span className="text-[var(--brand-primary)]">{paper.source_url}</span></div>
                <div className="text-[10px] text-[var(--text-muted)]">
                  FlashFacts strictly indexes verified provenance and refuses to substitute fabricated or unverified synthetic PDFs.
                </div>
              </div>
              <div className="pt-2 flex justify-center gap-3 text-xs">
                <a
                  href={paper.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary px-4 py-2 inline-flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Official Commission Portal</span>
                </a>
              </div>
            </div>
          ) : !canUseLocalPdf ? (
            <div className="p-8 text-center space-y-4 max-w-lg bg-[var(--surface)] rounded-2xl border border-[var(--border)] m-4 font-mono">
              <ShieldCheck className="w-9 h-9 mx-auto text-sky-500" />
              <h3 className="font-bold text-sm text-[var(--text-primary)]">
                Official Commission Portal Document
              </h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                This question paper is archived directly on the official {paper.authority} portal. FlashFacts indexes verified official provenance while strictly respecting redistribution boundaries. No synthetic mockups or unverified files are substituted.
              </p>
              <div className="pt-2">
                <a
                  href={paper.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary px-4 py-2 text-xs inline-flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Official Commission Archive</span>
                </a>
              </div>
            </div>
          ) : pdfError ? (
            <div className="p-8 text-center space-y-4 max-w-md bg-[var(--surface)] rounded-2xl border border-[var(--border)] m-4 font-mono">
              <AlertCircle className="w-8 h-8 mx-auto text-rose-500" />
              <h3 className="font-bold text-sm text-[var(--text-primary)]">Unable to Render PDF Preview</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                {pdfError}
              </p>
              <div className="flex flex-wrap justify-center gap-3 pt-2 text-xs">
                {canDownload && (
                  <a href={downloadUrl} download className="btn btn-primary px-4 py-2">
                    Download PDF
                  </a>
                )}
                <a href={paper.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary px-4 py-2">
                  Official Source
                </a>
              </div>
            </div>
          ) : (
            <iframe
              src={`${displayPdfUrl}#toolbar=1&navpanes=0`}
              className="w-full h-full border-0"
              title={paper.title}
              onLoad={() => setLoadingPdf(false)}
            />
          )}
        </div>

        {/* Footer Meta & Attribution */}
        <div className="px-5 py-2.5 border-t border-[var(--border)] bg-[var(--surface)] flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[var(--text-secondary)]">
          <div className="flex items-center gap-3">
            {canUseLocalPdf && paper.checksum_sha256 ? (
              <span>SHA-256: {paper.checksum_sha256.slice(0, 16)}...</span>
            ) : paper.availability_status === "external_pdf" ? (
              <span>Verified External Document &bull; {paper.authority}</span>
            ) : (
              <span>Source: {paper.authority}</span>
            )}
            {canUseLocalPdf && paper.file_size_bytes ? (
              <span>
                Size:{" "}
                {paper.file_size_bytes > 1024 * 1024
                  ? `${(paper.file_size_bytes / (1024 * 1024)).toFixed(2)} MB (Local PDF)`
                  : `${(paper.file_size_bytes / 1024).toFixed(1)} KB (Local PDF)`}
              </span>
            ) : paper.file_size_bytes ? (
              <span>
                Size:{" "}
                {paper.file_size_bytes > 1024 * 1024
                  ? `${(paper.file_size_bytes / (1024 * 1024)).toFixed(2)} MB (Official Host)`
                  : `${(paper.file_size_bytes / 1024).toFixed(1)} KB (Official Host)`}
              </span>
            ) : (
              <span>Mode: Official Portal Provenance</span>
            )}
          </div>
          <div>
            <span>
              Status:{" "}
              {paper.availability_status === "external_pdf"
                ? "Verified Official External PDF"
                : paper.availability_status === "source_link_only"
                ? "Official Archive Link"
                : paper.availability_status === "unavailable"
                ? "PDF Currently Unavailable"
                : paper.availability_status}{" "}
              &bull; FlashFacts Archive
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
