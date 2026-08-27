export interface Event {
  id: number;
  title: string;
  summary: string;
  domain: string;
  event_date: string;
  published_at: string;
  source_id: number;
  source_url: string;
  confidence_score: number;
  dedup_hash: string;
  created_at: string;
  updated_at: string;

  // Phase 3A AI Enrichment
  why_it_matters?: string;
  importance_score?: number;
  classification_confidence?: number;
  ai_processed_at?: string;
  processing_status?: string;

  entities?: { id: number; name: string; entity_type: string }[];
  source_count?: number;
  sources?: import("./source").Source[];
}

export interface EventListResponse {
  total: number;
  limit: number;
  offset: number;
  events: Event[];
}

export interface EventFilter {
  domain?: string;
  date?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
  sort?: "latest" | "important" | string;
}
