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
  BookOpen,
  Target,
  AlertCircle,
  CheckSquare,
  BarChart3,
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
  { name: "Explore Archive", href: "/explore", icon: Compass },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "PYQ Bank", href: "/pyqs", icon: BookOpen, badge: "PYQ" },
  { name: "Mock Tests", href: "/mock-tests", icon: Target, badge: "Mock" },
  { name: "Mistake Book", href: "/revision", icon: AlertCircle },
  { name: "Syllabus Tracker", href: "/syllabus", icon: CheckSquare },
  { name: "Ask FlashFacts", href: "/ask", icon: MessageSquareText, badge: "AI" },
  { name: "Performance", href: "/analytics", icon: BarChart3 },
  { name: "Search", href: "/search", icon: Search },
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
    <div className="relative group">
      <Link
        href={item.href}
        aria-current={isActive ? "page" : undefined}
        aria-label={item.name}
        title={collapsed ? item.name : undefined}
        className={`sidebar-nav-item flex items-center rounded-xl transition-all ${
          collapsed
            ? "h-10 w-10 mx-auto justify-center p-0"
            : "gap-3 px-3 py-2 w-full"
        } ${
          isActive
            ? "bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] font-semibold border border-[var(--brand-primary-border)] shadow-2xs"
            : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-muted)]"
        }`}
      >
        <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center">
          <Icon className="h-4 w-4" />
        </span>

        <span
          className={`min-w-0 flex-1 truncate text-xs font-medium ${
            collapsed ? "hidden" : "inline"
          }`}
        >
          {item.name}
        </span>

        {/* Text badge when expanded */}
        {item.badge && (
          <span
            className={`soft-badge flex-shrink-0 px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase ${
              collapsed ? "hidden" : "inline"
            }`}
          >
            {item.badge}
          </span>
        )}

        {/* Small badge dot indicator when collapsed */}
        {item.badge && (
          <span
            className={`absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[var(--brand-primary)] border-2 border-[var(--surface)] ${
              collapsed ? "block" : "hidden"
            }`}
            title={`${item.name} (${item.badge})`}
          />
        )}
      </Link>

      {/* Instant Tooltip on Hover or Focus in Collapsed Mode */}
      <div
        role="tooltip"
        className={`pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50 rounded-md bg-[var(--text-primary)] px-2.5 py-1 text-xs font-medium text-white shadow-lg whitespace-nowrap transition-all ${
          collapsed ? "hidden group-hover:block group-focus-within:block" : "hidden"
        }`}
      >
        {item.name}
        {item.badge && (
          <span className="ml-1.5 opacity-80 text-[10px] font-mono">({item.badge})</span>
        )}
      </div>
    </div>
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
    {
      label: "EDITORIAL",
      items: [
        getItem("/"),
        getItem("/explore"),
        getItem("/calendar"),
      ],
    },
    {
      label: "EXAM PRACTICE",
      items: [
        getItem("/pyqs"),
        getItem("/mock-tests"),
        getItem("/revision"),
        getItem("/syllabus"),
      ],
    },
    {
      label: "INTELLIGENCE",
      items: [
        getItem("/ask"),
        getItem("/analytics"),
        getItem("/search"),
      ],
    },
  ];
  const settings = getItem("/settings");
  const toggleLabel = collapsed ? "Expand sidebar" : "Collapse sidebar";

  return (
    <aside
      className={`hidden lg:flex h-screen sticky top-0 z-40 select-none flex-shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)] transition-[width] duration-200 ease-in-out ${
        collapsed ? "w-[72px]" : "w-[260px]"
      }`}
      aria-label={collapsed ? "Collapsed sidebar" : "Expanded sidebar"}
    >
      {/* Brand Header with Logo Toggle */}
      <div
        className={`border-b border-[var(--border)] ${
          collapsed ? "px-3" : "px-4"
        } py-3.5 flex items-center ${collapsed ? "justify-center" : "justify-between"}`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <button
            type="button"
            onClick={onToggle}
            aria-label={toggleLabel}
            aria-expanded={!collapsed}
            title={toggleLabel}
            className="w-8 h-8 rounded-lg bg-[var(--brand-primary)] text-white flex items-center justify-center shadow-xs flex-shrink-0 hover:bg-[var(--brand-primary-hover)] active:scale-95 transition-all focus-visible:outline-2 focus-visible:outline-[var(--brand-primary)] cursor-pointer"
          >
            <Zap className="w-4 h-4 fill-current text-white" />
          </button>
          <Link
            href="/"
            className={`flex flex-col min-w-0 group focus-visible:outline-none ${
              collapsed ? "hidden" : "flex"
            }`}
            title="FlashFacts Home"
          >
            <span className="text-base font-extrabold tracking-tight text-[var(--text-primary)] font-serif leading-none truncate group-hover:text-[var(--brand-primary)] transition-colors">
              FLASHFACTS
            </span>
            <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-mono font-semibold">
              Daily Exam News
            </span>
          </Link>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className={`flex-1 space-y-6 overflow-y-auto py-5 ${collapsed ? "px-2" : "px-3.5"}`}>
        {sections.map((section) => (
          <section key={section.label} aria-labelledby={`sidebar-${section.label.toLowerCase()}`}>
            <h2
              id={`sidebar-${section.label.toLowerCase()}`}
              className={
                collapsed
                  ? "sr-only"
                  : "eyebrow mb-1.5 px-2 text-[10px] tracking-[0.14em] text-[var(--text-muted)] font-bold"
              }
            >
              {section.label}
            </h2>
            <div className="space-y-1">
              {section.items.map((item) => (
                <SidebarNavItem
                  key={item.href}
                  item={item}
                  pathname={pathname}
                  collapsed={collapsed}
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* Footer / Settings & Status */}
      <div className={`space-y-2 border-t border-[var(--border)] bg-[var(--surface-muted)]/50 p-3 ${collapsed ? "px-2" : ""}`}>
        <SidebarNavItem item={settings} pathname={pathname} collapsed={collapsed} />
        <div
          className={`flex items-center justify-between border-t border-[var(--border)] pt-2.5 px-2 text-[11px] font-mono text-[var(--text-muted)] ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <span className="flex items-center gap-1.5" title="FastAPI Live (Operational)">
            <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
            <span className={collapsed ? "hidden" : "inline"}>FastAPI Live</span>
          </span>
          <span className={`opacity-70 ${collapsed ? "hidden" : "inline"}`}>v2.5</span>
        </div>
      </div>
    </aside>
  );
}
