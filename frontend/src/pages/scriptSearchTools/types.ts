import React from 'react';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface JobResult {
  job_id: string;
  status?: string;
  result?: {
    script?: string;
    script_content?: string;
    final_video_url?: string;
    video_url?: string;
    search_queries?: string[];
    // New query format from video search API
    queries?: Array<{
      query: string;
      start_time: number;
      end_time: number;
      duration: number;
      visual_concept?: string;
    }>;
    total_duration?: number;
    total_segments?: number;
    videos?: Array<{
      id: string;
      url: string;
      image: string;
      duration: number;
      width: number;
      height: number;
      user: { name: string };
    }>;
    // Enhanced articles structure for news research
    articles?: Array<{
      title: string;
      description?: string;
      snippet?: string;
      content?: string;
      url?: string;
      link?: string;
      source: string;
      publishedAt?: string;
      date?: string;
      provider?: string;
      model_used?: string;
      research_type?: string;
      search_result?: boolean;
    }>;
    // Enhanced news research fields
    summary?: string;
    sources?: string[];
    sources_used?: string[];
    total_sources?: number;
    research_date?: string;
    content?: string;
    // Video search result fields
    query_used?: string;
    provider_used?: string;
    total_results?: number;
    page?: number;
    per_page?: number;
    // Stock image results
    images?: Array<Record<string, unknown>>;
    // Web search results
    results?: Array<Record<string, unknown>>;
    query?: unknown;
    engine?: unknown;
    search_time?: unknown;
    [key: string]: unknown;
  };
  error?: string | null;
}

/** Shared state/callbacks that each tab component receives from the parent. */
export interface TabContext {
  loading: Record<string, boolean>;
  setLoading: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  errors: Record<string, string | null>;
  setErrors: React.Dispatch<React.SetStateAction<Record<string, string | null>>>;
  results: Record<string, JobResult | null>;
  setResults: React.Dispatch<React.SetStateAction<Record<string, JobResult | null>>>;
  jobStatuses: Record<string, string>;
  pollJobStatus: (jobId: string, toolName: string) => void;
  renderJobResult: (toolName: string, result: JobResult | null, icon: React.ReactNode) => React.ReactNode;
}
