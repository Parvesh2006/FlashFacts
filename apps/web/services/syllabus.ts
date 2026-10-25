import { api } from "@/lib/api";

export interface SyllabusTopic {
  id: number;
  exam_name: string;
  subject: string;
  unit_number?: number;
  unit_name: string;
  topic_name: string;
  subtopics?: string[];
  order_index: number;
  status: "not_started" | "in_progress" | "completed" | "needs_revision";
  notes?: string;
  last_studied_at?: string;
}

export interface SyllabusUnitGroup {
  unit_number?: number;
  unit_name: string;
  subject: string;
  topics: SyllabusTopic[];
  completed_count: number;
  total_count: number;
  completion_percentage: number;
}

export interface SyllabusSubjectGroup {
  subject: string;
  units: SyllabusUnitGroup[];
  completed_count: number;
  total_count: number;
  completion_percentage: number;
}

export interface ExamSyllabus {
  exam_name: string;
  overall_completion_percentage: number;
  total_topics: number;
  completed_topics: number;
  in_progress_topics: number;
  needs_revision_topics: number;
  subjects: SyllabusSubjectGroup[];
}

export interface TopicProgressResult {
  topic_id: number;
  status: string;
  notes?: string;
  last_studied_at?: string;
  message: string;
}

export async function fetchExamSyllabus(examName: string): Promise<ExamSyllabus> {
  return api.get<ExamSyllabus>(`/api/v1/syllabus/${encodeURIComponent(examName)}`);
}

export async function updateTopicProgress(payload: {
  topic_id: number;
  status: "not_started" | "in_progress" | "completed" | "needs_revision";
  notes?: string;
}): Promise<TopicProgressResult> {
  return api.post<TopicProgressResult>("/api/v1/syllabus/progress", payload);
}
