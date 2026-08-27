import { api } from "@/lib/api";
import { Event, EventFilter, EventListResponse } from "@/types/event";

export async function getEvents(filter?: EventFilter): Promise<EventListResponse> {
  return api.get<EventListResponse>("/api/v1/events", filter as Record<string, string | number | boolean | undefined>);
}

export async function getEvent(id: number | string): Promise<Event> {
  return api.get<Event>(`/api/v1/events/${id}`);
}
