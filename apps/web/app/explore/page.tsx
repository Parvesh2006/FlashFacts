"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Compass, ChevronLeft, ChevronRight, SlidersHorizontal } from "lucide-react";
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
      setError(err instanceof Error ? err.message : "Failed to load events.");
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
    <div className="space-y-6">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <div className="eyebrow flex items-center gap-2 mb-1">
            <Compass className="w-4 h-4" />
            <span>Event Explorer</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl">
            Explore Current Affairs
          </h1>
          <p className="body-copy text-sm">
            Filter, search, and navigate current affairs events by category, date range, or keywords.
          </p>
        </div>

        <div className="soft-badge flex items-center gap-2 text-xs font-mono px-3 py-1.5">
          <SlidersHorizontal className="w-3.5 h-3.5 accent-mark" />
          <span>{total} Total Matched</span>
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
            emptyDescription="No events match your requested filter parameters."
            onRetry={fetchExploreEvents}
          />

        <div className="flex items-center gap-3">
          <label className="meta-text">Sort</label>
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              updateUrlParams({ sort: e.target.value, offset: 0 });
            }}
            className="control-input px-3 py-1.5 text-sm"
          >
            <option value="latest">Latest</option>
            <option value="important">Most Important</option>
          </select>
        </div>

          {/* Pagination Controls */}
          {total > limitParam && (
            <div className="flex items-center justify-between pt-4 border-t font-mono text-xs text-[var(--text-secondary)]">
              <span>
                Showing page {currentPage} of {totalPages} ({total} events)
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrevPage}
                  disabled={offsetParam === 0}
                  className="control flex items-center gap-1 px-3 py-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>

                <button
                  onClick={handleNextPage}
                  disabled={offsetParam + limitParam >= total}
                  className="control flex items-center gap-1 px-3 py-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
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
