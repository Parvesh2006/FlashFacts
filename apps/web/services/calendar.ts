import { api } from "@/lib/api";
import { CalendarResponse } from "@/types/calendar";

export async function getCalendar(month: string): Promise<CalendarResponse> {
  return api.get<CalendarResponse>("/api/v1/calendar", { month });
}
