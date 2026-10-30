import { api } from "@/lib/api";

export interface SourceItem {
  name: string;
  url?: string | null;
  date?: string | null;
}

export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface AskResponse {
  answer: string;
  filters?: Record<string, any>;
  sources?: (SourceItem | string)[];
  events_found?: number;
  provider?: string;
}

export async function askQuestion(
  question: string,
  history?: ChatHistoryItem[]
): Promise<AskResponse> {
  const payload: { question: string; history?: ChatHistoryItem[] } = { question };
  if (history && history.length > 0) {
    payload.history = history;
  }
  return await api.post<AskResponse>("/api/v1/ask", payload);
}
