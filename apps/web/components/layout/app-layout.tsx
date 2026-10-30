"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
import { MobileDrawer, MobileBottomBar } from "./mobile-nav";
import { ensureAuthSession } from "@/lib/auth";
import { OfflineCoordinator } from "@/components/offline/offline-coordinator";

const SIDEBAR_STORAGE_KEY = "flashfacts-sidebar-collapsed";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
    ensureAuthSession().catch(() => {});

    // Ensure dark mode class is permanently stripped from the document
    try {
      localStorage.removeItem("flashfacts-theme");
      document.documentElement.classList.remove("dark");
    } catch {
      // ignore
    }

    // Load persisted sidebar collapsed state
    try {
      const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (saved !== null) {
        setIsSidebarCollapsed(saved === "true");
      }
    } catch {
      // ignore
    }
  }, []);

  const handleSidebarToggle = () => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  useEffect(() => {
    const handleEasterEggShortcut = (event: KeyboardEvent) => {
      const target = event.target;
      const isEditing =
        target instanceof HTMLElement &&
        (target.isContentEditable ||
          ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

      if (
        event.altKey &&
        event.shiftKey &&
        !event.ctrlKey &&
        !event.metaKey &&
        event.code === "KeyJ" &&
        !isEditing
      ) {
        event.preventDefault();
        if (pathname !== "/fact-jumper") router.push("/fact-jumper");
      }
    };

    window.addEventListener("keydown", handleEasterEggShortcut);
    return () => window.removeEventListener("keydown", handleEasterEggShortcut);
  }, [pathname, router]);

  const effectiveCollapsed = isMounted ? isSidebarCollapsed : false;

  return (
    <div className="app-shell min-h-screen flex flex-col lg:flex-row bg-[var(--background)]">
      <Sidebar
        collapsed={effectiveCollapsed}
        onToggle={handleSidebarToggle}
      />
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 pb-16 lg:pb-0 transition-all duration-200">
        <TopNav
          onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          isMobileMenuOpen={isMobileMenuOpen}
          isSidebarCollapsed={effectiveCollapsed}
          onSidebarToggle={handleSidebarToggle}
        />
        <main className="page-enter flex-1 w-full p-4 md:p-6 lg:p-8 xl:p-10">
          {children}
        </main>
      </div>

      <MobileBottomBar />
      <OfflineCoordinator />
    </div>
  );
}
