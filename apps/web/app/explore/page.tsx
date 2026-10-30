"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Compass, ChevronLeft, ChevronRight, SlidersHorizontal, ArrowUpDown } from "lucide-react";
import { EventFilters } from "@/components/events/event-filters";
import { EventList } from "@/components/events/event-list";
import { SkeletonGrid } from "@/components/common/skeleton-loader";
import { ErrorState } from "@/components/common/error-state";
import { getEvents } from "@/services/events";
import { getDomains } from "@/services/domains";
import { Event } from "@/types/event";
import { DomainStat } from "@/types/domain";
import { BackButton } from "@/components/navigation/back-button";

function ExploreContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const domainParam = searchParams.get("domain") || undefined;
  const dateParam = searchParams.get("date") || undefined;
  const startDateParam = searchParams.get("start_date") || undefined;
  const endDateParam = searchParams.get("end_date") || undefined;
  const limitParam = Number(searchParams.get("limit")) || 24;
  const offsetParam = Number(searchParams.get("offset")) || 0;

  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [domains, setDomains] = useState<DomainStat[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<string>(searchParams.get("sort") || "latest");

  // Fetch domain list for filter dropdown
  useEffect(() => {
    getDomains()
      .then(setDomains)
      .catch(() => setDomains([]));
  }, []);

  // Update URL Search Params helper
  const updateUrlParams = (newParams: Record<string, string | number | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "") {
        params.set(key, String(val));
      } else {
        params.delete(key);
      }
    });
    router.push(`/explore?${params.toString()}`);
  };

  const fetchExploreEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getEvents({
        domain: domainParam,
        date: dateParam,
        start_date: startDateParam,
        end_date: endDateParam,
        sort,
        limit: limitParam,
        offset: offsetParam,
      });

      setEvents(res.events || []);
      setTotal(res.total || 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load events from server.");
    } finally {
      setLoading(false);
    }
  }, [domainParam, dateParam, startDateParam, endDateParam, sort, limitParam, offsetParam]);

  useEffect(() => {
    fetchExploreEvents();
  }, [fetchExploreEvents]);

  // Pagination Handlers
  const currentPage = Math.floor(offsetParam / limitParam) + 1;
  const totalPages = Math.ceil(total / limitParam) || 1;

  const handlePrevPage = () => {
    if (offsetParam >= limitParam) {
      updateUrlParams({ offset: offsetParam - limitParam });
    }
  };

  const handleNextPage = () => {
    if (offsetParam + limitParam < total) {
      updateUrlParams({ offset: offsetParam + limitParam });
    }
  };

  const handleResetFilters = () => {
    router.push("/explore");
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto page-enter">
      <BackButton fallbackHref="/" />

      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
              INTELLIGENCE ARCHIVE
            </span>
            <span className="text-xs text-[var(--text-muted)]">• Comprehensive Feed</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
            Explore Current Affairs
          </h1>
          <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-2xl">
            Browse through classified exam intelligence records with domain filtering, exact dates, and importance sorting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="badge-editorial px-3 py-1.5 flex items-center gap-2 bg-[var(--surface-muted)] text-[var(--text-primary)] border-[var(--border)]">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[var(--accent)]" />
            <span className="font-semibold">{total}</span>
            <span className="text-[var(--text-muted)]">Verified Items</span>
          </div>

          <div className="flex items-center gap-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg px-2.5 py-1">
            <ArrowUpDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            <select
              value={sort}
              onChange={(e) => {
                setSort(e.target.value);
                updateUrlParams({ sort: e.target.value, offset: 0 });
              }}
              className="bg-transparent text-xs text-[var(--text-primary)] font-medium focus:outline-none cursor-pointer"
              aria-label="Sort events"
            >
              <option value="latest">Latest First</option>
              <option value="important">Most Exam-Relevant</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <EventFilters
        domains={domains}
        selectedDomain={domainParam}
        selectedDate={dateParam}
        startDate={startDateParam}
        endDate={endDateParam}
        limit={limitParam}
        onDomainChange={(domain) => updateUrlParams({ domain, offset: 0 })}
        onDateChange={(date) => updateUrlParams({ date, offset: 0 })}
        onDateRangeChange={(start_date, end_date) =>
          updateUrlParams({ start_date, end_date, offset: 0 })
        }
        onReset={handleResetFilters}
      />

      {/* Events Grid / Loading / Error */}
      {error ? (
        <ErrorState message={error} onRetry={fetchExploreEvents} />
      ) : loading ? (
        <SkeletonGrid count={9} />
      ) : (
        <div className="space-y-6">
          <EventList
            events={events}
            emptyTitle="No current affairs found"
            emptyDescription="No events match your requested filter parameters. Try clearing date constraints or choosing a different domain."
            onRetry={fetchExploreEvents}
          />

          {/* Pagination Controls */}
          {total > limitParam && (
            <div className="editorial-card p-4 flex flex-col sm:flex-row items-center justify-between gap-4 border border-[var(--border)]">
              <span className="text-xs text-[var(--text-secondary)] font-medium">
                Page <strong className="text-[var(--text-primary)]">{currentPage}</strong> of{" "}
                <strong className="text-[var(--text-primary)]">{totalPages}</strong> ({total} total entries)
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrevPage}
                  disabled={offsetParam === 0}
                  className="button-base button-secondary px-3 py-1.5 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>

                <button
                  onClick={handleNextPage}
                  disabled={offsetParam + limitParam >= total}
                  className="button-base button-secondary px-3 py-1.5 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ExplorePage() {
  return (
    <Suspense fallback={<SkeletonGrid count={6} />}>
      <ExploreContent />
    </Suspense>
  );
}
