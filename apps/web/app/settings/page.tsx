"use client";

import React, { useState } from "react";
import {
  User,
  GraduationCap,
  LogOut,
  Sparkles,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import { BackButton } from "@/components/navigation/back-button";
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

export default function SettingsPage() {
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [updatingExam, setUpdatingExam] = useState<boolean>(false);

  const { user, isStudent, isGuest, logout, updateTargetExam } = useAuth();

  const exams = [
    "TNPSC Group 4",
    "TNPSC Group 2",
    "TNPSC Group 1",
    "UPSC CSE Prelims",
    "SSC CGL",
    "RRB NTPC",
  ];

  const handleTargetExamChange = async (newExam: string) => {
    setUpdatingExam(true);
    try {
      await updateTargetExam(newExam);
    } catch (err) {
      console.error("Failed to update target exam", err);
    } finally {
      setUpdatingExam(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto page-enter">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b border-[var(--border)] pb-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
            ASPIRANT PREFERENCES
          </span>
          <span className="text-xs text-[var(--text-muted)]">• Study Profile</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
          Settings & Preferences
        </h1>
        <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5">
          Configure your target examination, study preferences, and account synchronization across devices.
        </p>
      </div>

      {/* 1. Aspirant Profile & Target Exam */}
      <div className="editorial-card p-5 md:p-6 space-y-4 border border-[var(--border)] bg-[var(--surface)] shadow-xs">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <h2 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
            <User className="w-4 h-4 text-[var(--accent)]" />
            <span>Aspirant Profile & Target Examination</span>
          </h2>
          {isStudent && (
            <span className="badge-editorial text-[10px] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,var(--border))] font-semibold">
              Authenticated Student
            </span>
          )}
          {isGuest && (
            <span className="badge-editorial text-[10px] text-amber-700 border-amber-300 font-semibold">
              Guest Session
            </span>
          )}
        </div>

        {user ? (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] space-y-1">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
                  Aspirant Username
                </span>
                <span className="text-sm font-bold text-[var(--text-primary)]">{user.username}</span>
                {user.email && (
                  <span className="text-xs text-[var(--text-secondary)] block truncate">
                    {user.email}
                  </span>
                )}
              </div>

              <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] space-y-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
                  Current Target Exam
                </span>
                <select
                  disabled={updatingExam}
                  value={user.target_exam}
                  onChange={(e) => handleTargetExamChange(e.target.value)}
                  className="w-full py-2 px-3 text-xs rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] cursor-pointer"
                >
                  {exams.map((ex) => (
                    <option key={ex} value={ex}>
                      {ex}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {isGuest ? (
              <div className="p-4 rounded-xl border border-[color-mix(in_srgb,var(--accent)_30%,var(--border))] bg-[var(--accent-soft)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="font-semibold text-[var(--accent)] flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    <span>Active Guest Session</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    Test attempts and mistakes are saved for this browser session. Create an account to permanently sync your Mistake Book and scores across all your devices.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsAuthOpen(true)}
                  className="button-base button-primary px-3 py-1.5 text-xs whitespace-nowrap font-semibold shadow-xs"
                >
                  Sign In / Register
                </button>
              </div>
            ) : (
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => logout()}
                  className="button-base button-secondary px-3.5 py-1.5 text-xs flex items-center gap-1.5 text-[var(--danger)] hover:bg-[var(--danger-soft)] cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center space-y-3 text-xs">
            <p className="text-[var(--text-secondary)]">
              No authenticated account is currently active.
            </p>
            <button
              type="button"
              onClick={() => setIsAuthOpen(true)}
              className="button-base button-primary px-4 py-2 text-xs mx-auto font-semibold"
            >
              Sign In or Register
            </button>
          </div>
        )}
      </div>
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        title="Account Preferences"
      />
    </div>
  );
}
