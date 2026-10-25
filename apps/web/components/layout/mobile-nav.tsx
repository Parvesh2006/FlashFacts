"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItems } from "./sidebar";
import { LayoutDashboard, GraduationCap, BookOpen, Target, Search, X } from "lucide-react";

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileDrawer({ isOpen, onClose }: MobileNavProps) {
  const pathname = usePathname();

  if (!isOpen) return null;

  return (
    <div id="mobile-navigation" className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Mobile navigation">
      <div
        className="mobile-drawer-backdrop fixed inset-0 bg-[rgba(24,24,22,0.54)] backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="mobile-drawer fixed inset-y-0 left-0 w-72 bg-[var(--surface)] border-r p-5 shadow-2xl flex flex-col justify-between">
        <div className="overflow-y-auto max-h-[85vh]">
          <div className="flex items-center justify-between pb-4 border-b">
            <span className="font-extrabold text-[var(--text-primary)] tracking-normal">
              FLASHFACTS MENU
            </span>
            <button type="button" onClick={onClose} className="control p-2" aria-label="Close navigation">
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
                  className={`nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium ${
                    isActive
                      ? "nav-item-active bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] font-semibold border border-[var(--brand-primary-border)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-muted)]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="pt-4 border-t meta-text">
          Exam Intelligence Platform v2.5
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
    { name: "Exams", href: "/exams", icon: GraduationCap },
    { name: "PYQs", href: "/pyqs", icon: BookOpen },
    { name: "Mocks", href: "/mock-tests", icon: Target },
    { name: "Search", href: "/search", icon: Search },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 lg:hidden bg-[color-mix(in_srgb,var(--surface)_94%,transparent)] border-t backdrop-blur-md py-2 px-4 flex items-center justify-around">
      {mainTabs.map((tab) => {
        const Icon = tab.icon;
        const isActive =
          tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`nav-item flex flex-col items-center gap-1 text-[10px] font-mono ${
              isActive ? "text-[var(--brand-primary)] font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
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
