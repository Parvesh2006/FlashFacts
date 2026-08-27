"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Compass, Layers, RefreshCw } from "lucide-react";
import { WelcomeBanner } from "@/components/dashboard/welcome-banner";
import { StatCards } from "@/components/dashboard/stat-cards";
import { DomainGrid } from "@/components/domains/domain-grid";
import { EventList } from "@/components/events/event-list";
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
        getEvents({ limit: 12 }),
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

  return (
    <div className="space-y-8">
      {/* 1. Welcome Header Banner */}
      <WelcomeBanner />

      {/* Error state if backend fails */}
      {error ? (
        <ErrorState message={error} onRetry={fetchDashboardData} />
      ) : loading ? (
        <SkeletonGrid count={6} />
      ) : (
        <>
          {/* 2. Key Metrics Overview Cards */}
          <StatCards
            totalEvents={totalEvents}
            domainCount={domains.length}
            sourceCount={sourceCount}
          />

          {/* 3. Domain Categories Grid Section */}
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="headline text-2xl flex items-center gap-2">
                  <Layers className="w-5 h-5 accent-mark" />
                  <span>Domain Intelligence Breakdown</span>
                </h2>
                <p className="body-copy text-sm">
                  Select a category to filter current affairs events
                </p>
              </div>

              <Link
                href="/explore"
                className="text-xs font-mono text-[var(--brand-primary)] flex items-center gap-1 font-semibold"
              >
                <span>View All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <DomainGrid domains={domains} />
          </section>

          {/* 4. Latest Current Affairs Section */}
          <section className="space-y-4 pt-2">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="headline text-2xl flex items-center gap-2">
                  <Compass className="w-5 h-5 accent-mark" />
                  <span>Latest Current Affairs</span>
                </h2>
                <p className="body-copy text-sm">
                  Recently indexed current affairs events across all permitted feeds
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={fetchDashboardData}
                  className="control p-2 text-[var(--text-secondary)] hover:text-[var(--brand-primary)]"
                  title="Refresh Latest Events"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>

                <Link
                  href="/explore"
                  className="text-xs font-mono text-[var(--brand-primary)] flex items-center gap-1 font-semibold"
                >
                  <span>Explore Explorer</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <EventList
              events={events}
              emptyTitle="No current affairs have been indexed yet."
              emptyDescription="No events exist in the database. Ingest permitted RSS feeds or check backend connection."
              onRetry={fetchDashboardData}
            />
          </section>
        </>
      )}
    </div>
  );
}
