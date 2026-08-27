export interface ApiResponse<T> {
  data?: T;
  error?: string;
  loading?: boolean;
}

export interface QueryParams {
  domain?: string;
  date?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
  [key: string]: string | number | boolean | undefined;
}
