"use client";

import React, { useState } from "react";
import {
  GraduationCap,
  Building2,
  Landmark,
  Coins,
  TrainTrack,
  CheckCircle2,
  Clock,
  BookOpen,
} from "lucide-react";
import { EXAM_CATEGORIES, ExamCategory } from "@/services/exams";
import { BackButton } from "@/components/navigation/back-button";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Building2,
  Landmark,
  GraduationCap,
  Coins,
  TrainTrack,
};

export default function ExamsPage() {
  const [selectedExam, setSelectedExam] = useState<ExamCategory>(EXAM_CATEGORIES[0]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b pb-4">
        <div className="eyebrow flex items-center gap-2 mb-1">
          <GraduationCap className="w-4 h-4" />
          <span>Competitive Exam Preparation Engine</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">
          Exam Intelligence
        </h1>
        <p className="body-copy text-sm">
          Targeted current affairs scoring, high-yield topic filtering, and MCQ generation for competitive exams.
        </p>
      </div>

      {/* Exam Selection Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {EXAM_CATEGORIES.map((exam) => {
          const IconComponent = ICON_MAP[exam.iconName] || BookOpen;
          const isSelected = selectedExam.id === exam.id;

          return (
            <button
              key={exam.id}
              onClick={() => setSelectedExam(exam)}
              aria-pressed={isSelected}
              className={`editorial-card editorial-card-hover p-4 text-left ${
                isSelected
                  ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)]"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    isSelected ? "brand-button" : "soft-badge"
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                </div>
                {isSelected && <CheckCircle2 className="w-4 h-4 text-[var(--brand-primary)]" />}
              </div>
              <h3 className="font-bold text-sm text-[var(--text-primary)] font-mono">{exam.code}</h3>
              <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5 leading-snug">{exam.name}</p>
            </button>
          );
        })}
      </div>

      {/* Selected Exam Dashboard & Empty Preparation State */}
      <div className="editorial-card p-5 md:p-7 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
          <div>
            <span className="eyebrow text-[11px] block">
              TARGET EXAMINATION PROFILE
            </span>
            <h2 className="headline text-xl">{selectedExam.name} ({selectedExam.code})</h2>
            <p className="body-copy text-xs mt-1">{selectedExam.description}</p>
          </div>

          <div className="soft-badge flex items-center gap-2 text-xs font-mono px-3 py-1.5 self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5 accent-mark" />
            <span>Preparation Mode Active</span>
          </div>
        </div>

        {/* Phase 2 Preparation State Box */}
        <div className="editorial-panel p-6 md:p-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-full status-warning flex items-center justify-center mx-auto">
            <GraduationCap className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-[var(--text-primary)]">
            Exam Intelligence Engine in Preparation
          </h3>
          <p className="text-xs text-[var(--text-secondary)] max-w-lg mx-auto font-mono leading-relaxed">
            The exam mapping & MCQ generation model is currently being calibrated for {selectedExam.code}.
            Future releases will map events directly to exam syllabus weightages.
          </p>
          <div className="pt-2 font-mono text-[11px] text-[var(--text-muted)]">
            Endpoint Stubs Ready: GET /api/v1/exams | POST /api/v1/questions
          </div>
        </div>
      </div>
    </div>
  );
}
