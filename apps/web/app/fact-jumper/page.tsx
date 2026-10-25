"use client";

import React from "react";
import Link from "next/link";
import { BackButton } from "@/components/navigation/back-button";
import { FactJumperGame } from "@/components/game/fact-jumper-game";
import { Zap, WifiOff, Award, Sparkles, BookOpen, Target } from "lucide-react";

export default function FactJumperPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Navigation & Breadcrumb */}
      <div className="flex items-center justify-between">
        <BackButton label="Back to FlashFacts" />
        <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)]">
          <WifiOff className="w-3.5 h-3.5 text-emerald-500" />
          <span>Offline Ready</span>
        </div>
      </div>

      <p className="meta-text text-xs" role="note">
        Hidden Easter egg: press Alt + Shift + J from any FlashFacts page to open Fact Jumper.
      </p>

      {/* Main Game Interface */}
      <FactJumperGame />

      {/* Contextual Study Break & High Score Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center gap-2 text-[var(--brand-primary)]">
            <Zap className="w-4 h-4" />
            <h3 className="font-bold text-sm">Active Cognitive Reset</h3>
          </div>
          <p className="body-copy text-xs leading-relaxed">
            Taking a 2-minute active reflex break between intense mock tests or PYQ revision resets working memory and improves long-term concept consolidation.
          </p>
        </div>

        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center gap-2 text-amber-500">
            <Sparkles className="w-4 h-4" />
            <h3 className="font-bold text-sm">Milestone Exam Facts</h3>
          </div>
          <p className="body-copy text-xs leading-relaxed">
            Every 100 points unlocked presents a high-yield competitive exam fact across Indian Polity, History, Science & Technology, and Tamil Nadu heritage.
          </p>
        </div>

        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center gap-2 text-blue-500">
            <Award className="w-4 h-4" />
            <h3 className="font-bold text-sm">Local Storage Persistence</h3>
          </div>
          <p className="body-copy text-xs leading-relaxed">
            Your high score is preserved locally on this device. No accounts, cookies, internet connection, or external API calls required.
          </p>
        </div>
      </div>

      {/* Quick Links Back to Study Modes */}
      <div className="editorial-card p-6 flex flex-wrap items-center justify-between gap-4 bg-[var(--surface-muted)]/50">
        <div>
          <h4 className="font-bold text-sm text-[var(--text-primary)]">
            Ready to return to exam preparation?
          </h4>
          <p className="meta-text text-xs">
            Continue with your target syllabus progress or test yourself with authentic PYQs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/pyqs"
            className="brand-button text-xs font-mono px-4 py-2 flex items-center gap-1.5"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Practice PYQs</span>
          </Link>
          <Link
            href="/mock-tests"
            className="px-4 py-2 rounded-xl border text-xs font-mono font-semibold hover:bg-[var(--surface-elevated)] flex items-center gap-1.5 transition-colors"
          >
            <Target className="w-3.5 h-3.5" />
            <span>Mock Tests</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
