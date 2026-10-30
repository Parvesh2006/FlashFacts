"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, Calendar, GraduationCap, ArrowRight, BookOpen, Target, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { StudentMascot } from "@/components/illustrations/educational-illustrations";

export function WelcomeBanner() {
  const { user } = useAuth();
  const targetExam = user?.target_exam || "TNPSC Group 4";

  const todayStr = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="editorial-card p-5 sm:p-6 md:p-7 bg-[var(--surface)] border border-[var(--border)] shadow-xs">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        {/* Left Side: Mascot + Editorial Welcome Text */}
        <div className="flex items-start sm:items-center gap-4 sm:gap-5 max-w-3xl">
          {/* Friendly Student Mascot with subtle greeting */}
          <div className="shrink-0 pt-1 sm:pt-0">
            <StudentMascot size={84} className="sm:w-[96px] sm:h-[96px]" />
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
              <span className="badge-editorial text-[10px] text-[var(--brand-primary)] border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] font-semibold">
                CURRENT AFFAIRS INTELLIGENCE
              </span>

              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] text-[var(--text-secondary)] border border-[var(--border)] bg-[var(--surface-muted)]">
                <Calendar className="w-3 h-3 text-[var(--accent)]" />
                <span>{todayStr}</span>
              </span>

              <Link
                href="/exams"
                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] text-[var(--accent)] border border-[var(--accent-border)] bg-[var(--accent-soft)] hover:opacity-90 transition-opacity font-semibold"
                title="Change Target Exam"
              >
                <GraduationCap className="w-3 h-3" />
                <span>{targetExam}</span>
              </Link>
            </div>

            <h1 className="headline text-2xl sm:text-3xl md:text-[2.1rem] leading-tight text-[var(--text-primary)] font-bold">
              Your daily edge in current affairs.
            </h1>

            <p className="body-copy text-sm sm:text-base font-normal text-[var(--text-secondary)] leading-relaxed">
              Read smarter. Practise regularly. Prepare with confidence.
            </p>
          </div>
        </div>

        {/* Right Side: Quick Action Buttons (Blue as accent only!) */}
        <div className="flex flex-wrap sm:flex-col items-stretch gap-2.5 shrink-0 w-full sm:w-auto self-end sm:self-center">
          <Link
            href="/mock-tests"
            className="button-base button-primary px-4 py-2 text-xs font-semibold shadow-xs justify-center"
          >
            <Target className="w-3.5 h-3.5" />
            <span>Start Practice Drill</span>
            <ArrowRight className="w-3 h-3 ml-0.5" />
          </Link>

          <Link
            href="/pyqs"
            className="button-base button-secondary px-3.5 py-2 text-xs font-semibold justify-center hover:border-[var(--brand-primary)]"
          >
            <BookOpen className="w-3.5 h-3.5 text-[var(--brand-primary)]" />
            <span>Official PYQ Library</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
