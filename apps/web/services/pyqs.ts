import { api } from "@/lib/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PYQ {
  id: number;
  exam_name: string;
  year: number;
  paper_name?: string;
  subject?: string;
  topic?: string;
  source?: string;
  language: string;
  is_verified: boolean;
  question_type?: "verified_pyq" | "syllabus_practice" | "current_affairs" | "invalid" | string;
  quality_status?: "valid" | "invalid" | "needs_review" | string;
  rejection_reason?: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation?: string;
  is_bookmarked: boolean;
  created_at: string;
  updated_at: string;
}

export interface PYQFilters {
  exams: string[];
  years: number[];
  subjects: string[];
  topics: string[];
  total_count: number;
}

export interface PYQBookmarkResult {
  pyq_id: number;
  bookmarked: boolean;
  message: string;
}

export interface PYQPaper {
  id: string;
  exam_name: string;
  exam_category: string;
  year: number;
  exam_date?: string;
  subject: string;
  language: string;
  shift_session?: string;
  paper_code?: string;
  title: string;
  source_url: string;
  pdf_url?: string;
  authority: string;
  checksum_sha256?: string;
  verification_status: string;
  redistribution_status: string;
  file_size_bytes?: number;
  mime_type: string;
  availability_status: string;
  download_count: number;
  has_local_file: boolean;
  last_verified_at?: string;
  source_status?: string;
  created_at: string;
  updated_at: string;
}

export interface PYQPaperListResponse {
  items: PYQPaper[];
  total: number;
  limit: number;
  offset: number;
}

export interface PYQPaperFilterOptions {
  categories: string[];
  exams: string[];
  years: number[];
  subjects: string[];
  languages: string[];
  availability_statuses?: string[];
}

export async function fetchPYQs(params?: {
  exam_name?: string;
  year?: number;
  subject?: string;
  topic?: string;
  type?: string;
  include_invalid?: boolean;
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<PYQ[]> {
  return api.get<PYQ[]>("/api/v1/pyqs/", params);
}

export async function fetchPYQFilters(exam_name?: string): Promise<PYQFilters> {
  return api.get<PYQFilters>("/api/v1/pyqs/filters", { exam_name });
}

export async function fetchPYQBookmarks(limit = 100, offset = 0): Promise<PYQ[]> {
  return api.get<PYQ[]>("/api/v1/pyqs/bookmarks", { limit, offset });
}

export async function togglePYQBookmark(pyqId: number): Promise<PYQBookmarkResult> {
  return api.post<PYQBookmarkResult>(`/api/v1/pyqs/${pyqId}/bookmark`);
}

// =========================================================================
// PYQ PAPERS (Official PDF Question Paper Archive)
// =========================================================================

export async function fetchPYQPapers(params?: {
  category?: string;
  exam_name?: string;
  year?: number;
  subject?: string;
  language?: string;
  availability?: string;
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<PYQPaperListResponse> {
  return api.get<PYQPaperListResponse>("/api/v1/pyqs/papers", params);
}

export async function fetchPYQPaperFilters(): Promise<PYQPaperFilterOptions> {
  return api.get<PYQPaperFilterOptions>("/api/v1/pyqs/papers/filters");
}

export async function fetchPYQPaperById(paperId: string): Promise<PYQPaper> {
  return api.get<PYQPaper>(`/api/v1/pyqs/papers/${paperId}`);
}

export function getPYQPaperPdfUrl(paperId: string): string {
  return `${BASE_URL}/api/v1/pyqs/papers/${paperId}/pdf`;
}

export function getPYQPaperDownloadUrl(paperId: string): string {
  return `${BASE_URL}/api/v1/pyqs/papers/${paperId}/download`;
}
