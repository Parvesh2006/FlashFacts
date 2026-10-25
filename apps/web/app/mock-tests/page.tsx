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
  Calendar,
  Sparkles,
  RotateCcw,
  BookOpen,
} from "lucide-react";
import {
  fetchMockTests,
  fetchAttemptHistory,
  createMockTest,
  MockTestSummary,
  MockTestAttemptSummary,
} from "@/services/mock-tests";
import { BackButton } from "@/components/navigation/back-button";

export default function MockTestsPage() {
  const router = useRouter();
  const [tests, setTests] = useState<MockTestSummary[]>([]);
  const [attempts, setAttempts] = useState<MockTestAttemptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"available" | "history">("available");

  // Create test modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedExam, setSelectedExam] = useState("TNPSC Group 4");
  const [selectedQuestions, setSelectedQuestions] = useState(10);
  const [selectedTime, setSelectedTime] = useState(20);
  const [selectedDifficulty, setSelectedDifficulty] = useState("medium");
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [testData, attemptData] = await Promise.all([
        fetchMockTests(),
        fetchAttemptHistory().catch(() => []),
      ]);
      setTests(testData);
      setAttempts(attemptData);
    } catch (err) {
      console.error("Failed to load mock tests", err);
    } finally {
      setLoading(false);
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
    <div className="space-y-7 max-w-6xl mx-auto">
      <BackButton fallbackHref="/exams" />

      {/* Header */}
      <div className="border-b pb-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="eyebrow flex items-center gap-2 mb-2">
            <GraduationCap className="w-4 h-4" />
            <span>Interactive Exam Practice</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl">Mock Test Centre</h1>
          <p className="body-copy text-base mt-2 max-w-3xl">
            Take timed full-length and topic practice tests under actual examination conditions.
            All tests feature authentic PYQs, live current-affairs MCQs, server-side scoring, and negative marking.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="brand-button text-sm font-mono px-5 py-2.5 flex items-center gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Custom Test</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b gap-6 text-sm font-mono font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("available")}
          className={`pb-3 border-b-2 transition-all ${
            activeTab === "available"
              ? "border-[var(--brand-primary)] text-[var(--brand-primary)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          Available Tests ({tests.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("history")}
          className={`pb-3 border-b-2 transition-all ${
            activeTab === "history"
              ? "border-[var(--brand-primary)] text-[var(--brand-primary)]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          Attempt History ({attempts.length})
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="editorial-card p-12 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin accent-mark" />
          <span className="body-copy text-sm font-mono">Loading mock test modules...</span>
        </div>
      ) : activeTab === "available" ? (
        tests.length === 0 ? (
          <div className="editorial-card p-12 text-center space-y-4">
            <GraduationCap className="w-12 h-12 mx-auto text-[var(--text-secondary)] opacity-50" />
            <h3 className="headline text-lg">No ready tests available</h3>
            <p className="body-copy text-sm max-w-md mx-auto">
              Create a custom mock test tailored to your target exam and question count.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="brand-button text-xs font-mono px-4 py-2"
            >
              Generate Test Now
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {tests.map((test) => (
              <div
                key={test.id}
                className="editorial-card editorial-card-hover p-6 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="soft-badge px-2.5 py-1 text-xs font-mono font-semibold text-[var(--brand-primary)]">
                      {test.exam_name}
                    </span>
                    <span className="text-xs font-mono text-[var(--text-secondary)] capitalize">
                      {test.difficulty}
                    </span>
                  </div>

                  <h3 className="headline text-lg font-bold">
                    {test.domain ? `${test.domain} Mock Drill` : `${test.exam_name} Practice Test`}
                  </h3>

                  <div className="flex flex-wrap gap-3 text-xs font-mono text-[var(--text-secondary)]">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5" />
                      {test.total_questions} Questions
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {test.time_limit_minutes} Mins
                    </span>
                    {test.negative_marking > 0 && (
                      <span className="text-amber-500 font-medium">
                        -{test.negative_marking} Neg.
                      </span>
                    )}
                  </div>
                </div>

                <Link
                  href={`/mock-tests/${test.id}`}
                  className="brand-button text-xs font-mono py-2.5 px-4 flex items-center justify-center gap-2 w-full text-center"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Test</span>
                </Link>
              </div>
            ))}
          </div>
        )
      ) : (
        /* Attempt History Tab */
        attempts.length === 0 ? (
          <div className="editorial-card p-12 text-center space-y-3">
            <Clock className="w-10 h-10 mx-auto text-[var(--text-secondary)] opacity-50" />
            <h3 className="headline text-lg">No attempts recorded yet</h3>
            <p className="body-copy text-sm max-w-md mx-auto">
              Your test submissions, scores, and performance trends will appear here automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {attempts.map((att) => (
              <div
                key={att.id}
                className="editorial-card p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base text-[var(--text-primary)]">
                      {att.exam_name}
                    </span>
                    <span className="text-xs font-mono text-[var(--text-secondary)]">
                      • {new Date(att.submitted_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-[var(--text-secondary)] flex gap-4">
                    <span>
                      Score: <strong className="text-[var(--text-primary)]">{att.score}</strong>
                    </span>
                    <span>
                      Accuracy: <strong className="text-[var(--text-primary)]">{att.accuracy}%</strong>
                    </span>
                    <span>
                      Answered: {att.total_answered} of {att.total_questions}
                    </span>
                  </div>
                </div>

                <Link
                  href={`/mock-tests/${att.test_id}/result/${att.id}`}
                  className="brand-button text-xs font-mono px-4 py-2 flex items-center gap-1.5 self-end sm:self-auto"
                >
                  <span>Review Answers</span>
                </Link>
              </div>
            ))}
          </div>
        )
      )}

      {/* Create Custom Test Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="editorial-card max-w-md w-full p-6 space-y-5 shadow-2xl border-[var(--border-subtle)]">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="headline text-xl">Generate Custom Mock Test</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 text-xs font-mono">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateTest} className="space-y-4 text-sm font-mono">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  TARGET EXAMINATION
                </label>
                <select
                  value={selectedExam}
                  onChange={(e) => setSelectedExam(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)]"
                >
                  <option value="TNPSC Group 4">TNPSC Group 4 (Tamil Nadu)</option>
                  <option value="TNPSC Group 2">TNPSC Group 2 / 2A</option>
                  <option value="UPSC CSE">UPSC Civil Services (Prelims)</option>
                  <option value="SSC CGL">SSC CGL (Tier 1)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                    TOTAL QUESTIONS
                  </label>
                  <select
                    value={selectedQuestions}
                    onChange={(e) => setSelectedQuestions(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)]"
                  >
                    <option value={5}>5 Questions (Quick)</option>
                    <option value={10}>10 Questions (Standard)</option>
                    <option value={20}>20 Questions (In-Depth)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                    TIME LIMIT
                  </label>
                  <select
                    value={selectedTime}
                    onChange={(e) => setSelectedTime(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)]"
                  >
                    <option value={10}>10 Minutes</option>
                    <option value={20}>20 Minutes</option>
                    <option value={30}>30 Minutes</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  DIFFICULTY
                </label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)]"
                >
                  <option value="easy">Easy — Core Syllabus Facts</option>
                  <option value="medium">Medium — Standard Exam Level</option>
                  <option value="hard">Hard — Advanced Conceptual & Analytical</option>
                </select>
              </div>

              <div className="pt-3 border-t flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg border text-xs font-mono text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="brand-button px-5 py-2 text-xs font-mono flex items-center gap-2"
                >
                  {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{creating ? "Generating Test..." : "Generate Test"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
