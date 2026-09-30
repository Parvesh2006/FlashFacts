import { api } from "@/lib/api";
import type {
  EventExamIntelligence,
  ExamEventsResponse,
  MCQResponse,
} from "@/types/event";

export interface Exam {
  id: string;
  name: string;
  code: string;
  description: string;
  category: string;
  iconName?: string;
}

export type ExamCategory = Exam;

export const EXAM_FALLBACKS: Exam[] = [
  {
    id: "tnpsc-group-4",
    name: "TNPSC Group 4",
    code: "TNPSC-G4",
    description: "Tamil Nadu Public Service Commission Group 4 examination.",
    category: "tnpsc",
    iconName: "Building2",
  },
  {
    id: "tnpsc-group-2",
    name: "TNPSC Group 2",
    code: "TNPSC-G2",
    description: "Tamil Nadu Public Service Commission Group 2 examination.",
    category: "tnpsc",
    iconName: "Building2",
  },
  {
    id: "ssc-cgl",
    name: "SSC CGL",
    code: "SSC-CGL",
    description: "Staff Selection Commission Combined Graduate Level examination.",
    category: "ssc",
    iconName: "GraduationCap",
  },
  {
    id: "ssc-chsl",
    name: "SSC CHSL",
    code: "SSC-CHSL",
    description: "Staff Selection Commission Combined Higher Secondary Level examination.",
    category: "ssc",
    iconName: "GraduationCap",
  },
  {
    id: "upsc-cse",
    name: "UPSC Civil Services",
    code: "UPSC-CSE",
    description: "Union Public Service Commission Civil Services examination.",
    category: "upsc",
    iconName: "Landmark",
  },
  {
    id: "rrb-ntpc",
    name: "RRB NTPC",
    code: "RRB-NTPC",
    description: "Railway Recruitment Board Non-Technical Popular Categories examination.",
    category: "rrb",
    iconName: "TrainTrack",
  },
  {
    id: "banking",
    name: "Banking",
    code: "BANK",
    description: "Competitive banking examinations including IBPS and SBI.",
    category: "banking",
    iconName: "Coins",
  },
];

export async function fetchExams(): Promise<Exam[]> {
  try {
    return await api.get<Exam[]>("/api/v1/exams");
  } catch {
    return EXAM_FALLBACKS;
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
