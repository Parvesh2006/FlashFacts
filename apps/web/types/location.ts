export interface GeographicLocation {
  id: number;
  name: string;
  normalized_name: string;
  location_type: string;
  parent_id?: number | null;
  country_code?: string;
  state_code?: string;
  district_code?: string;
  aliases?: string[];
  children?: GeographicLocation[];
}

export interface EventLocationRelation {
  id: number;
  name: string;
  location_type: string;
  relation_type: string;
  confidence: number;
}

export interface EventLocationResponse {
  event_id: number;
  locations: EventLocationRelation[];
}

export interface TimelineNode {
  event_id: number;
  title: string;
  event_date: string;
  position: "PRECEDING" | "CURRENT" | "SUBSEQUENT";
  relation_type: string;
}

export interface EventTimelineResponse {
  event_id: number;
  domain?: string;
  timeline: TimelineNode[];
}

export interface SourceCoverageResponse {
  total_sources: number;
  enabled_sources: number;
  total_reference_locations: number;
  events_with_geographic_mapping: number;
  coverage_breakdown: { level: string; count: number }[];
}

