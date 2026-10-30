"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Menu,
  X,
  Calendar as CalendarIcon,
  User,
  LogOut,
  GraduationCap,
  Sparkles,
  Zap,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

interface TopNavProps {
  onMenuToggle?: () => void;
  isMobileMenuOpen?: boolean;
  isSidebarCollapsed?: boolean;
  onSidebarToggle?: () => void;
}

export function TopNav({
  onMenuToggle,
  isMobileMenuOpen,
  isSidebarCollapsed = false,
  onSidebarToggle,
}: TopNavProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("login");

  const { user, isStudent, isGuest, logout } = useAuth();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const [todayDateFormatted, setTodayDateFormatted] = useState("Today");

  useEffect(() => {
    setTodayDateFormatted(
      new Date().toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    );
  }, []);

  const activeTargetExam = user?.target_exam || "TNPSC Group 4";

  return (
    <>
      <header className="sticky top-0 z-30 w-full border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_90%,transparent)] backdrop-blur-md px-4 lg:px-8 py-2.5 flex items-center justify-between gap-4">
        {/* Mobile Toggle & Brand Logo Toggle */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenuToggle}
            className="control lg:hidden p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            aria-label="Toggle navigation"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-navigation"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onSidebarToggle}
              aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!isSidebarCollapsed}
              title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="w-8 h-8 rounded-lg bg-[var(--brand-primary)] text-white flex items-center justify-center shadow-xs hover:bg-[var(--brand-primary-hover)] active:scale-95 transition-all focus-visible:outline-2 focus-visible:outline-[var(--brand-primary)] cursor-pointer"
            >
              <Zap className="w-4 h-4 fill-current text-white" />
            </button>
            <Link
              href="/"
              className="flex flex-col group focus-visible:outline-none"
              title="FlashFacts Home"
            >
              <span className="text-base font-extrabold tracking-tight text-[var(--text-primary)] font-serif leading-none group-hover:text-[var(--brand-primary)] transition-colors">
                FLASHFACTS
              </span>
              <span className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-mono font-semibold leading-tight">
                Exam Intelligence
              </span>
            </Link>
          </div>
        </div>

        {/* Search Bar with Subtle Glass Effect */}
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-lg mx-auto hidden sm:block">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search current affairs, events, syllabus, topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-12 py-2 text-xs font-mono bg-[var(--surface-muted)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] focus:bg-[var(--surface)] transition-all"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-muted)] bg-[var(--surface)] border border-[var(--border)] rounded">
              ↵
            </kbd>
          </div>
        </form>

        {/* Context Controls & User Auth */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Target Exam Pill */}
          <Link
            href="/exams"
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] text-xs font-mono font-medium hover:opacity-90 transition-opacity"
            title="Current Target Examination (Click to switch)"
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span className="font-semibold">{activeTargetExam}</span>
          </Link>

          {/* Date Badge */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)] text-xs font-mono">
            <CalendarIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
            <span suppressHydrationWarning>{todayDateFormatted}</span>
          </div>

          {/* User Auth Status / Sign-in trigger */}
          {isStudent && user ? (
            <div className="flex items-center gap-2">
              <Link
                href="/settings"
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-xs hover:border-[var(--brand-primary)] transition-colors"
              >
                <div className="w-6 h-6 rounded-full bg-[var(--brand-primary)] text-white flex items-center justify-center font-bold text-[10px]">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="font-semibold text-[var(--text-primary)] leading-tight">
                    {user.username}
                  </div>
                </div>
              </Link>
              <button
                type="button"
                onClick={() => logout()}
                title="Log out"
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors"
                aria-label="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : isGuest && user ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--surface-muted)] text-[11px] text-[var(--text-muted)] font-mono border border-[var(--border)]">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>Guest</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setAuthModalTab("login");
                  setIsAuthModalOpen(true);
                }}
                className="brand-button px-3 py-1.5 text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => {
                setAuthModalTab("login");
                setIsAuthModalOpen(true);
              }}
              className="brand-button px-3.5 py-1.5 text-xs font-semibold flex items-center gap-1.5"
            >
              <User className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        defaultTab={authModalTab}
      />
    </>
  );
}
