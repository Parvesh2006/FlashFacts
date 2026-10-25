import { api } from "@/lib/api";

export interface RevisionItem {
  id: string;
  question_source: string;
  question_id?: number;
  mock_test_id?: string;
  exam_name: string;
  subject?: string;
  topic?: string;
  question_text: string;
  options: string[];
  selected_answer?: string;
  correct_answer: string;
  explanation?: string;
  outcome: string;
  mistake_count: number;
  is_revised: boolean;
  next_review_at?: string;
  last_reviewed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RetryRevisionResult {
  id: string;
  is_correct: boolean;
  selected_letter?: string;
  correct_letter: string;
  mistake_count: number;
  is_revised: boolean;
  next_review_at?: string;
  explanation?: string;
}

export interface RevisionSummary {
  total_count: number;
  pending_count: number;
  revised_count: number;
  exams: string[];
  subjects: string[];
}

export async function fetchRevisionItems(params?: {
  exam_name?: string;
  subject?: string;
  status?: "all" | "pending" | "revised";
  limit?: number;
  offset?: number;
}): Promise<RevisionItem[]> {
  return api.get<RevisionItem[]>("/api/v1/revision/", params);
}

export async function fetchRevisionSummary(): Promise<RevisionSummary> {
  return api.get<RevisionSummary>("/api/v1/revision/summary");
}

export async function retryRevisionQuestion(
  itemId: string,
  selectedAnswer: string
): Promise<RetryRevisionResult> {
  return api.post<RetryRevisionResult>(`/api/v1/revision/${itemId}/retry`, {
    selected_answer: selectedAnswer,
  });
}

export async function updateRevisionStatus(
  itemId: string,
  isRevised: boolean
): Promise<RevisionItem> {
  return api.patch<RevisionItem>(`/api/v1/revision/${itemId}/status`, {
    is_revised: isRevised,
  });
}

export async function deleteRevisionItem(itemId: string): Promise<void> {
  return api.delete<void>(`/api/v1/revision/${itemId}`);
}

export async function saveQuestionToMistakeBook(payload: {
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation?: string;
  exam_name?: string;
  subject?: string;
  topic?: string;
  selected_answer?: string;
}): Promise<RevisionItem> {
  return api.post<RevisionItem>("/api/v1/revision/save", payload);
}
