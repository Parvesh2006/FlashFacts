"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Compass,
  Calendar,
  Search,
  MessageSquareText,
  GraduationCap,
  Settings,
  Zap,
} from "lucide-react";

export interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export const navItems: NavItem[] = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Explore", href: "/explore", icon: Compass },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Search", href: "/search", icon: Search },
  { name: "Ask FlashFacts", href: "/ask", icon: MessageSquareText, badge: "AI" },
  { name: "Exam Mode", href: "/exams", icon: GraduationCap },
  { name: "Settings", href: "/settings", icon: Settings },
];

interface SidebarNavItemProps {
  item: NavItem;
  pathname: string;
  collapsed?: boolean;
}

export function SidebarNavItem({ item, pathname, collapsed = false }: SidebarNavItemProps) {
  const Icon = item.icon;
  const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

  return (
    <Link
      href={item.href}
      aria-current={isActive ? "page" : undefined}
      aria-label={collapsed ? item.name : undefined}
      title={collapsed ? item.name : undefined}
      className={`sidebar-nav-item group flex items-center ${collapsed ? "sidebar-nav-item-collapsed justify-center gap-0 px-2" : "gap-3"} ${
        isActive ? "sidebar-nav-item-active" : ""
      }`}
    >
      <span className="sidebar-nav-icon flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg">
        <Icon className="h-4 w-4" />
      </span>
      <span className={`sidebar-label min-w-0 flex-1 truncate ${collapsed ? "sidebar-label-collapsed" : ""}`}>
        {item.name}
      </span>
      {item.badge && !collapsed && (
        <span className="soft-badge flex-shrink-0 px-1.5 py-0.5 text-[10px] font-mono">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const getItem = (href: string) => navItems.find((item) => item.href === href)!;
  const sections = [
    { label: "MAIN", items: [getItem("/"), getItem("/explore"), getItem("/calendar")] },
    { label: "INTELLIGENCE", items: [getItem("/search"), getItem("/ask")] },
    { label: "LEARNING", items: [getItem("/exams")] },
  ];
  const settings = getItem("/settings");

  const toggleLabel = collapsed ? "Expand sidebar" : "Collapse sidebar";

  return (
    <aside
      className={`hidden lg:flex h-screen sticky top-0 z-30 select-none flex-shrink-0 flex-col border-r bg-[var(--surface)] transition-[width] duration-300 ease-out ${collapsed ? "w-[76px]" : "w-[272px]"}`}
      aria-label={collapsed ? "Collapsed sidebar" : "Expanded sidebar"}
    >
      <div className={`border-b ${collapsed ? "px-3" : "px-5"} py-6 ${collapsed ? "flex flex-col items-center gap-4" : "flex items-center justify-between gap-3"}`}>
        <div className={`flex min-w-0 items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
          <button
            type="button"
            onClick={onToggle}
            className="brand-mark flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl transition-transform duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brand-primary)]"
            aria-label={toggleLabel}
            aria-expanded={!collapsed}
            title={toggleLabel}
          >
            <Zap className="h-4 w-4 fill-current" />
          </button>
          <Link
            href="/"
            className={`sidebar-label min-w-0 group ${collapsed ? "sidebar-label-collapsed" : ""}`}
            aria-label="FlashFacts overview"
          >
            <h1 className="flex items-center gap-1.5 text-lg font-extrabold tracking-normal text-[var(--text-primary)]">
              FLASHFACTS
              <span className="soft-badge px-1.5 py-0.5 text-[10px] font-mono uppercase">v2.5</span>
            </h1>
            <p className="meta-text mt-1 uppercase">Current Affairs Intelligence</p>
          </Link>
        </div>
      </div>

      <div className={`flex-1 space-y-7 overflow-y-auto py-6 ${collapsed ? "px-3" : "px-4"}`}>
        {sections.map((section) => (
          <section key={section.label} aria-labelledby={`sidebar-${section.label.toLowerCase()}`}>
            <h2
              id={`sidebar-${section.label.toLowerCase()}`}
              className={`eyebrow mb-2 px-2 text-[10px] tracking-[0.14em] ${collapsed ? "hidden" : ""}`}
            >
              {section.label}
            </h2>
            <div className="space-y-2">
              {section.items.map((item) => (
                <SidebarNavItem key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className={`space-y-3 border-t bg-[var(--surface-muted)]/45 p-4 ${collapsed ? "px-3" : ""}`}>
        <p className={`eyebrow px-2 text-[10px] tracking-[0.14em] ${collapsed ? "hidden" : ""}`}>BOTTOM AREA</p>
        <SidebarNavItem item={settings} pathname={pathname} collapsed={collapsed} />
        <div className={`flex items-center justify-between border-t pt-3 meta-text ${collapsed ? "justify-center" : ""}`}>
          <span className="flex items-center gap-1.5" title="API Connected">
            <span className="h-2 w-2 rounded-full bg-[var(--success)] animate-pulse" />
            {!collapsed && <span>API Connected</span>}
          </span>
          {!collapsed && <span>FastAPI</span>}
        </div>
      </div>
    </aside>
  );
}
