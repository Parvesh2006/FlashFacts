"use client";

import React, { useEffect, useState } from "react";
import {
  GraduationCap,
  Building2,
  Landmark,
  Coins,
  TrainTrack,
  CheckCircle2,
  Clock,
  BookOpen,
  Brain,
  Newspaper,
  Target,
  ArrowRight,
  Sparkles,
  Loader2,
} from "lucide-react";
import { fetchExams, ExamCategory } from "@/services/exams";
import { BackButton } from "@/components/navigation/back-button";

const ICON_MAP: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  Building2,
  Landmark,
  GraduationCap,
  Coins,
  TrainTrack,
};

const EXAM_ICON_MAP: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  "tnpsc-group-4": Building2,
  "tnpsc-group-2": Building2,
  "ssc-cgl": GraduationCap,
  "ssc-chsl": GraduationCap,
  "upsc-cse": Landmark,
  "rrb-ntpc": TrainTrack,
  banking: Coins,
};

const TOPICS = [
  {
    id: "current-affairs",
    name: "Current Affairs",
    description: "Recent national and international developments",
    icon: Newspaper,
  },
  {
    id: "science-technology",
    name: "Science & Technology",
    description: "AI, space, research and emerging technology",
    icon: Brain,
  },
  {
    id: "government",
    name: "Government & Schemes",
    description: "Policies, schemes, institutions and appointments",
    icon: Landmark,
  },
  {
    id: "economy",
    name: "Economy",
    description: "Business, finance, banking and economic developments",
    icon: Coins,
  },
  {
    id: "sports",
    name: "Sports",
    description: "Major tournaments, players and sporting events",
    icon: Target,
  },
];

export default function ExamsPage() {
  const [exams, setExams] = useState<ExamCategory[]>([]);
  const [selectedExam, setSelectedExam] = useState<ExamCategory | null>(null);
  const [selectedTopic, setSelectedTopic] = useState("current-affairs");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExams() {
      try {
        const data = await fetchExams();
        setExams(data);

        if (data.length > 0) {
          setSelectedExam(data[0]);
        }
      } finally {
        setLoading(false);
      }
    }

    loadExams();
  }, []);

  const selectedTopicData = TOPICS.find(
    (topic) => topic.id === selectedTopic
  );

  return (
    <div className="space-y-7 max-w-6xl mx-auto">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b pb-5">
        <div className="eyebrow flex items-center gap-2 mb-2">
          <GraduationCap className="w-4 h-4" />
          <span>Competitive Exam Preparation</span>
        </div>

        <h1 className="headline text-3xl md:text-4xl">
          Exam Intelligence
        </h1>

        <p className="body-copy text-base mt-2 max-w-3xl">
          Turn live FlashFacts into focused exam preparation. Select your
          examination, choose a topic, and practice high-yield current affairs.
        </p>
      </div>

      {/* Selected Exam */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="headline text-xl">Choose your exam</h2>
            <p className="body-copy text-sm mt-1">
              Your preparation will be tailored to this examination.
            </p>
          </div>

          <div className="soft-badge hidden sm:flex items-center gap-2 text-sm font-mono px-3 py-2">
            <Clock className="w-4 h-4 accent-mark" />
            <span>Preparation Mode</span>
          </div>
        </div>

        {loading ? (
          <div className="editorial-card p-8 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin accent-mark" />
            <span className="body-copy">Loading examinations...</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {exams.map((exam) => {
              const IconComponent =
              EXAM_ICON_MAP[exam.id] ||
              ICON_MAP[exam.iconName] ||
              BookOpen;

              const isSelected = selectedExam?.id === exam.id;

              return (
                <button
                  key={exam.id}
                  onClick={() => setSelectedExam(exam)}
                  aria-pressed={isSelected}
                  className={`editorial-card editorial-card-hover p-5 text-left transition-all ${
                    isSelected
                      ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)]"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isSelected ? "brand-button" : "soft-badge"
                      }`}
                    >
                      <IconComponent className="w-5 h-5" />
                    </div>

                    {isSelected && (
                      <CheckCircle2 className="w-5 h-5 text-[var(--brand-primary)]" />
                    )}
                  </div>

                  <h3 className="font-bold text-base text-[var(--text-primary)] font-mono">
                    {exam.code}
                  </h3>

                  <p className="text-sm text-[var(--text-secondary)] font-mono mt-1 leading-snug">
                    {exam.name}
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Target Exam Summary */}
      {selectedExam && (
        <section className="editorial-card p-5 md:p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="eyebrow text-xs block mb-1">
                TARGET EXAMINATION
              </span>

              <h2 className="headline text-2xl">
                {selectedExam.name}
                <span className="text-[var(--text-secondary)]">
                  {" "}
                  ({selectedExam.code})
                </span>
              </h2>

              <p className="body-copy text-sm mt-2 max-w-3xl">
                {selectedExam.description}
              </p>
            </div>

            <div className="flex items-center gap-2 soft-badge px-4 py-2 text-sm font-mono shrink-0">
              <Sparkles className="w-4 h-4 accent-mark" />
              <span>AI-ready</span>
            </div>
          </div>
        </section>
      )}

      {/* Topic Selection */}
      <section>
        <div className="mb-4">
          <h2 className="headline text-xl">Choose a topic</h2>
          <p className="body-copy text-sm mt-1">
            Focus your preparation before starting practice.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {TOPICS.map((topic) => {
            const Icon = topic.icon;
            const isSelected = selectedTopic === topic.id;

            return (
              <button
                key={topic.id}
                onClick={() => setSelectedTopic(topic.id)}
                className={`editorial-card editorial-card-hover p-5 text-left transition-all ${
                  isSelected
                    ? "border-[var(--brand-primary)] bg-[var(--brand-primary-soft)]"
                    : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                      isSelected ? "brand-button" : "soft-badge"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>

                  {isSelected && (
                    <CheckCircle2 className="w-5 h-5 text-[var(--brand-primary)]" />
                  )}
                </div>

                <h3 className="text-lg font-semibold text-[var(--text-primary)] mt-4">
                  {topic.name}
                </h3>

                <p className="text-sm text-[var(--text-secondary)] mt-1 leading-relaxed">
                  {topic.description}
                </p>
              </button>
            );
          })}
        </div>
      </section>

      {/* Start Practice */}
      <section className="editorial-panel p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-5 h-5 accent-mark" />

              <span className="eyebrow text-xs">
                READY TO PRACTICE
              </span>
            </div>

            <h2 className="headline text-2xl">
              {selectedTopicData?.name}
            </h2>

            <p className="body-copy text-sm mt-2">
              {selectedExam?.code} · Practice questions based on FlashFacts
              intelligence.
            </p>
          </div>

          <button
            type="button"
            disabled={!selectedExam}
            className="brand-button inline-flex items-center justify-center gap-2 px-5 py-3 rounded-lg text-sm font-semibold shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => {
              if (!selectedExam) return;

              alert(
                `${selectedExam.code} · ${selectedTopicData?.name}\n\nMCQ engine is the next stage.`
              );
            }}
          >
            <span>Start Practice</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* Coming Next */}
      <section className="border-t pt-5">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-[var(--text-secondary)] font-mono">
          <span>✓ Live FlashFacts</span>
          <span>✓ Historical search</span>
          <span>✓ Exam selection</span>
          <span>→ MCQ engine next</span>
          <span>→ AI FlashFacts next</span>
        </div>
      </section>
    </div>
  );
}