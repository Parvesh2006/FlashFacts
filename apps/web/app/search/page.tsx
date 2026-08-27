"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search as SearchIcon, Filter, Layers } from "lucide-react";
import { searchEvents, SearchResult } from "@/services/search";
import { getEvents } from "@/services/events";
import { EventList } from "@/components/events/event-list";
import { SkeletonGrid } from "@/components/common/skeleton-loader";
import { Event } from "@/types/event";
import { BackButton } from "@/components/navigation/back-button";

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [allEvents, setAllEvents] = useState<Event[]>([]);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch initial pool of events for fallback client-side searching
  useEffect(() => {
    getEvents({ limit: 100 })
      .then((res) => setAllEvents(res.events || []))
      .catch(() => setAllEvents([]));
  }, []);

  // Perform search whenever query or event pool updates
  useEffect(() => {
    if (!query.trim()) {
      setSearchResult(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    searchEvents(query, allEvents)
      .then((res) => setSearchResult(res))
      .finally(() => setLoading(false));
  }, [query, allEvents]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <BackButton fallbackHref="/" />

      {/* Search Header */}
      <div className="border-b pb-4">
        <div className="eyebrow flex items-center gap-2 mb-1">
          <SearchIcon className="w-4 h-4" />
          <span>Keyword Intelligence Search</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">
          Search Current Affairs
        </h1>
        <p className="body-copy text-sm">
          Query indexed news titles, summaries, and domain classifications.
        </p>
      </div>

      <form onSubmit={handleSearchSubmit} className="editorial-card p-4">
        <div className="relative flex flex-col sm:block">
          <SearchIcon className="absolute left-4 w-5 h-5 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Type keywords (e.g. 'Artificial Intelligence', 'Summit', 'Budget')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="control-input w-full pl-12 pr-4 sm:pr-28 py-3 text-sm font-mono focus:outline-none focus:border-[var(--brand-primary)]"
          />
          <button
            type="submit"
            className="brand-button mt-2 w-full px-4 py-2 text-xs font-mono font-semibold sm:absolute sm:right-2 sm:top-1/2 sm:mt-0 sm:w-auto sm:-translate-y-1/2"
            aria-label="Submit search"
          >
            Search
          </button>
        </div>
        <div className="mt-2 flex flex-col gap-1 meta-text sm:flex-row sm:items-center sm:justify-between">
          <span>Search Engine: Keyword Exact Match Architecture</span>
          <span>Future Endpoint: GET /api/v1/search?q=</span>
        </div>
      </form>

      {/* Search Results Display */}
      {loading ? (
        <SkeletonGrid count={6} />
      ) : searchResult ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b pb-2 meta-text">
            <span className="flex items-center gap-1.5 text-[var(--text-primary)]">
              <Filter className="w-3.5 h-3.5 accent-mark" />
              Found <strong className="text-[var(--brand-primary)]">{searchResult.total}</strong> events for query &ldquo;{searchResult.query}&rdquo;
            </span>
          </div>

          <EventList
            events={searchResult.events}
            emptyTitle={`No results matching "${searchResult.query}"`}
            emptyDescription="Try searching for alternate keywords or check spelling."
          />
        </div>
      ) : (
        <div className="editorial-card p-8 text-center">
          <Layers className="w-10 h-10 mx-auto text-[var(--text-muted)] mb-3" />
          <p className="text-sm font-mono text-[var(--text-primary)] mb-1">Enter a query above to search current affairs events.</p>
          <p className="meta-text">Search checks titles, summaries, and domain labels in real time.</p>
        </div>
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
