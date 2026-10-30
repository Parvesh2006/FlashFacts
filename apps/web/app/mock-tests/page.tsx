"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  GraduationCap,
  Clock,
  Award,
  Play,
  Plus,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  BookOpen,
  ArrowRight,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import {
  fetchMockTests,
  fetchAttemptHistory,
  createMockTest,
  fetchEligibleCounts,
  MockTestSummary,
  MockTestAttemptSummary,
  ExamBankStats,
} from "@/services/mock-tests";
import { BackButton } from "@/components/navigation/back-button";
import { EmptyState } from "@/components/common/empty-state";
import { CompletedTestIllustration } from "@/components/illustrations/educational-illustrations";

export default function MockTestsPage() {
  const router = useRouter();
  const [tests, setTests] = useState<MockTestSummary[]>([]);
  const [attempts, setAttempts] = useState<MockTestAttemptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"available" | "history">("available");

  // Bank stats and modal states
  const [bankStats, setBankStats] = useState<Record<string, ExamBankStats> | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [generatingForId, setGeneratingForId] = useState<string | null>(null);
  const [selectedExam, setSelectedExam] = useState("TNPSC Group 4");
  const [selectedQuestions, setSelectedQuestions] = useState(10);
  const [selectedTime, setSelectedTime] = useState(15);
  const [selectedDifficulty, setSelectedDifficulty] = useState("medium");
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [testData, attemptData, statsData] = await Promise.all([
        fetchMockTests(),
        fetchAttemptHistory().catch(() => []),
        fetchEligibleCounts().catch(() => null),
      ]);

      // Stable template identity deduplication (belt-and-suspenders guarantee)
      const seenSignatures = new Set<string>();
      const distinctTests: MockTestSummary[] = [];
      for (const t of testData) {
        const sig =
          t.template_key ||
          `${t.exam_name}|${t.domain || t.subject || "all"}|${t.total_questions}|${t.time_limit_minutes}|${t.difficulty}|${Number(t.negative_marking || 0).toFixed(2)}`.toLowerCase();
        if (!seenSignatures.has(sig)) {
          seenSignatures.add(sig);
          distinctTests.push(t);
        }
      }

      setTests(distinctTests);
      setAttempts(attemptData);
      setBankStats(statsData);
    } catch (err: any) {
      console.error("Failed to load mock tests", err);
      setLoadError("Failed to load mock test modules. Please check connectivity and retry.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionsChange = (count: number) => {
    setSelectedQuestions(count);
    if (count <= 10) setSelectedTime(15);
    else if (count <= 25) setSelectedTime(30);
    else if (count <= 50) setSelectedTime(60);
    else setSelectedTime(120);
  };

  const handleStartFreshTest = async (testTemplate: MockTestSummary) => {
    setGeneratingForId(testTemplate.id);
    try {
      const newTest = await createMockTest({
        exam_name: testTemplate.exam_name,
        domain: testTemplate.domain,
        total_questions: testTemplate.total_questions,
        time_limit_minutes: testTemplate.time_limit_minutes,
        difficulty: testTemplate.difficulty,
        include_pyqs: true,
        include_events: true,
      });
      router.push(`/mock-tests/${newTest.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to generate new test session.");
    } finally {
      setGeneratingForId(null);
    }
  };

  const handleCreateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const newTest = await createMockTest({
        exam_name: selectedExam,
        total_questions: selectedQuestions,
        time_limit_minutes: selectedTime,
        difficulty: selectedDifficulty,
        include_pyqs: true,
        include_events: true,
      });
      setShowCreateModal(false);
      router.push(`/mock-tests/${newTest.id}`);
    } catch (err: any) {
      setCreateError(err.message || "Failed to create mock test. Please try again.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-7 max-w-6xl mx-auto page-enter">
      <BackButton fallbackHref="/exams" />

      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] pb-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
              EXAM SIMULATION CENTRE
            </span>
            <span className="text-xs text-[var(--text-muted)]">• Negative Marking Enabled</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
            Mock Test Centre
          </h1>
          <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-3xl leading-relaxed">
            Take timed full-length and sectional practice tests under authentic examination conditions.
            Powered by real commission PYQs, verified current-affairs MCQs, and strict server-side evaluation.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="button-base button-primary text-xs px-4 py-2.5 flex items-center gap-2 self-start md:self-auto font-semibold shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>Generate Custom Mock</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--border)] gap-6 text-xs font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab("available")}
          className={`pb-3 border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === "available"
              ? "border-[var(--accent)] text-[var(--accent)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <span>Available Tests</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--surface-muted)] text-[var(--text-secondary)] border border-[var(--border)]">
            {tests.length}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("history")}
          className={`pb-3 border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === "history"
              ? "border-[var(--accent)] text-[var(--accent)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <span>Attempt History</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--surface-muted)] text-[var(--text-secondary)] border border-[var(--border)]">
            {attempts.length}
          </span>
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="editorial-card p-12 flex flex-col items-center justify-center gap-3 border border-[var(--border)]">
          <Loader2 className="w-6 h-6 animate-spin text-[var(--accent)]" />
          <span className="text-xs font-medium text-[var(--text-secondary)]">Loading mock test modules...</span>
        </div>
      ) : loadError ? (
        <div className="editorial-card p-8 flex flex-col items-center justify-center gap-3 border border-red-200 bg-red-50/50 text-center">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <span className="text-xs font-medium text-red-700">{loadError}</span>
          <button
            type="button"
            onClick={loadData}
            className="button-base button-secondary text-xs px-3 py-1.5 font-semibold mt-1"
          >
            Retry
          </button>
        </div>
      ) : activeTab === "available" ? (
        tests.length === 0 ? (
          <EmptyState
            icon={<GraduationCap className="w-7 h-7 text-[var(--accent)]" />}
            title="No Ready Mock Tests Available"
            description="Configure a custom test session tailored to your target exam, difficulty level, and question volume."
            actionLabel="Generate Custom Test"
            onAction={() => setShowCreateModal(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {tests.map((test) => (
              <div
                key={test.id}
                className="editorial-card p-6 flex flex-col justify-between space-y-4 border border-[var(--border)] hover:border-[var(--text-muted)] transition-all shadow-xs"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="badge-editorial text-xs font-semibold text-[var(--accent)] border-[var(--accent)]">
                      {test.exam_name}
                    </span>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                      {test.difficulty}
                    </span>
                  </div>

                  <h3 className="headline text-lg font-bold text-[var(--text-primary)]">
                    {test.title || (test.domain ? `${test.domain} Sectional Drill` : `${test.exam_name} Practice Test`)}
                  </h3>

                  <div className="flex flex-wrap gap-3 text-xs text-[var(--text-secondary)]">
                    <span className="flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-[var(--accent)]" />
                      {test.total_questions} Questions
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-[var(--accent)]" />
                      {test.time_limit_minutes} Mins
                    </span>
                    {test.negative_marking > 0 && (
                      <span className="text-amber-700 font-medium flex items-center gap-1">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        -{test.negative_marking} Neg.
                      </span>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  disabled={generatingForId === test.id}
                  onClick={() => handleStartFreshTest(test)}
                  className="button-base button-primary text-xs py-2.5 px-4 flex items-center justify-center gap-2 w-full text-center font-semibold shadow-xs"
                >
                  {generatingForId === test.id ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Generating Fresh Session...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Start Practice Test</span>
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        )
      ) : attempts.length === 0 ? (
        <EmptyState
          illustration={<CompletedTestIllustration size={110} />}
          title="No Test Attempts Recorded"
          description="Your test submissions, accuracy metrics, scores, and question reviews will appear here automatically once you complete a test."
          actionLabel="Start a Practice Test"
          onAction={() => setActiveTab("available")}
        />
      ) : (
        <div className="space-y-4">
          {attempts.map((att) => (
            <div
              key={att.id}
              className="editorial-card p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-[var(--border)] shadow-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-base text-[var(--text-primary)]">
                    {att.exam_name}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">
                    • {new Date(att.submitted_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="text-xs text-[var(--text-secondary)] flex flex-wrap gap-4 pt-0.5">
                  <span>
                    Score: <strong className="text-[var(--text-primary)] font-bold">{att.score}</strong> / {att.total_questions}
                  </span>
                  <span>
                    Accuracy: <strong className="text-[var(--success)] font-bold">{att.accuracy}%</strong>
                  </span>
                  <span>
                    Answered: {att.total_answered} of {att.total_questions}
                  </span>
                </div>
              </div>

              <Link
                href={`/mock-tests/${att.test_id}/result/${att.id}`}
                className="button-base button-secondary text-xs px-4 py-2 flex items-center gap-1.5 self-end sm:self-auto font-semibold"
              >
                <span>Review Performance</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Create Custom Test Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="editorial-card max-w-md w-full p-6 space-y-5 shadow-xl border border-[var(--border)] bg-[var(--surface)]">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div>
                <span className="badge-editorial text-[10px] text-[var(--accent)] border-[var(--accent)] mb-1">
                  CONFIGURATOR
                </span>
                <h3 className="headline text-xl font-bold text-[var(--text-primary)]">
                  Generate Mock Test
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm p-1"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="p-3 rounded-lg bg-[var(--danger-soft)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] text-[var(--danger)] text-xs">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateTest} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                  Target Examination
                </label>
                <select
                  value={selectedExam}
                  onChange={(e) => {
                    const nextExam = e.target.value;
                    setSelectedExam(nextExam);
                    const stats = bankStats?.[nextExam];
                    if (stats && !stats.supported_lengths.includes(selectedQuestions)) {
                      handleQuestionsChange(stats.supported_lengths[0] || 10);
                    }
                  }}
                  className="w-full px-3 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                >
                  <option value="TNPSC Group 4">TNPSC Group 4 (Tamil Nadu)</option>
                  <option value="TNPSC Group 2">TNPSC Group 2 / 2A</option>
                  <option value="UPSC CSE">UPSC Civil Services (Prelims)</option>
                  <option value="SSC CGL">SSC CGL (Tier 1)</option>
                  <option value="RRB NTPC">RRB NTPC (CBT-1)</option>
                </select>
                {bankStats?.[selectedExam] && (
                  <p className="text-[11px] text-[var(--success)] font-medium mt-1 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Verified Question Bank: {bankStats[selectedExam].available_questions} questions available
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                    Question Count
                  </label>
                  <select
                    value={selectedQuestions}
                    onChange={(e) => handleQuestionsChange(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    <option value={10}>10 Questions (Quick)</option>
                    {(!bankStats?.[selectedExam] || bankStats[selectedExam].available_questions >= 25) && (
                      <option value={25}>25 Questions (Sectional)</option>
                    )}
                    {(!bankStats?.[selectedExam] || bankStats[selectedExam].available_questions >= 50) && (
                      <option value={50}>50 Questions (Half-Mock)</option>
                    )}
                    {(!bankStats?.[selectedExam] || bankStats[selectedExam].available_questions >= 100) && (
                      <option value={100}>100 Questions (Full Simulation)</option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                    Time Allowed
                  </label>
                  <select
                    value={selectedTime}
                    onChange={(e) => setSelectedTime(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    <option value={15}>15 Minutes</option>
                    <option value={30}>30 Minutes</option>
                    <option value={60}>60 Minutes</option>
                    <option value={90}>90 Minutes</option>
                    <option value={120}>120 Minutes (2h)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                  Difficulty Level
                </label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                >
                  <option value="easy">Easy — Core Syllabus & Foundational Facts</option>
                  <option value="medium">Medium — Standard Commission Exam Standard</option>
                  <option value="hard">Hard — Advanced Multi-Statement & Analytical</option>
                </select>
              </div>

              <div className="pt-3 border-t border-[var(--border)] flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="button-base button-ghost px-4 py-2 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="button-base button-primary px-5 py-2 text-xs font-semibold flex items-center gap-2"
                >
                  {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{creating ? "Generating..." : "Generate Test"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
