export interface Source {
  id: number;
  name: string;
  url: string;
  feed_url: string;
  source_type: string;
  domain: string;
  reliability_score: number;
  enabled: boolean;
  last_fetched_at?: string;
  created_at: string;
  updated_at: string;
}
