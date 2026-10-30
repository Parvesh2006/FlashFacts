"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  BookOpen,
  FileText,
  Search,
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  Filter,
  Sparkles,
  ArrowRight,
  RotateCcw,
  AlertCircle,
  GraduationCap,
  Download,
  Eye,
  ExternalLink,
  ShieldCheck,
  HardDriveDownload,
  Trash2,
  Layers,
  Database,
} from "lucide-react";
import {
  fetchPYQs,
  fetchPYQFilters,
  togglePYQBookmark,
  fetchPYQPapers,
  fetchPYQPaperFilters,
  getPYQPaperPdfUrl,
  getPYQPaperDownloadUrl,
  PYQ,
  PYQFilters,
  PYQPaper,
  PYQPaperFilterOptions,
} from "@/services/pyqs";
import { saveQuestionToMistakeBook } from "@/services/revision";
import { BackButton } from "@/components/navigation/back-button";
import { PDFViewerModal } from "@/components/pyqs/pdf-viewer-modal";
import { EmptyBookmarksIllustration } from "@/components/illustrations/educational-illustrations";
import {
  getOfflinePapers,
  isPaperSavedOffline,
  savePaperToOffline,
  removeOfflinePaper,
  getStorageUsage,
  OfflinePaperRecord,
} from "@/lib/offline-pdf-storage";
import { useAuth } from "@/lib/auth";

function getCleanOption(opt: string): string {
  if (!opt) return "";
  const cleaned = opt.replace(/^[A-D][.)]\s*/i, "").trim();
  return cleaned || opt.trim();
}

function getCorrectOptionIndex(q: PYQ): number {
  if (!q.correct_answer || !q.options || q.options.length !== 4) return -1;
  const raw = q.correct_answer.trim();
  if (/^[A-D]$/i.test(raw)) {
    return raw.toUpperCase().charCodeAt(0) - 65;
  }
  const match = raw.match(/^([A-D])[.)]\s*/i);
  if (match) {
    return match[1].toUpperCase().charCodeAt(0) - 65;
  }
  const cleanAns = getCleanOption(raw).toLowerCase();
  for (let i = 0; i < q.options.length; i++) {
    const cleanOpt = getCleanOption(q.options[i]).toLowerCase();
    if (cleanOpt === cleanAns || q.options[i].trim().toLowerCase() === raw.toLowerCase()) {
      return i;
    }
  }
  return -1;
}

