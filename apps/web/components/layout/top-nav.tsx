"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Menu,
  X,
  Calendar as CalendarIcon,
  Zap,
  User,
  LogOut,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { AuthModal } from "@/components/auth/auth-modal";

interface TopNavProps {
  onMenuToggle?: () => void;
  isMobileMenuOpen?: boolean;
}

export function TopNav({ onMenuToggle, isMobileMenuOpen }: TopNavProps) {
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
      }),
    );
  }, []);

  return (
    <>
      <header className="sticky top-0 z-20 w-full border-b bg-[color-mix(in_srgb,var(--background)_88%,transparent)] backdrop-blur-md px-4 lg:px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="control lg:hidden p-2"
            aria-label="Toggle navigation"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-navigation"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex lg:hidden items-center gap-2">
            <div className="brand-mark w-7 h-7 rounded-md flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 fill-current" />
            </div>
            <span className="text-sm font-extrabold tracking-normal text-[var(--text-primary)]">
              FLASHFACTS
            </span>
          </div>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md mx-auto lg:mx-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search current affairs, events, domains..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="control-input w-full pl-9 pr-4 py-2 text-xs font-mono focus:outline-none focus:border-[var(--brand-primary)] transition-all"
            />
          </div>
        </form>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2">
            <div className="soft-badge flex items-center gap-2 px-3 py-1.5 meta-text">
              <CalendarIcon className="w-3.5 h-3.5 accent-mark" />
              <span>{todayDateFormatted}</span>
            </div>
          </div>

          {/* User Auth Status / Sign-in trigger */}
          {isStudent && user ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-xs">
                <div className="w-6 h-6 rounded-full bg-[var(--brand-primary)] text-white flex items-center justify-center font-bold text-[10px]">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="font-semibold text-[var(--text-primary)] leading-tight">
                    {user.username}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] leading-tight">
                    {user.target_exam}
                  </div>
                </div>
              </div>
              <button
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
              <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--surface-muted)] text-[11px] text-[var(--text-muted)] font-mono">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>Guest</span>
              </div>
              <button
                onClick={() => {
                  setAuthModalTab("login");
                  setIsAuthModalOpen(true);
                }}
                className="btn btn-primary px-3 py-1.5 text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Sign In to Save</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setAuthModalTab("login");
                  setIsAuthModalOpen(true);
                }}
                className="btn btn-primary px-3.5 py-1.5 text-xs font-semibold flex items-center gap-1.5"
              >
                <User className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            </div>
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
