"use client";

import React, { useState } from "react";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
import { MobileDrawer, MobileBottomBar } from "./mobile-nav";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="app-shell min-h-screen flex flex-col lg:flex-row">
      <Sidebar />
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 pb-16 lg:pb-0">
        <TopNav
          onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          isMobileMenuOpen={isMobileMenuOpen}
        />
        <main className="page-enter flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      <MobileBottomBar />
    </div>
  );
}
