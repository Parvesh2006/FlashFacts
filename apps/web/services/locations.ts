import { api } from "@/lib/api";
import type {
  GeographicLocation,
  EventLocationResponse,
  EventTimelineResponse,
  SourceCoverageResponse,
} from "@/types/location";

export async function fetchLocations(parentId?: number): Promise<GeographicLocation[]> {
  const params = parentId ? { parent_id: parentId } : undefined;
  return api.get<GeographicLocation[]>("/api/v1/locations", params);
}

export async function fetchLocationTree(): Promise<GeographicLocation[]> {
  return api.get<GeographicLocation[]>("/api/v1/locations/tree");
}

export async function fetchEventLocations(eventId: number): Promise<EventLocationResponse> {
  return api.get<EventLocationResponse>(`/api/v1/events/${eventId}/location`);
}

export async function fetchEventTimeline(eventId: number): Promise<EventTimelineResponse> {
  return api.get<EventTimelineResponse>(`/api/v1/events/${eventId}/timeline`);
}

export async function fetchSourceCoverage(): Promise<SourceCoverageResponse> {
  return api.get<SourceCoverageResponse>("/api/v1/coverage");
}

