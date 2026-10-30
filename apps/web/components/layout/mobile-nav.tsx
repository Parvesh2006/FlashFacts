"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItems } from "./sidebar";
import {
  LayoutDashboard,
  GraduationCap,
  BookOpen,
  Target,
  MessageSquareText,
  X,
  Zap,
  Compass,
} from "lucide-react";

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileDrawer({ isOpen, onClose }: MobileNavProps) {
  const pathname = usePathname();

  if (!isOpen) return null;

  return (
    <div
      id="mobile-navigation"
      className="fixed inset-0 z-50 lg:hidden"
      role="dialog"
      aria-modal="true"
      aria-label="Mobile navigation"
    >
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 left-0 w-72 bg-[var(--surface)] border-r border-[var(--border)] p-5 shadow-2xl flex flex-col justify-between">
        <div className="overflow-y-auto max-h-[85vh]">
          <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-[var(--brand-primary)] text-white flex items-center justify-center">
                <Zap className="w-4 h-4 fill-current text-white" />
              </div>
              <span className="font-extrabold text-sm text-[var(--text-primary)] font-serif">
                FLASHFACTS
              </span>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              aria-label="Close navigation"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] font-semibold border border-[var(--brand-primary-border)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-muted)]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="flex-1">{item.name}</span>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold bg-[var(--surface-muted)] border border-[var(--border)]">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="pt-4 border-t border-[var(--border)] text-[11px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Exam Intelligence Platform</span>
          <span>v2.5</span>
        </div>
      </div>
    </div>
  );
}

// Bottom navigation bar for small mobile screens
export function MobileBottomBar() {
  const pathname = usePathname();

  const mainTabs = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Explore", href: "/explore", icon: Compass },
    { name: "PYQs", href: "/pyqs", icon: BookOpen },
    { name: "Mocks", href: "/mock-tests", icon: Target },
    { name: "Ask AI", href: "/ask", icon: MessageSquareText },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 lg:hidden bg-[color-mix(in_srgb,var(--surface)_92%,transparent)] border-t border-[var(--border)] backdrop-blur-md py-2 px-3 flex items-center justify-around shadow-lg">
      {mainTabs.map((tab) => {
        const Icon = tab.icon;
        const isActive =
          tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex flex-col items-center gap-1 py-1 px-2.5 rounded-lg text-[10px] font-mono transition-colors ${
              isActive
                ? "text-[var(--brand-primary)] font-bold bg-[var(--brand-primary-soft)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
            aria-current={isActive ? "page" : undefined}
          >
            <Icon className="w-4 h-4" />
            <span>{tab.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}
