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
import {
  getOfflinePapers,
  isPaperSavedOffline,
  savePaperToOffline,
  removeOfflinePaper,
  getStorageUsage,
  OfflinePaperRecord,
} from "@/lib/offline-pdf-storage";
import { useAuth } from "@/lib/auth";

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
  const [selectedPaperYear, setSelectedPaperYear] = useState<string>("");
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
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
      year: selectedPaperYear ? parseInt(selectedPaperYear, 10) : undefined,
      language: selectedLanguage || undefined,
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
  }, [selectedCategory, selectedPaperYear, selectedLanguage, paperSearchQuery]);

  // Load Practice MCQs when filters change
  useEffect(() => {
    if (activeTab === "practice") {
      setLoadingPractice(true);
      fetchPYQs({
        exam_name: selectedExam || undefined,
        year: selectedPracticeYear ? parseInt(selectedPracticeYear, 10) : undefined,
        q: practiceSearchQuery || undefined,
        limit: 100,
      })
        .then(setPyqs)
        .catch((err) => console.error("Failed to load practice questions", err))
        .finally(() => setLoadingPractice(false));
    }
  }, [activeTab, selectedExam, selectedPracticeYear, practiceSearchQuery]);

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

            {/* Sub-Filters: Year & Language */}
            <div className="flex flex-wrap items-center gap-4 font-mono text-xs">
              <div className="flex items-center gap-2">
                <span className="text-[var(--text-secondary)] text-[11px]">Year:</span>
                <select
                  value={selectedPaperYear}
                  onChange={(e) => setSelectedPaperYear(e.target.value)}
                  className="control-input py-1 px-2 text-xs font-mono"
                >
                  <option value="">All Years</option>
                  {paperFilters?.years.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[var(--text-secondary)] text-[11px]">Language:</span>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="control-input py-1 px-2 text-xs font-mono"
                >
                  <option value="">All Languages</option>
                  {paperFilters?.languages.map((l) => (
                    <option key={l} value={l}>
                      {l.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {(selectedCategory || selectedPaperYear || selectedLanguage || paperSearchQuery) && (
                <button
                  onClick={() => {
                    setSelectedCategory("");
                    setSelectedPaperYear("");
                    setSelectedLanguage("");
                    setPaperSearchQuery("");
                  }}
                  className="text-[11px] text-[var(--brand-primary)] hover:underline flex items-center gap-1 ml-auto"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset Filters</span>
                </button>
              )}
            </div>
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
                        <span className="text-emerald-600 font-semibold flex items-center gap-1 text-[10px]">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Official</span>
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
                          {p.file_size_bytes && (
                            <span>{(p.file_size_bytes / 1024).toFixed(1)} KB</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="pt-2 border-t flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
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
          <div className="editorial-card p-4 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
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

          {loadingPractice ? (
            <div className="editorial-card p-16 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[var(--brand-primary)]" />
              <p className="font-mono text-xs text-[var(--text-secondary)]">Loading practice questions...</p>
            </div>
          ) : (
            <div className="space-y-5">
              {pyqs.map((q, idx) => {
                const userAns = selectedAnswers[q.id];
                const isRevealed = revealedExplanations[q.id];
                const isCorrect = userAns ? q.correct_answer.startsWith(userAns) : null;

                return (
                  <div key={q.id} className="editorial-card p-6 space-y-4">
                    <div className="flex items-center justify-between gap-2 font-mono text-xs border-b pb-3">
                      <div className="flex items-center gap-2">
                        <span className="soft-badge px-2 py-0.5 font-bold text-[var(--brand-primary)]">
                          Q{idx + 1}
                        </span>
                        <span>{q.exam_name}</span>
                        <span>&bull;</span>
                        <span>{q.year}</span>
                        {q.subject && (
                          <>
                            <span>&bull;</span>
                            <span className="text-[var(--text-secondary)]">{q.subject}</span>
                          </>
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
                      {q.options.map((opt) => {
                        const optLetter = opt.charAt(0);
                        const isSelected = userAns === optLetter;
                        const isThisCorrect = q.correct_answer.startsWith(optLetter);

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
                            key={opt}
                            onClick={() => handleAnswerSelect(q.id, optLetter)}
                            className={`p-3 rounded-xl border text-left transition-colors flex items-start gap-2 ${optClass}`}
                          >
                            <span className="font-bold">{optLetter}.</span>
                            <span>{opt.substring(opt.indexOf(".") + 1).trim()}</span>
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
                              <XCircle className="w-4 h-4" /> Incorrect. Correct is {q.correct_answer.charAt(0)}
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
            <div className="editorial-card p-12 text-center space-y-3 font-mono text-xs">
              <HardDriveDownload className="w-10 h-10 mx-auto text-[var(--text-secondary)]" />
              <h3 className="text-base font-bold text-[var(--text-primary)]">No Offline Papers Saved</h3>
              <p className="text-[var(--text-secondary)] max-w-md mx-auto">
                Click the "Save Offline" button on any paper card in the Question Papers tab to cache it locally on this device.
              </p>
              <button
                onClick={() => setActiveTab("papers")}
                className="btn btn-primary px-4 py-2 mt-2"
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
