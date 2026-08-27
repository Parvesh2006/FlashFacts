import { api } from "@/lib/api";

export interface AskResponse {
  answer: string;
  sources?: string[];
}

export async function askQuestion(question: string): Promise<AskResponse> {
  try {
    return await api.post<AskResponse>("/api/v1/ask", { question });
  } catch {
    // Phase 2 fallback response matching prompt instructions
    return {
      answer: "Ask FlashFacts AI is being connected to the intelligence engine.",
      sources: [],
    };
  }
}
