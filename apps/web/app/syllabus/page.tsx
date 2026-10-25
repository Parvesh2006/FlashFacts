"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckSquare,
  BookOpen,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Loader2,
  AlertCircle,
  FileText,
  Save,
  ArrowRight,
} from "lucide-react";
import {
  fetchExamSyllabus,
  updateTopicProgress,
  ExamSyllabus,
  SyllabusTopic,
} from "@/services/syllabus";
import { BackButton } from "@/components/navigation/back-button";

const EXAM_OPTIONS = [
  "TNPSC Group 4",
  "UPSC CSE",
  "SSC CGL",
];

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  not_started: { label: "Not Started", color: "bg-slate-500/10 text-slate-500" },
  in_progress: { label: "In Progress", color: "bg-blue-500/10 text-blue-600 font-semibold" },
  completed: { label: "Completed", color: "bg-emerald-500/10 text-emerald-600 font-semibold" },
  needs_revision: { label: "Needs Revision", color: "bg-amber-500/10 text-amber-600 font-semibold" },
};

export default function SyllabusPage() {
  const [selectedExam, setSelectedExam] = useState("TNPSC Group 4");
  const [syllabus, setSyllabus] = useState<ExamSyllabus | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedUnits, setExpandedUnits] = useState<Record<string, boolean>>({});

  // Notes editing state
  const [editingNotesTopicId, setEditingNotesTopicId] = useState<number | null>(null);
  const [notesText, setNotesText] = useState<string>("");
  const [savingNotes, setSavingNotes] = useState(false);

  useEffect(() => {
    loadSyllabus();
  }, [selectedExam]);

  const loadSyllabus = async () => {
    setLoading(true);
    try {
      const data = await fetchExamSyllabus(selectedExam);
      setSyllabus(data);

      // Default expand all units on first load
      const initialExpanded: Record<string, boolean> = {};
      data.subjects.forEach((subj) => {
        subj.units.forEach((unit) => {
          initialExpanded[`${subj.subject}-${unit.unit_name}`] = true;
        });
      });
      setExpandedUnits(initialExpanded);
    } catch (err) {
      console.error("Failed to load syllabus", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleUnit = (unitKey: string) => {
    setExpandedUnits((prev) => ({ ...prev, [unitKey]: !prev[unitKey] }));
  };

  const handleStatusChange = async (
    topic: SyllabusTopic,
    newStatus: "not_started" | "in_progress" | "completed" | "needs_revision"
  ) => {
    try {
      await updateTopicProgress({
        topic_id: topic.id,
        status: newStatus,
        notes: topic.notes,
      });

      // Update state in place and recalculate percentages
      loadSyllabus();
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const handleSaveNotes = async (topicId: number) => {
    setSavingNotes(true);
    try {
      const targetTopic = syllabus?.subjects
        .flatMap((s) => s.units)
        .flatMap((u) => u.topics)
        .find((t) => t.id === topicId);

      await updateTopicProgress({
        topic_id: topicId,
        status: targetTopic?.status || "in_progress",
        notes: notesText,
      });
      setEditingNotesTopicId(null);
      loadSyllabus();
    } catch (err) {
      console.error("Failed to save notes", err);
    } finally {
      setSavingNotes(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-7">
      <BackButton fallbackHref="/exams" />

      {/* Header */}
      <div className="border-b pb-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="eyebrow flex items-center gap-2 mb-2">
            <CheckSquare className="w-4 h-4" />
            <span>Official Curriculum Mapping</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl">Syllabus Completion Tracker</h1>
          <p className="body-copy text-base mt-2 max-w-3xl">
            Track your preparation against the official notification syllabus for your target exam.
            Mark topics as completed, record revision notes, and connect directly to relevant PYQs and current affairs.
          </p>
        </div>

        {/* Exam Selector */}
        <div className="flex gap-2">
          {EXAM_OPTIONS.map((exam) => (
            <button
              key={exam}
              onClick={() => setSelectedExam(exam)}
              className={`px-3.5 py-2 rounded-xl text-xs font-mono font-medium transition-all ${
                selectedExam === exam
                  ? "bg-[var(--brand-primary)] text-white shadow-sm"
                  : "bg-[var(--surface-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {exam}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="editorial-card p-12 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin accent-mark" />
          <span className="body-copy text-sm font-mono">Loading curriculum topics...</span>
        </div>
      ) : !syllabus ? (
        <div className="editorial-card p-12 text-center">
          <p className="body-copy text-sm">Failed to load syllabus data.</p>
        </div>
      ) : (
        <>
          {/* Overall Completion Hero Card */}
          <div className="editorial-card p-6 md:p-8 space-y-4 bg-gradient-to-br from-[var(--surface-elevated)] to-[var(--surface)]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="eyebrow text-xs">CURRICULUM MASTERY</span>
                <h3 className="headline text-2xl font-bold">{syllabus.exam_name} Progress</h3>
                <p className="body-copy text-xs font-mono mt-1">
                  {syllabus.completed_topics} of {syllabus.total_topics} topics completed (
                  {syllabus.in_progress_topics} in progress, {syllabus.needs_revision_topics} needing revision)
                </p>
              </div>

              <div className="text-3xl font-bold font-mono text-emerald-600 bg-[var(--surface)] px-4 py-2 rounded-xl border">
                {syllabus.overall_completion_percentage}%
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-3 rounded-full overflow-hidden bg-slate-200 dark:bg-slate-800">
              <div
                style={{ width: `${syllabus.overall_completion_percentage}%` }}
                className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
              />
            </div>
          </div>

          {/* Subjects Hierarchy */}
          <div className="space-y-6">
            {syllabus.subjects.map((subj) => (
              <div key={subj.subject} className="editorial-card p-6 space-y-5">
                {/* Subject Header */}
                <div className="flex items-center justify-between border-b pb-3">
                  <div>
                    <h3 className="headline text-xl font-bold">{subj.subject}</h3>
                    <span className="text-xs font-mono text-[var(--text-secondary)]">
                      {subj.completed_count} of {subj.total_count} topics completed
                    </span>
                  </div>
                  <div className="text-sm font-mono font-bold text-emerald-600 bg-emerald-500/10 px-3 py-1 rounded-lg">
                    {subj.completion_percentage}%
                  </div>
                </div>

                {/* Units within Subject */}
                <div className="space-y-4">
                  {subj.units.map((unit) => {
                    const unitKey = `${subj.subject}-${unit.unit_name}`;
                    const isExpanded = expandedUnits[unitKey] !== false;

                    return (
                      <div key={unit.unit_name} className="border rounded-xl bg-[var(--surface)] overflow-hidden">
                        {/* Unit Title Bar */}
                        <button
                          type="button"
                          onClick={() => toggleUnit(unitKey)}
                          className="w-full p-4 flex items-center justify-between gap-3 text-left hover:bg-[var(--surface-elevated)] transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-[var(--brand-primary)]" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-[var(--text-secondary)]" />
                            )}
                            <span className="font-semibold text-sm text-[var(--text-primary)]">
                              {unit.unit_name}
                            </span>
                          </div>

                          <span className="text-xs font-mono text-[var(--text-secondary)]">
                            {unit.completed_count} / {unit.total_count} completed ({unit.completion_percentage}%)
                          </span>
                        </button>

                        {/* Topics List */}
                        {isExpanded && (
                          <div className="p-4 pt-0 space-y-4 border-t divide-y divide-[var(--border-subtle)]">
                            {unit.topics.map((topic) => {
                              const isEditingNotes = editingNotesTopicId === topic.id;
                              const statusConfig = STATUS_LABELS[topic.status] || STATUS_LABELS.not_started;

                              return (
                                <div key={topic.id} className="pt-4 first:pt-3 space-y-3">
                                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                                    <div className="space-y-1 max-w-2xl">
                                      <h4 className="text-sm font-semibold text-[var(--text-primary)] leading-snug">
                                        {topic.topic_name}
                                      </h4>

                                      {/* Subtopics */}
                                      {topic.subtopics && topic.subtopics.length > 0 && (
                                        <div className="flex flex-wrap gap-1.5 pt-1">
                                          {topic.subtopics.map((st, stIdx) => (
                                            <span
                                              key={stIdx}
                                              className="text-[11px] font-mono text-[var(--text-secondary)] bg-[var(--surface-elevated)] px-2 py-0.5 rounded border"
                                            >
                                              {st}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                    </div>

                                    {/* Status Selector Dropdown */}
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                      <select
                                        value={topic.status}
                                        onChange={(e) =>
                                          handleStatusChange(
                                            topic,
                                            e.target.value as "not_started" | "in_progress" | "completed" | "needs_revision"
                                          )
                                        }
                                        className={`text-xs font-mono px-3 py-1.5 rounded-lg border focus:outline-none ${statusConfig.color}`}
                                      >
                                        <option value="not_started">Not Started</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                        <option value="needs_revision">Needs Revision</option>
                                      </select>
                                    </div>
                                  </div>

                                  {/* Notes & Quick Links Bar */}
                                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-[var(--text-secondary)] pt-1">
                                    <div className="flex items-center gap-3">
                                      <button
                                        type="button"
                                        onClick={() => {
                                          if (isEditingNotes) {
                                            setEditingNotesTopicId(null);
                                          } else {
                                            setEditingNotesTopicId(topic.id);
                                            setNotesText(topic.notes || "");
                                          }
                                        }}
                                        className="text-[var(--brand-primary)] hover:underline flex items-center gap-1"
                                      >
                                        <FileText className="w-3.5 h-3.5" />
                                        <span>{topic.notes ? "Edit Notes" : "+ Add Study Notes"}</span>
                                      </button>

                                      {topic.last_studied_at && (
                                        <span className="text-[11px]">
                                          Last studied: {new Date(topic.last_studied_at).toLocaleDateString()}
                                        </span>
                                      )}
                                    </div>

                                    <Link
                                      href={`/pyqs?exam_name=${encodeURIComponent(selectedExam)}&subject=${encodeURIComponent(topic.subject)}`}
                                      className="text-xs text-[var(--text-secondary)] hover:text-[var(--brand-primary)] flex items-center gap-1"
                                    >
                                      <span>Practice Topic PYQs</span>
                                      <ArrowRight className="w-3 h-3" />
                                    </Link>
                                  </div>

                                  {/* Notes Box */}
                                  {isEditingNotes ? (
                                    <div className="p-3 rounded-lg border bg-[var(--surface-elevated)] space-y-2">
                                      <textarea
                                        value={notesText}
                                        onChange={(e) => setNotesText(e.target.value)}
                                        placeholder="Record key constitutional articles, formulas, dates, or concepts to remember..."
                                        rows={3}
                                        className="w-full text-xs p-2.5 rounded border bg-[var(--surface)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-primary)]"
                                      />
                                      <div className="flex justify-end gap-2">
                                        <button
                                          type="button"
                                          onClick={() => setEditingNotesTopicId(null)}
                                          className="px-3 py-1 text-xs font-mono rounded border"
                                        >
                                          Cancel
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => handleSaveNotes(topic.id)}
                                          disabled={savingNotes}
                                          className="brand-button px-3.5 py-1 text-xs font-mono flex items-center gap-1.5"
                                        >
                                          <Save className="w-3 h-3" />
                                          <span>{savingNotes ? "Saving..." : "Save Notes"}</span>
                                        </button>
                                      </div>
                                    </div>
                                  ) : (
                                    topic.notes && (
                                      <div className="p-2.5 rounded-lg bg-[var(--surface-elevated)] border text-xs text-[var(--text-secondary)] italic">
                                        "{topic.notes}"
                                      </div>
                                    )
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
