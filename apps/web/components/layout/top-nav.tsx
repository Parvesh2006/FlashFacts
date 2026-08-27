"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Menu, X, Calendar as CalendarIcon, Zap } from "lucide-react";

interface TopNavProps {
  onMenuToggle?: () => void;
  isMobileMenuOpen?: boolean;
}

export function TopNav({ onMenuToggle, isMobileMenuOpen }: TopNavProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

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

      <div className="hidden sm:flex items-center gap-2">
        <div className="soft-badge flex items-center gap-2 px-3 py-2 meta-text">
          <CalendarIcon className="w-3.5 h-3.5 accent-mark" />
          <span>{todayDateFormatted}</span>
        </div>
      </div>
    </header>
  );
}
