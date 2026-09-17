export interface Event {
  id: number;
  title: string;
  summary: string;
  domain: string;
  event_date: string;
  published_at: string;
  source_id: number;
  source_url: string;
  source: string;
  url: string;
  event_type?: string;
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

// Exam Intelligence Types
export interface ExamRelevance {
  exam_id: string;
  exam_name: string;
  exam_code: string;
  relevance_score: number;
  section: string;
  reasons: string[];
}

export interface EventExamIntelligence {
  event_id: number;
  title?: string;
  domain?: string;
  relevant_exams: ExamRelevance[];
  key_points: string[];
}

export interface MCQOption {
  label: string;
  text: string;
}

export interface MCQ {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  event_id: number;
}

export interface MCQResponse {
  event_id: number;
  mcqs: MCQ[];
  provider: string;
  used_fallback?: boolean;
  error?: string;
}

export interface ExamEvent {
  event: Event;
  relevance_score: number;
  section: string;
  reasons: string[];
}

export interface ExamEventsResponse {
  exam_id: string;
  exam_name: string;
  total: number;
  limit: number;
  offset: number;
  events: ExamEvent[];
}
