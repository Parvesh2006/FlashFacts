import { api } from "@/lib/api";
import type {
  EventExamIntelligence,
  ExamEventsResponse,
  MCQResponse,
} from "@/types/event";

export interface ExamCategory {
export interface Exam {
  id: string;
  name: string;
  code: string;
  description: string;
  iconName: string;
  category: string;
}

export const EXAM_CATEGORIES: ExamCategory[] = [
  {
    id: "tnpsc",
    name: "TNPSC",
    code: "TNPSC",
    description: "Tamil Nadu Public Service Commission Examinations",
    iconName: "Building2",
  },
  {
    id: "upsc",
    name: "UPSC",
    code: "UPSC",
    description: "Union Public Service Commission Civil Services & Defense",
    iconName: "Landmark",
  },
  {
    id: "ssc",
    name: "SSC",
    code: "SSC",
    description: "Staff Selection Commission CGL, CHSL, & Officers",
    iconName: "GraduationCap",
  },
  {
    id: "banking",
    name: "Banking",
    code: "BANK",
    description: "IBPS, SBI PO, Clerk & RBI Assistant Examinations",
    iconName: "Coins",
  },
  {
    id: "rrb",
    name: "RRB",
    code: "RRB",
    description: "Railway Recruitment Board NTPC & Technical Cadres",
    iconName: "TrainTrack",
  },
];

export async function fetchExams(): Promise<ExamCategory[]> {
export async function fetchExams(): Promise<Exam[]> {
  try {
    const exams = await api.get<ExamCategory[]>("/api/v1/exams");

    return exams;
    return await api.get<Exam[]>("/api/v1/exams");
  } catch {
    return EXAM_CATEGORIES;
    return [];
  }
}

export async function fetchExamEvents(
  examId: string,
  options?: { limit?: number; offset?: number }
): Promise<ExamEventsResponse> {
  return api.get<ExamEventsResponse>(`/api/v1/exams/${examId}/events`, {
    limit: options?.limit ?? 20,
    offset: options?.offset ?? 0,
  });
}

export async function fetchEventExamRelevance(
  eventId: number
): Promise<EventExamIntelligence> {
  return api.get<EventExamIntelligence>(
    `/api/v1/events/${eventId}/exam-relevance`
  );
}

export async function fetchEventMCQ(
  eventId: number,
  examId?: string,
  count?: number
): Promise<MCQResponse> {
  const params: Record<string, string | number | boolean | undefined> = {};
  if (examId) params.exam_id = examId;
  if (count) params.count = count;
  return api.get<MCQResponse>(`/api/v1/events/${eventId}/mcq`, params);
}