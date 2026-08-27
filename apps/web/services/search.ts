import { api } from "@/lib/api";
import { Event } from "@/types/event";

export interface SearchResult {
  events: Event[];
  query: string;
  total: number;
}

export async function searchEvents(query: string, loadedEvents?: Event[]): Promise<SearchResult> {
  const cleanQuery = query.trim().toLowerCase();
  if (!cleanQuery) {
    return { events: [], query, total: 0 };
  }

  // Attempt backend endpoint if available, fallback to client-side filtering
  try {
    const data = await api.get<{ events: Event[]; total: number }>("/api/v1/search", { q: query });
    return {
      events: data.events || [],
      query,
      total: data.total || 0,
    };
  } catch {
    // Client-side fallback search across loaded events
    if (loadedEvents && loadedEvents.length > 0) {
      const filtered = loadedEvents.filter(
        (e) =>
          e.title.toLowerCase().includes(cleanQuery) ||
          e.summary.toLowerCase().includes(cleanQuery) ||
          e.domain.toLowerCase().includes(cleanQuery)
      );
      return {
        events: filtered,
        query,
        total: filtered.length,
      };
    }
    
    // Default empty search response if no backend search endpoint & no loaded events passed
    return {
      events: [],
      query,
      total: 0,
    };
  }
}
