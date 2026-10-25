import { api } from "@/lib/api";

export interface ScoreHistoryPoint {
  attempt_id: string;
  test_id: string;
  exam_name: string;
  score: number;
  accuracy: number;
  total_answered: number;
  total_questions: number;
  time_taken_seconds: number;
  submitted_at: string;
}

export interface SubjectPerformance {
  subject: string;
  total_questions: number;
  correct_count: number;
  accuracy: number;
}

export interface StudyRecommendation {
  subject: string;
  topic: string;
  reason: string;
  action: string;
  priority: "high" | "medium" | "normal";
}

export interface PerformanceAnalytics {
  total_tests_completed: number;
  total_questions_attempted: number;
  overall_accuracy: number;
  average_score: number;
  total_correct: number;
  total_incorrect: number;
  total_unanswered: number;
  average_time_per_question_seconds: number;
  revision_pending_count: number;
  strong_topics: string[];
  weak_topics: string[];
  scores_over_time: ScoreHistoryPoint[];
  subject_performance: SubjectPerformance[];
  recommendations: StudyRecommendation[];
}

export async function fetchPerformanceAnalytics(): Promise<PerformanceAnalytics> {
  return api.get<PerformanceAnalytics>("/api/v1/analytics/performance");
}
