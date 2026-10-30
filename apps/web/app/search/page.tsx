"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search as SearchIcon, Filter, Layers, X, Sparkles, Calendar, BookOpen } from "lucide-react";
import { searchEvents, SearchResult } from "@/services/search";
import { getEvents } from "@/services/events";
import { EventList } from "@/components/events/event-list";
import { SkeletonGrid } from "@/components/common/skeleton-loader";
import { EmptyState } from "@/components/common/empty-state";
import { EmptySearchIllustration } from "@/components/illustrations/educational-illustrations";
import { Event } from "@/types/event";
import { BackButton } from "@/components/navigation/back-button";

const POPULAR_SEARCHES = [
  "Constitution",
  "Tamil Nadu Schemes",
  "Monetary Policy",
  "Chandrayaan",
  "Union Budget",
  "Election Commission",
  "G20 / Global Summits",
  "Science & Tech",
];

const DOMAINS = [
  "All Domains",
  "Polity",
  "Economy",
  "Science",
  "Technology",
  "AI",
  "Government",
  "International",
  "Sports",
];

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [allEvents, setAllEvents] = useState<Event[]>([]);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [domain, setDomain] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Sync state if URL query param changes
  useEffect(() => {
    if (initialQuery !== query) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  // Fetch initial pool of events for fallback client-side searching
  useEffect(() => {
    getEvents({ limit: 100 })
      .then((res) => setAllEvents(res.events || []))
      .catch(() => setAllEvents([]));
  }, []);

  // Perform search whenever query or event pool updates
  useEffect(() => {
    const hasFilters = Boolean(domain || startDate || endDate);
    if (!query.trim() && !hasFilters) {
      setSearchResult(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const filters = {
      domain: domain === "All Domains" || !domain ? undefined : domain,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    };
    const resultPromise = query.trim()
      ? searchEvents(query, allEvents, filters)
      : getEvents({ ...filters, limit: 100 }).then((res) => ({
          events: res.events || [],
          query: "",
          total: res.total || 0,
        }));

    resultPromise
      .then((res) => setSearchResult(res))
      .finally(() => setLoading(false));
  }, [query, allEvents, domain, startDate, endDate]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleChipClick = (term: string) => {
    setQuery(term);
    router.push(`/search?q=${encodeURIComponent(term)}`);
  };

  const handleClearFilters = () => {
    setQuery("");
    setDomain("");
    setStartDate("");
    setEndDate("");
    router.push("/search");
  };

  const hasActiveFilters = Boolean(query || domain || startDate || endDate);

  return (
    <div className="space-y-6 max-w-5xl mx-auto page-enter">
      <BackButton fallbackHref="/" />

      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] pb-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge-editorial text-xs text-[var(--accent)] border-[var(--accent)] font-semibold">
            ARCHIVE SEARCH
          </span>
          <span className="text-xs text-[var(--text-muted)]">• Verified Syllabus Engine</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl text-[var(--text-primary)] font-bold tracking-tight">
          Current Affairs Intelligence Search
        </h1>
        <p className="body-copy text-sm text-[var(--text-secondary)] mt-1.5 max-w-2xl">
          Instantly query verified exam news, policy developments, constitutional updates, and historical exam questions across TNPSC, UPSC, SSC, and RRB.
        </p>
      </div>

      {/* Main Search Panel */}
      <div className="editorial-card p-5 md:p-6 shadow-xs border border-[var(--border)]">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="relative flex items-center">
            <SearchIcon className="absolute left-4 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
            <input
              type="text"
              placeholder="Search by keywords, policies, committees, acts, or locations..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-12 pr-28 py-3.5 text-sm rounded-xl bg-[var(--surface-muted)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:bg-[var(--surface)] transition-all font-sans"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="absolute right-24 text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1 rounded-md"
                aria-label="Clear query"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <button
              type="submit"
              className="button-base button-primary absolute right-2 px-4 py-2 text-xs font-semibold"
              aria-label="Submit search"
            >
              Search
            </button>
          </div>

          {/* Quick Syllabus Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[var(--accent)]" /> Popular:
            </span>
            {POPULAR_SEARCHES.map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => handleChipClick(term)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                  query === term
                    ? "bg-[var(--accent)] text-white border-[var(--accent)] font-medium"
                    : "bg-[var(--surface)] text-[var(--text-secondary)] border-[var(--border)] hover:border-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                {term}
              </button>
            ))}
          </div>

          {/* Filter Bar: Domain & Dates */}
          <div className="pt-3 border-t border-[var(--border)] grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Domain Classification
              </label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                aria-label="Filter by domain"
              >
                {DOMAINS.map((d) => (
                  <option key={d} value={d === "All Domains" ? "" : d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                From Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                aria-label="Filter from date"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                To Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                aria-label="Filter through date"
              />
            </div>
          </div>

          {hasActiveFilters && (
            <div className="flex items-center justify-between pt-1">
              <span className="text-xs text-[var(--text-muted)]">
                Active query parameters applied
              </span>
              <button
                type="button"
                onClick={handleClearFilters}
                className="text-xs text-[var(--accent)] hover:underline font-medium inline-flex items-center gap-1"
              >
                <X className="w-3.5 h-3.5" /> Reset all filters
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Search Results Display */}
      {loading ? (
        <SkeletonGrid count={6} />
      ) : searchResult ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
            <span className="flex items-center gap-2 text-sm text-[var(--text-primary)]">
              <Filter className="w-4 h-4 text-[var(--accent)]" />
              Found <strong className="font-bold text-[var(--accent)]">{searchResult.total}</strong> verified items matching{" "}
              {searchResult.query ? (
                <span>&ldquo;<strong className="text-[var(--text-primary)]">{searchResult.query}</strong>&rdquo;</span>
              ) : (
                "selected filters"
              )}
            </span>
            <span className="text-xs text-[var(--text-muted)] font-mono">
              Live Index
            </span>
          </div>

          <EventList
            events={searchResult.events}
            emptyTitle={`No events found for "${searchResult.query || "selected filters"}"`}
            emptyDescription="Try broadening your search term, checking alternate spellings, or clearing date constraints."
          />
        </div>
      ) : (
        <EmptyState
          illustration={<EmptySearchIllustration size={110} />}
          title="Search the Intelligence Archive"
          description="Type keywords, policies, committees, or constitutional amendments above to explore our comprehensive exam current affairs database."
        />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SkeletonGrid count={6} />}>
      <SearchContent />
    </Suspense>
  );
}
