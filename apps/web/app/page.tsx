"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Compass,
  Layers,
  RefreshCw,
  GraduationCap,
  BookOpen,
  Target,
  AlertCircle,
  Building2,
  Landmark,
  TrainTrack,
  Sparkles,
  Search,
} from "lucide-react";
import { WelcomeBanner } from "@/components/dashboard/welcome-banner";
import { StatCards } from "@/components/dashboard/stat-cards";
import { DomainGrid } from "@/components/domains/domain-grid";
import { EventCard } from "@/components/events/event-card";
import { SkeletonGrid } from "@/components/common/skeleton-loader";
import { ErrorState } from "@/components/common/error-state";
import { getEvents } from "@/services/events";
import { getDomains } from "@/services/domains";
import { getSources } from "@/services/sources";
import { Event } from "@/types/event";
import { DomainStat } from "@/types/domain";

export default function DashboardPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [totalEvents, setTotalEvents] = useState<number>(0);
  const [domains, setDomains] = useState<DomainStat[]>([]);
  const [sourceCount, setSourceCount] = useState<number>(0);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [eventsRes, domainsRes, sourcesRes] = await Promise.all([
        getEvents({ limit: 10 }),
        getDomains(),
        getSources(),
      ]);

      setEvents(eventsRes.events || []);
      setTotalEvents(eventsRes.total || 0);
      setDomains(domainsRes || []);
      setSourceCount((sourcesRes || []).length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const leadStory = events.length > 0 ? events[0] : null;
  const secondaryStories = events.length > 1 ? events.slice(1, 7) : [];

  const examShortcuts = [
    {
      name: "TNPSC Group 4",
      sub: "General Studies & Tamil Nadu Affairs",
      href: "/exams",
      icon: Building2,
      badge: "State",
      color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20",
    },
    {
      name: "TNPSC Group 2",
      sub: "Administration & Development",
      href: "/exams",
      icon: Building2,
      badge: "State",
      color: "text-teal-600 bg-teal-500/10 border-teal-500/20",
    },
    {
      name: "UPSC CSE Prelims",
      sub: "National & Global Importance",
      href: "/exams",
      icon: Landmark,
      badge: "National",
      color: "text-blue-600 bg-blue-500/10 border-blue-500/20",
    },
    {
      name: "SSC CGL",
      sub: "General Awareness & Economy",
      href: "/exams",
      icon: GraduationCap,
      badge: "Central",
      color: "text-indigo-600 bg-indigo-500/10 border-indigo-500/20",
    },
    {
      name: "RRB NTPC",
      sub: "Current Affairs & Railways",
      href: "/exams",
      icon: TrainTrack,
      badge: "Central",
      color: "text-amber-600 bg-amber-500/10 border-amber-500/20",
    },
  ];

  return (
    <div className="space-y-10 max-w-7xl mx-auto">
      {/* 1. Text-Only Hero / Welcome Area */}
      <WelcomeBanner />

      {error ? (
        <ErrorState message={error} onRetry={fetchDashboardData} />
      ) : loading ? (
        <div className="space-y-6">
          <SkeletonGrid count={4} />
          <div className="h-64 rounded-xl skeleton-shimmer" />
        </div>
      ) : (
        <>
          {/* 2. Lead Story Section (Prominent Editorial Card) */}
          {leadStory && (
            <section className="space-y-3" aria-labelledby="lead-story-heading">
              <div className="flex items-center justify-between">
                <span id="lead-story-heading" className="eyebrow flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>TODAY&apos;S EDITORIAL LEAD</span>
                </span>
                <span className="text-xs font-mono text-[var(--text-muted)]">
                  Highest Importance &amp; Verified Accuracy
                </span>
              </div>

              <EventCard event={leadStory} variant="lead" />
            </section>
          )}

          {/* 3. Continue Learning / Quick Action Bento Row */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-4" aria-label="Learning Actions">
            {/* Quick Practice Card */}
            <div className="editorial-card p-5 flex flex-col justify-between bg-[var(--surface)] border border-[var(--border)] border-l-4 border-l-[var(--brand-primary)] shadow-xs">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="badge-editorial text-[10px] text-[var(--brand-primary)] border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] font-semibold">
                    DAILY DRILL
                  </span>
                  <Target className="w-4 h-4 text-[var(--brand-primary)]" />
                </div>
                <h3 className="headline text-lg font-bold text-[var(--text-primary)]">Mock Test Practice</h3>
                <p className="body-copy-sm text-xs sm:text-[13px] text-[var(--text-secondary)]">
                  Take a 10 or 25-question timed mock test calibrated with official negative marking and real PYQs.
                </p>
              </div>
              <div className="pt-4 mt-2">
                <Link
                  href="/mock-tests"
                  className="button-base button-primary w-full text-xs py-2 px-3 flex items-center justify-center gap-1.5 font-semibold shadow-xs"
                >
                  <span>Launch Practice Test</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {/* PYQ Library Spotlight */}
            <div className="editorial-card p-5 flex flex-col justify-between bg-[var(--surface)] border border-[var(--border)] border-l-4 border-l-[var(--accent)] shadow-xs">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="badge-editorial text-[10px] text-[var(--accent)] border-[var(--accent-border)] bg-[var(--accent-soft)] font-semibold">
                    OFFICIAL PAPERS
                  </span>
                  <BookOpen className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <h3 className="headline text-lg font-bold text-[var(--text-primary)]">Previous Year Papers</h3>
                <p className="body-copy-sm text-xs sm:text-[13px] text-[var(--text-secondary)]">
                  Access authentic TNPSC, UPSC &amp; SSC question papers with verified official answer keys and in-browser PDF viewing.
                </p>
              </div>
              <div className="pt-4 mt-2">
                <Link
                  href="/pyqs"
                  className="button-base button-secondary w-full text-xs py-2 px-3 flex items-center justify-center gap-1.5 font-semibold hover:border-[var(--brand-primary)]"
                >
                  <span>Explore PYQ Library</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {/* Mistake Book Card */}
            <div className="editorial-card p-5 flex flex-col justify-between bg-[var(--surface)] border border-[var(--border)] border-l-4 border-l-amber-500 shadow-xs">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="badge-editorial text-[10px] text-amber-700 border-amber-300 bg-amber-50 font-semibold">
                    SPACED REPETITION
                  </span>
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                </div>
                <h3 className="headline text-lg font-bold text-[var(--text-primary)]">Aspirant Mistake Book</h3>
                <p className="body-copy-sm text-xs sm:text-[13px] text-[var(--text-secondary)]">
                  Review tricky questions you previously missed. Master difficult concepts through automated spaced-repetition schedules.
                </p>
              </div>
              <div className="pt-4 mt-2">
                <Link
                  href="/revision"
                  className="button-base button-secondary w-full text-xs py-2 px-3 flex items-center justify-center gap-1.5 font-semibold border-amber-300 text-amber-700 hover:bg-amber-50"
                >
                  <span>Review Mistakes</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </section>

          {/* 4. Latest Current Affairs (Modular Bento Grid) */}
          <section className="space-y-4" aria-labelledby="latest-news-heading">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
              <div>
                <h2 id="latest-news-heading" className="headline text-2xl flex items-center gap-2">
                  <Compass className="w-5 h-5 text-[var(--brand-primary)]" />
                  <span>Latest Exam-Relevant Developments</span>
                </h2>
                <p className="body-copy text-xs sm:text-sm">
                  Curated and deduplicated stories filtered for competitive examination usefulness
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={fetchDashboardData}
                  className="control p-2 text-[var(--text-secondary)] hover:text-[var(--brand-primary)]"
                  title="Refresh latest stories"
                  aria-label="Refresh latest stories"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
                <Link
                  href="/explore"
                  className="button-base button-secondary px-3 py-1.5 text-xs flex items-center gap-1.5"
                >
                  <span>View All Archive</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {secondaryStories.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {secondaryStories.map((ev) => (
                  <EventCard key={ev.id} event={ev} />
                ))}
              </div>
            ) : (
              <div className="editorial-card p-8 text-center text-xs font-mono text-[var(--text-muted)]">
                No secondary stories currently available.
              </div>
            )}
          </section>

          {/* 5. Exam Preparation Hub */}
          <section className="space-y-4" aria-labelledby="exam-hub-heading">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div>
                <h2 id="exam-hub-heading" className="headline text-2xl flex items-center gap-2">
                  <GraduationCap className="w-5 h-5 text-[var(--accent)]" />
                  <span>Target Exam Portals</span>
                </h2>
                <p className="body-copy text-xs sm:text-sm">
                  Jump directly into curated syllabus feeds, mock tests, and question banks
                </p>
              </div>

              <Link
                href="/exams"
                className="text-xs font-mono font-semibold text-[var(--brand-primary)] flex items-center gap-1"
              >
                <span>All Exams</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {examShortcuts.map((exam, i) => {
                const Icon = exam.icon;
                return (
                  <Link
                    key={i}
                    href={exam.href}
                    className="editorial-card p-4 hover:border-[var(--brand-primary)] transition-all flex flex-col justify-between group"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${exam.color}`}>
                          {exam.badge}
                        </span>
                        <Icon className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand-primary)] transition-colors" />
                      </div>
                      <h4 className="font-bold text-sm text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
                        {exam.name}
                      </h4>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-snug">
                        {exam.sub}
                      </p>
                    </div>

                    <div className="pt-3 mt-3 border-t border-[var(--border)] flex items-center justify-between text-[11px] font-mono text-[var(--brand-primary)]">
                      <span>Open Feed</span>
                      <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>

          {/* 6. Real Live Metrics Overview */}
          <section className="space-y-3" aria-labelledby="metrics-heading">
            <div className="border-b border-[var(--border)] pb-2">
              <span id="metrics-heading" className="eyebrow">
                PLATFORM INTEGRITY &amp; SYSTEM METRICS
              </span>
            </div>
            <StatCards
              totalEvents={totalEvents}
              domainCount={domains.length}
              sourceCount={sourceCount}
            />
          </section>

          {/* 7. Domain Intelligence Breakdown */}
          <section className="space-y-4" aria-labelledby="domains-heading">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <div>
                <h2 id="domains-heading" className="headline text-2xl flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[var(--brand-primary)]" />
                  <span>Syllabus Domain Breakdown</span>
                </h2>
                <p className="body-copy text-xs sm:text-sm">
                  Filter verified current affairs by official subject domains
                </p>
              </div>

              <Link
                href="/explore"
                className="text-xs font-mono font-semibold text-[var(--brand-primary)] flex items-center gap-1"
              >
                <span>Browse All</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <DomainGrid domains={domains} />
          </section>
        </>
      )}
    </div>
  );
}
