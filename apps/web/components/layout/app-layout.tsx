"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
import { MobileDrawer, MobileBottomBar } from "./mobile-nav";
import { ensureAuthSession } from "@/lib/auth";
import { OfflineCoordinator } from "@/components/offline/offline-coordinator";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    ensureAuthSession().catch(() => {});
  }, []);

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

  return (
    <div className="app-shell min-h-screen flex flex-col lg:flex-row">
      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed((current) => !current)}
      />
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 pb-16 lg:pb-0">
        <TopNav
          onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          isMobileMenuOpen={isMobileMenuOpen}
        />
        <main key={pathname} className="page-enter flex-1 w-full p-4 md:p-6 lg:p-8 xl:p-10">
          {children}
        </main>
      </div>

      <MobileBottomBar />
      <OfflineCoordinator />
    </div>
  );
}