export default function PYQBankPage() {
  const { user } = useAuth();

  // Primary Tab Mode
  const [activeTab, setActiveTab] = useState<"papers" | "practice" | "offline">("papers");

  // ==========================================
  // STATE: PYQ Question Papers (PDFs)
  // ==========================================
  const [papers, setPapers] = useState<PYQPaper[]>([]);
  const [paperFilters, setPaperFilters] = useState<PYQPaperFilterOptions | null>(null);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [paperError, setPaperError] = useState<string | null>(null);

  // Filters for Papers
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedExamName, setSelectedExamName] = useState<string>("");
  const [selectedPaperYear, setSelectedPaperYear] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
  const [selectedAvailability, setSelectedAvailability] = useState<string>("");
  const [paperSearchQuery, setPaperSearchQuery] = useState<string>("");

  // PDF Viewer Modal State
  const [selectedPaperForViewing, setSelectedPaperForViewing] = useState<PYQPaper | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  // Offline Cached Papers State
  const [offlinePapers, setOfflinePapers] = useState<OfflinePaperRecord[]>([]);
  const [storageStats, setStorageStats] = useState<{ usedBytes: number; quotaBytes: number }>({
    usedBytes: 0,
    quotaBytes: 0,
  });
  const [offlineStatusMap, setOfflineStatusMap] = useState<Record<string, boolean>>({});

  // ==========================================
  // STATE: MCQ Practice Bank
  // ==========================================
  const [pyqs, setPyqs] = useState<PYQ[]>([]);
  const [practiceFilters, setPracticeFilters] = useState<PYQFilters | null>(null);
  const [loadingPractice, setLoadingPractice] = useState(true);
  const [selectedExam, setSelectedExam] = useState<string>("TNPSC Group 4");
  const [selectedPracticeYear, setSelectedPracticeYear] = useState<string>("");
  const [selectedPracticeType, setSelectedPracticeType] = useState<string>("all");
  const [practiceSearchQuery, setPracticeSearchQuery] = useState<string>("");

  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [revealedExplanations, setRevealedExplanations] = useState<Record<number, boolean>>({});
  const [bookmarkingId, setBookmarkingId] = useState<number | null>(null);
  const [savedToMistakeId, setSavedToMistakeId] = useState<number | null>(null);

  // Load Filters & Initial Data
  useEffect(() => {
    fetchPYQPaperFilters()
      .then(setPaperFilters)
      .catch((err) => console.error("Failed to fetch paper filters", err));

    fetchPYQFilters()
      .then(setPracticeFilters)
      .catch((err) => console.error("Failed to fetch practice filters", err));

    refreshOfflinePapers();
  }, []);

  const refreshOfflinePapers = async () => {
    try {
      const records = await getOfflinePapers();
      setOfflinePapers(records);
      const map: Record<string, boolean> = {};
      records.forEach((r) => {
        map[r.id] = true;
      });
      setOfflineStatusMap(map);
      const usage = await getStorageUsage();
      setStorageStats(usage);
    } catch {
      // ignore
    }
  };

  // Load Papers when filters change
  useEffect(() => {
    setLoadingPapers(true);
    setPaperError(null);
    fetchPYQPapers({
      category: selectedCategory || undefined,
      exam_name: selectedExamName || undefined,
      year: selectedPaperYear ? parseInt(selectedPaperYear, 10) : undefined,
      subject: selectedSubject || undefined,
      language: selectedLanguage || undefined,
      availability: selectedAvailability || undefined,
      q: paperSearchQuery || undefined,
      limit: 50,
    })
      .then((res) => {
        setPapers(res.items);
      })
      .catch((err) => {
        console.error("Failed to load papers", err);
        setPaperError("Unable to retrieve question papers from archive.");
      })
      .finally(() => setLoadingPapers(false));
  }, [
    selectedCategory,
    selectedExamName,
    selectedPaperYear,
    selectedSubject,
    selectedLanguage,
    selectedAvailability,
    paperSearchQuery,
  ]);

  // Load Practice MCQs when filters change
  useEffect(() => {
    if (activeTab === "practice") {
      setLoadingPractice(true);
      fetchPYQs({
        exam_name: selectedExam || undefined,
        year: selectedPracticeYear ? parseInt(selectedPracticeYear, 10) : undefined,
        type: selectedPracticeType === "all" ? undefined : selectedPracticeType,
        q: practiceSearchQuery || undefined,
        limit: 100,
      })
        .then(setPyqs)
        .catch((err) => console.error("Failed to load practice questions", err))
        .finally(() => setLoadingPractice(false));
    }
  }, [activeTab, selectedExam, selectedPracticeYear, selectedPracticeType, practiceSearchQuery]);

  const handleOpenViewer = (paper: PYQPaper) => {
    setSelectedPaperForViewing(paper);
    setIsViewerOpen(true);
  };

  const handleToggleOfflineSave = async (paper: PYQPaper) => {
    const isSaved = offlineStatusMap[paper.id];
    if (isSaved) {
      await removeOfflinePaper(paper.id);
    } else {
      try {
        const res = await fetch(getPYQPaperPdfUrl(paper.id));
        if (!res.ok) throw new Error("Failed to download PDF stream");
        const blob = await res.blob();
        await savePaperToOffline(paper, blob);
      } catch (err) {
        console.error("Offline save error", err);
        alert("Failed to save paper for offline use.");
        return;
      }
    }
    refreshOfflinePapers();
  };

  const handleAnswerSelect = (pyqId: number, optionLetter: string) => {
    setSelectedAnswers((prev) => ({ ...prev, [pyqId]: optionLetter }));
  };

  const handleToggleBookmark = async (pyqId: number) => {
    setBookmarkingId(pyqId);
    try {
      const res = await togglePYQBookmark(pyqId);
      setPyqs((prev) =>
        prev.map((q) => (q.id === pyqId ? { ...q, is_bookmarked: res.bookmarked } : q))
      );
    } catch (err) {
      console.error("Failed to toggle bookmark", err);
    } finally {
      setBookmarkingId(null);
    }
  };

  const handleSaveToMistake = async (pyq: PYQ, selectedLetter: string) => {
    setSavedToMistakeId(pyq.id);
    try {
      await saveQuestionToMistakeBook({
        question_text: pyq.question_text,
        subject: pyq.subject || pyq.exam_name,
        options: pyq.options,
        correct_answer: pyq.correct_answer,
        selected_answer: selectedLetter,
        explanation: pyq.explanation,
        exam_name: pyq.exam_name,
      });
      setTimeout(() => setSavedToMistakeId(null), 1500);
    } catch (err) {
      console.error("Failed to save to mistake book", err);
      setSavedToMistakeId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-7">
      <BackButton fallbackHref="/exams" />

      {/* Header */}
      <div className="border-b pb-5">
        <div className="eyebrow flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4" />
          <span>Authentic Competitive Examination Archives</span>
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="headline text-3xl md:text-4xl">Previous Year Questions (PYQs)</h1>
            <p className="body-copy text-base mt-2 max-w-3xl">
              Access genuine examination question paper PDFs directly from official authorities
              (TNPSC, UPSC, SSC, RRB), or practice past questions interactively with instant solutions.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="soft-badge px-2.5 py-1 text-emerald-600 bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Official Provenance</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Tab Switcher */}
      <div className="flex border-b border-[var(--border)] font-mono text-xs">
        <button
          onClick={() => setActiveTab("papers")}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-semibold transition-colors ${
            activeTab === "papers"
              ? "border-[var(--brand-primary)] text-[var(--brand-primary)] bg-[var(--surface)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Question Papers (Official PDFs)</span>
          <span className="soft-badge px-1.5 py-0.2 text-[10px] ml-1">{papers.length}</span>
        </button>

        <button
          onClick={() => setActiveTab("practice")}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-semibold transition-colors ${
            activeTab === "practice"
              ? "border-[var(--brand-primary)] text-[var(--brand-primary)] bg-[var(--surface)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>MCQ Practice Bank</span>
        </button>

        <button
          onClick={() => setActiveTab("offline")}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-semibold transition-colors ${
            activeTab === "offline"
              ? "border-[var(--brand-primary)] text-[var(--brand-primary)] bg-[var(--surface)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <HardDriveDownload className="w-4 h-4" />
          <span>Offline Library</span>
          {offlinePapers.length > 0 && (
            <span className="soft-badge px-1.5 py-0.2 text-[10px] bg-emerald-500/10 text-emerald-600 font-bold ml-1">
              {offlinePapers.length}
            </span>
          )}
        </button>
      </div>

      {/* =========================================================================
          TAB 1: OFFICIAL QUESTION PAPERS (PDF ARCHIVE)
         ========================================================================= */}
      {activeTab === "papers" && (
        <div className="space-y-6">
          {/* Category Tabs & Filter Toolbar */}
          <div className="editorial-card p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3">
              <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
                <span className="text-[var(--text-secondary)] mr-2 font-bold uppercase text-[10px]">
                  Board:
                </span>
                <button
                  onClick={() => setSelectedCategory("")}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                    selectedCategory === ""
                      ? "bg-[var(--brand-primary)] text-white"
                      : "bg-[var(--surface-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  All Boards
                </button>
                {paperFilters?.categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                      selectedCategory === cat
                        ? "bg-[var(--brand-primary)] text-white"
                        : "bg-[var(--surface-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Keyword Search */}
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                <input
                  type="text"
                  placeholder="Search papers, code, subject..."
                  value={paperSearchQuery}
                  onChange={(e) => setPaperSearchQuery(e.target.value)}
                  className="control-input w-full pl-8 pr-3 py-1.5 text-xs font-mono"
                />
              </div>
            </div>

            {/* Dynamic Multi-Attribute Filter Toolbar: Exam, Year, Subject, Language, Availability */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-mono text-xs pt-1">
              <div>
                <label className="block text-[var(--text-secondary)] text-[10px] uppercase font-bold mb-1">
                  1. Exam
                </label>
                <select
                  value={selectedExamName}
                  onChange={(e) => setSelectedExamName(e.target.value)}
                  className="control-input w-full py-1.5 px-2 text-xs font-mono"
                >
                  <option value="">All Examinations</option>
                  {paperFilters?.exams.map((ex) => (
                    <option key={ex} value={ex}>
                      {ex}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] text-[10px] uppercase font-bold mb-1">
                  2. Year
                </label>
                <select
                  value={selectedPaperYear}
                  onChange={(e) => setSelectedPaperYear(e.target.value)}
                  className="control-input w-full py-1.5 px-2 text-xs font-mono"
                >
                  <option value="">All Years</option>
                  {paperFilters?.years.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] text-[10px] uppercase font-bold mb-1">
                  3. Subject
                </label>
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="control-input w-full py-1.5 px-2 text-xs font-mono"
                >
                  <option value="">All Subjects</option>
                  {paperFilters?.subjects.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] text-[10px] uppercase font-bold mb-1">
                  4. Language
                </label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="control-input w-full py-1.5 px-2 text-xs font-mono"
                >
                  <option value="">All Languages</option>
                  {paperFilters?.languages.map((l) => (
                    <option key={l} value={l}>
                      {l.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] text-[10px] uppercase font-bold mb-1">
                  5. PDF Availability
                </label>
                <select
                  value={selectedAvailability}
                  onChange={(e) => setSelectedAvailability(e.target.value)}
                  className="control-input w-full py-1.5 px-2 text-xs font-mono"
                >
                  <option value="">All Papers</option>
                  <option value="available">Verified Local PDF</option>
                  <option value="source_link_only">Official Archive Link</option>
                  <option value="external_pdf">Verified External PDF</option>
                  <option value="unavailable">PDF Currently Unavailable</option>
                </select>
              </div>
            </div>

            {(selectedCategory ||
              selectedExamName ||
              selectedPaperYear ||
              selectedSubject ||
              selectedLanguage ||
              selectedAvailability ||
              paperSearchQuery) && (
              <div className="flex justify-end pt-1">
                <button
                  onClick={() => {
                    setSelectedCategory("");
                    setSelectedExamName("");
                    setSelectedPaperYear("");
                    setSelectedSubject("");
                    setSelectedLanguage("");
                    setSelectedAvailability("");
                    setPaperSearchQuery("");
                  }}
                  className="text-[11px] text-[var(--brand-primary)] hover:underline flex items-center gap-1 font-mono"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset All Filters</span>
                </button>
              </div>
            )}
          </div>

          {/* Paper Cards Grid */}
          {loadingPapers ? (
            <div className="editorial-card p-16 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[var(--brand-primary)]" />
              <p className="font-mono text-xs text-[var(--text-secondary)]">
                Fetching authentic question paper records...
              </p>
            </div>
          ) : papers.length === 0 ? (
            <div className="editorial-card p-12 text-center space-y-3 font-mono text-xs">
              <FileText className="w-10 h-10 mx-auto text-[var(--text-secondary)]" />
              <h3 className="text-base font-bold text-[var(--text-primary)]">No Papers Found</h3>
              <p className="text-[var(--text-secondary)] max-w-md mx-auto">
                No archived papers matched your current filter criteria. Try expanding your year or board selection.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {papers.map((p) => {
                const isSaved = offlineStatusMap[p.id];
                const isLocal = p.has_local_file && p.availability_status === "available";
                const isExternalPdf = p.availability_status === "external_pdf" && Boolean(p.pdf_url);
                const isUnavailable = p.availability_status === "unavailable";

                let statusBadgeText = "Official Archive Link";
                let statusBadgeClass = "text-sky-600";
                let StatusIcon = ExternalLink;

                if (p.verification_status !== "verified_official") {
                  statusBadgeText = "Unverified Source";
                  statusBadgeClass = "text-amber-600";
                  StatusIcon = AlertCircle;
                } else if (isLocal) {
                  statusBadgeText = "Verified Official Local PDF";
                  statusBadgeClass = "text-emerald-600";
                  StatusIcon = ShieldCheck;
                } else if (isExternalPdf) {
                  statusBadgeText = "Verified Official External PDF";
                  statusBadgeClass = "text-emerald-600";
                  StatusIcon = ShieldCheck;
                } else if (isUnavailable) {
                  statusBadgeText = "PDF Currently Unavailable";
                  statusBadgeClass = "text-rose-600";
                  StatusIcon = AlertCircle;
                }

                return (
                  <div
                    key={p.id}
                    className="editorial-card p-5 space-y-4 flex flex-col justify-between hover:border-[var(--brand-primary)] transition-colors"
                  >
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className="soft-badge px-2 py-0.5 font-bold text-[var(--brand-primary)] uppercase">
                            {p.exam_category}
                          </span>
                          <span className="soft-badge px-2 py-0.5">{p.year}</span>
                          <span className="soft-badge px-2 py-0.5 uppercase">{p.language}</span>
                        </div>
                        <span
                          className={`font-semibold flex items-center gap-1 text-[10px] ${statusBadgeClass}`}
                          title={`Verification Status: ${statusBadgeText}`}
                        >
                          <StatusIcon className="w-3.5 h-3.5" />
                          <span>{statusBadgeText}</span>
                        </span>
                      </div>

                      <h3 className="headline text-base font-bold text-[var(--text-primary)] line-clamp-2">
                        {p.title}
                      </h3>

                      <p className="text-xs text-[var(--text-secondary)] line-clamp-2">
                        {p.subject}
                      </p>

                      <div className="editorial-panel p-2.5 text-[11px] font-mono text-[var(--text-secondary)] space-y-1">
                        <div className="truncate">
                          <strong>Authority:</strong> {p.authority}
                        </div>
                        {p.shift_session && (
                          <div className="truncate">
                            <strong>Session:</strong> {p.shift_session}
                          </div>
                        )}
                        <div className="flex items-center justify-between text-[10px]">
                          <span>
                            Code: <strong>{p.paper_code || "OFFICIAL"}</strong>
                          </span>
                          {isLocal && p.file_size_bytes ? (
                            <span className="text-emerald-600 font-semibold">
                              {p.file_size_bytes > 1024 * 1024
                                ? `${(p.file_size_bytes / (1024 * 1024)).toFixed(2)} MB (Local PDF)`
                                : `${(p.file_size_bytes / 1024).toFixed(1)} KB (Local PDF)`}
                            </span>
                          ) : isExternalPdf && p.file_size_bytes ? (
                            <span className="text-emerald-600 font-semibold">{(p.file_size_bytes / 1024 / 1024).toFixed(1)} MB (Official Host)</span>
                          ) : isUnavailable ? (
                            <span className="text-rose-500 italic">Check in Progress</span>
                          ) : (
                            <span className="text-[var(--text-muted)] italic">Official Commission Archive</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="pt-2 border-t flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
                      {isLocal ? (
                        <>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleOpenViewer(p)}
                              className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>View PDF</span>
                            </button>

                            <a
                              href={getPYQPaperDownloadUrl(p.id)}
                              download
                              className="btn btn-secondary px-3 py-1.5 flex items-center gap-1.5"
                              title="Download PDF file"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Download</span>
                            </a>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleToggleOfflineSave(p)}
                              className={`p-1.5 rounded-lg border transition-colors ${
                                isSaved
                                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600"
                                  : "border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                              }`}
                              title={isSaved ? "Saved for offline study" : "Save for offline study"}
                            >
                              {isSaved ? (
                                <CheckCircle2 className="w-4 h-4" />
                              ) : (
                                <HardDriveDownload className="w-4 h-4" />
                              )}
                            </button>

                            <a
                              href={p.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--brand-primary)] transition-colors"
                              title="View Official Portal Source"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          </div>
                        </>
                      ) : isExternalPdf ? (
                        <>
                          <div className="flex items-center gap-2">
                            <a
                              href={p.pdf_url!}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
                              title="Open verified direct official question booklet from commission portal"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>View Official PDF</span>
                            </a>

                            <button
                              onClick={() => handleOpenViewer(p)}
                              className="btn btn-secondary px-2.5 py-1.5 flex items-center gap-1.5"
                              title="View Document Provenance and Live Verification Details"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Provenance</span>
                            </button>
                          </div>

                          <a
                            href={p.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--brand-primary)] transition-colors"
                            title="Open Official Commission Master Archive Portal"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </>
                      ) : isUnavailable ? (
                        <>
                          <div className="flex items-center gap-2">
                            <span
                              className="btn px-2.5 py-1.5 flex items-center gap-1.5 opacity-80 cursor-default bg-rose-500/10 text-rose-600 border border-rose-500/20 text-xs"
                              title="The official paper cannot be hosted locally because it was released via candidate-only login objection tracking"
                            >
                              <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                              <span>PDF Currently Unavailable</span>
                            </span>

                            <a
                              href={p.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn btn-secondary px-2.5 py-1.5 flex items-center gap-1.5"
                              title="Open Official Commission Portal"
                            >
                              <ExternalLink className="w-3.5 h-3.5 text-[var(--brand-primary)]" />
                              <span className="hidden sm:inline">Official Source</span>
                            </a>

                            <button
                              onClick={() => handleOpenViewer(p)}
                              className="btn btn-secondary px-2.5 py-1.5 flex items-center gap-1.5"
                              title="View Provenance Details"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Details</span>
                            </button>
                          </div>

                          <div className="text-[10px] text-[var(--text-muted)] font-mono">
                            CBT Response Portal Only
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex items-center gap-2">
                            <a
                              href={p.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5"
                              title="Open Official Commission Question Paper & Answer Key Portal"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Open Official Archive</span>
                            </a>

                            <button
                              onClick={() => handleOpenViewer(p)}
                              className="btn btn-secondary px-2.5 py-1.5 flex items-center gap-1.5"
                              title="View Document Details and Provenance"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Provenance</span>
                            </button>
                          </div>

                          <div className="text-[10px] text-[var(--text-muted)] font-mono">
                            Archive link verified
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: MCQ PRACTICE BANK (Interactive Questions)
         ========================================================================= */}
      {activeTab === "practice" && (
        <div className="space-y-6">
          <div className="editorial-card p-4 space-y-3 font-mono text-xs">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={selectedExam}
                  onChange={(e) => setSelectedExam(e.target.value)}
                  className="control-input py-1.5 px-3 text-xs font-mono"
                >
                  {practiceFilters?.exams.map((ex) => (
                    <option key={ex} value={ex}>
                      {ex}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedPracticeYear}
                  onChange={(e) => setSelectedPracticeYear(e.target.value)}
                  className="control-input py-1.5 px-3 text-xs font-mono"
                >
                  <option value="">All Years</option>
                  {practiceFilters?.years.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                <input
                  type="text"
                  placeholder="Search questions..."
                  value={practiceSearchQuery}
                  onChange={(e) => setPracticeSearchQuery(e.target.value)}
                  className="control-input w-full pl-8 pr-3 py-1.5 text-xs font-mono"
                />
              </div>
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[var(--border)]">
              <span className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-semibold mr-1">
                Category:
              </span>
              {[
                { id: "all", label: "All Questions" },
                { id: "verified_pyq", label: "Verified PYQs" },
                { id: "syllabus_practice", label: "Syllabus Practice" },
              ].map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setSelectedPracticeType(cat.id)}
                  className={`px-3 py-1 text-xs font-mono rounded-lg transition-all border ${
                    selectedPracticeType === cat.id
                      ? "bg-[var(--brand-primary)] text-white border-[var(--brand-primary)] font-semibold shadow-sm"
                      : "bg-[var(--surface-elevated)] text-[var(--text-secondary)] border-[var(--border)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {loadingPractice ? (
            <div className="editorial-card p-16 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[var(--brand-primary)]" />
              <p className="font-mono text-xs text-[var(--text-secondary)]">Loading practice questions...</p>
            </div>
          ) : (
            <div className="space-y-5">
              {pyqs.map((q, idx) => {
                // Graceful fallback for invalid/unverified questions
                if (q.quality_status === "invalid" || !q.options || q.options.length !== 4) {
                  return (
                    <div
                      key={q.id}
                      className="editorial-card p-5 border border-dashed border-amber-500/30 bg-amber-500/5 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="soft-badge px-2 py-0.5 font-bold text-amber-600 bg-amber-500/10">
                          Q{idx + 1} &bull; Unavailable
                        </span>
                        <span className="text-[var(--text-secondary)]">{q.exam_name}</span>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] font-mono">
                        Question unavailable for practice pending review.
                      </p>
                    </div>
                  );
                }

                const userAns = selectedAnswers[q.id];
                const isRevealed = revealedExplanations[q.id];
                const correctIdx = getCorrectOptionIndex(q);
                const correctLetter = correctIdx >= 0 ? String.fromCharCode(65 + correctIdx) : q.correct_answer;
                const isCorrect = userAns ? userAns === correctLetter : null;

                return (
                  <div key={q.id} className="editorial-card p-6 space-y-4">
                    <div className="flex items-center justify-between gap-2 font-mono text-xs border-b pb-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="soft-badge px-2 py-0.5 font-bold text-[var(--brand-primary)]">
                          Q{idx + 1}
                        </span>
                        <span className="font-semibold">{q.exam_name}</span>
                        <span>&bull;</span>
                        <span>{q.year}</span>
                        {q.subject && (
                          <>
                            <span>&bull;</span>
                            <span className="text-[var(--text-secondary)]">{q.subject}</span>
                          </>
                        )}
                        {q.question_type === "verified_pyq" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                            Verified PYQ
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-600 border border-blue-500/20">
                            Syllabus Practice
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleToggleBookmark(q.id)}
                        disabled={bookmarkingId === q.id}
                        className="text-[var(--text-secondary)] hover:text-[var(--brand-primary)] transition-colors p-1"
                        title={q.is_bookmarked ? "Remove Bookmark" : "Bookmark Question"}
                      >
                        {q.is_bookmarked ? (
                          <BookmarkCheck className="w-4 h-4 text-[var(--brand-primary)]" />
                        ) : (
                          <Bookmark className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    <p className="text-sm font-semibold leading-relaxed text-[var(--text-primary)]">
                      {q.question_text}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono text-xs">
                      {q.options.map((opt, optIdx) => {
                        const letter = String.fromCharCode(65 + optIdx);
                        const cleanOpt = getCleanOption(opt);
                        const isSelected = userAns === letter;
                        const isThisCorrect = correctIdx === optIdx;

                        let optClass = "border-[var(--border)] hover:bg-[var(--surface-elevated)]";
                        if (userAns) {
                          if (isThisCorrect) {
                            optClass = "border-emerald-500 bg-emerald-500/10 text-emerald-600 font-bold";
                          } else if (isSelected && !isThisCorrect) {
                            optClass = "border-rose-500 bg-rose-500/10 text-rose-600";
                          }
                        }

                        return (
                          <button
                            key={optIdx}
                            onClick={() => handleAnswerSelect(q.id, letter)}
                            className={`p-3 rounded-xl border text-left transition-colors flex items-start gap-2.5 ${optClass}`}
                          >
                            <span className="font-bold opacity-80">{letter}.</span>
                            <span className="flex-1 leading-snug">{cleanOpt}</span>
                          </button>
                        );
                      })}
                    </div>

                    {userAns && (
                      <div className="pt-2 flex flex-wrap items-center justify-between gap-3 font-mono text-xs border-t">
                        <div className="flex items-center gap-2">
                          {isCorrect ? (
                            <span className="text-emerald-600 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-4 h-4" /> Correct Answer!
                            </span>
                          ) : (
                            <span className="text-rose-600 font-bold flex items-center gap-1">
                              <XCircle className="w-4 h-4" /> Incorrect. Correct is {correctLetter}
                              {correctIdx >= 0 && q.options[correctIdx] && (
                                <span className="font-normal text-[var(--text-secondary)]">
                                  : {getCleanOption(q.options[correctIdx])}
                                </span>
                              )}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {!isCorrect && (
                            <button
                              onClick={() => handleSaveToMistake(q, userAns)}
                              className="text-[11px] px-2.5 py-1 rounded-lg border border-rose-500/30 text-rose-600 hover:bg-rose-500/10 transition-colors"
                            >
                              {savedToMistakeId === q.id ? "Logged in Mistake Book!" : "Add to Mistake Book"}
                            </button>
                          )}

                          <button
                            onClick={() =>
                              setRevealedExplanations((prev) => ({
                                ...prev,
                                [q.id]: !prev[q.id],
                              }))
                            }
                            className="btn btn-secondary px-3 py-1 text-[11px]"
                          >
                            {isRevealed ? "Hide Explanation" : "View Explanation"}
                          </button>
                        </div>
                      </div>
                    )}

                    {isRevealed && q.explanation && (
                      <div className="p-3.5 rounded-xl bg-[var(--surface-elevated)] border text-xs leading-relaxed text-[var(--text-secondary)] font-mono">
                        <strong>Explanation: </strong> {q.explanation}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: OFFLINE LIBRARY (Browser IndexedDB Storage)
         ========================================================================= */}
      {activeTab === "offline" && (
        <div className="space-y-6">
          <div className="editorial-card p-5 space-y-3 font-mono text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[var(--brand-primary)]" />
                <span className="font-bold text-[var(--text-primary)]">Local Offline Storage</span>
              </div>
              <span className="text-[var(--text-secondary)]">
                {offlinePapers.length} Papers Saved Offline
              </span>
            </div>
            <p className="body-copy text-xs">
              These question papers are stored persistently inside your browser storage (IndexedDB).
              You can reopen, review, and study them anytime even when completely disconnected from the internet.
            </p>
          </div>

          {offlinePapers.length === 0 ? (
            <div className="editorial-card p-12 text-center space-y-4 font-mono text-xs border border-[var(--border)] bg-[var(--surface)] shadow-xs">
              <EmptyBookmarksIllustration size={100} className="mx-auto" />
              <h3 className="text-base font-bold text-[var(--text-primary)]">No Offline Papers Saved</h3>
              <p className="text-[var(--text-secondary)] max-w-md mx-auto">
                Click the "Save Offline" button on any verified paper in the Question Papers tab to cache it locally on this device.
              </p>
              <button
                onClick={() => setActiveTab("papers")}
                className="button-base button-primary px-4 py-2 mt-2 font-semibold shadow-xs"
              >
                Browse Question Papers
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {offlinePapers.map((record) => {
                const p = record.paper;
                return (
                  <div
                    key={record.id}
                    className="editorial-card p-5 space-y-3 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2 font-mono text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className="soft-badge px-2 py-0.5 font-bold text-[var(--brand-primary)]">
                            {p.exam_category}
                          </span>
                          <span className="soft-badge px-2 py-0.5">{p.year}</span>
                        </div>
                        <span className="text-emerald-600 font-semibold text-[10px] flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Offline Cached</span>
                        </span>
                      </div>

                      <h4 className="font-bold text-sm text-[var(--text-primary)]">{p.title}</h4>
                      <p className="text-xs text-[var(--text-secondary)]">{p.subject}</p>
                      <div className="text-[11px] font-mono text-[var(--text-secondary)]">
                        Saved: {new Date(record.savedAt).toLocaleDateString()} &bull;{" "}
                        {(record.sizeBytes / 1024).toFixed(1)} KB
                      </div>
                    </div>

                    <div className="pt-2 border-t flex items-center justify-between gap-2 font-mono text-xs">
                      <button
                        onClick={() => handleOpenViewer(p)}
                        className="btn btn-primary px-3 py-1.5 flex items-center gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Open Offline</span>
                      </button>

                      <button
                        onClick={async () => {
                          await removeOfflinePaper(record.id);
                          refreshOfflinePapers();
                        }}
                        className="btn btn-secondary px-2.5 py-1.5 text-rose-500 hover:text-rose-600"
                        title="Delete from local cache"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* PDF Viewer Dialog */}
      <PDFViewerModal
        paper={selectedPaperForViewing}
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
        onOfflineStatusChange={refreshOfflinePapers}
      />
    </div>
  );
}
