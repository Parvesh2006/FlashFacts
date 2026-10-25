import { api } from "@/lib/api";

export interface MockTestSummary {
  id: string;
  exam_name: string;
  domain?: string;
  language: string;
  difficulty: string;
  total_questions: number;
  time_limit_minutes: number;
  negative_marking: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface MockTestQuestion {
  id: number;
  question_order: number;
  is_pyq: boolean;
  pyq_id?: number;
  event_id?: number;
  question_text: string;
  options: string[];
}

export interface MockTestDetails {
  id: string;
  exam_name: string;
  domain?: string;
  language: string;
  difficulty: string;
  total_questions: number;
  time_limit_minutes: number;
  negative_marking: number;
  status: string;
  created_at: string;
  updated_at: string;
  questions: MockTestQuestion[];
}

export interface MockTestAnswerReview {
  question_id: number;
  question_order: number;
  question_text: string;
  options: string[];
  selected_answer?: string;
  correct_answer: string;
  is_correct: boolean;
  explanation?: string;
}

export interface MockTestAttemptResult {
  id: string;
  test_id: string;
  user_id?: string;
  score: number;
  accuracy: number;
  total_answered: number;
  incorrect_count: number;
  unanswered_count: number;
  time_taken_seconds: number;
  is_submitted: boolean;
  submitted_at: string;
  review: MockTestAnswerReview[];
}

export interface MockTestAttemptSummary {
  id: string;
  test_id: string;
  exam_name: string;
  score: number;
  accuracy: number;
  total_answered: number;
  total_questions: number;
  time_taken_seconds: number;
  submitted_at: string;
}

export async function fetchMockTests(params?: {
  exam_name?: string;
  domain?: string;
  limit?: number;
  offset?: number;
}): Promise<MockTestSummary[]> {
  return api.get<MockTestSummary[]>("/api/v1/mock-tests/", params);
}

export async function fetchMockTest(testId: string): Promise<MockTestDetails> {
  return api.get<MockTestDetails>(`/api/v1/mock-tests/${testId}`);
}

export async function createMockTest(payload: {
  exam_name: string;
  domain?: string;
  difficulty?: string;
  total_questions?: number;
  time_limit_minutes?: number;
  negative_marking?: number;
  include_pyqs?: boolean;
  include_events?: boolean;
}): Promise<MockTestDetails> {
  return api.post<MockTestDetails>("/api/v1/mock-tests/", payload);
}

export async function submitMockTestAttempt(
  testId: string,
  payload: {
    answers: Record<string, string>;
    time_taken_seconds?: number;
    review_marked?: number[];
  }
): Promise<MockTestAttemptResult> {
  return api.post<MockTestAttemptResult>(`/api/v1/mock-tests/${testId}/attempts`, payload);
}

export async function fetchAttemptReview(
  testId: string,
  attemptId: string
): Promise<MockTestAttemptResult> {
  return api.get<MockTestAttemptResult>(`/api/v1/mock-tests/${testId}/attempts/${attemptId}`);
}

export async function fetchAttemptHistory(limit = 50, offset = 0): Promise<MockTestAttemptSummary[]> {
  return api.get<MockTestAttemptSummary[]>("/api/v1/mock-tests/attempts", { limit, offset });
}
