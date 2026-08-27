export interface CalendarDayStat {
  date: string; // YYYY-MM-DD
  total: number;
  domains: Record<string, number>;
}

export interface CalendarResponse {
  month: string; // YYYY-MM
  days: CalendarDayStat[];
}
