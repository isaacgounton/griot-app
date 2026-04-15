import React from 'react';
import { VoiceInfo } from '../../types/contentCreation';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface JobResult {
  job_id: string;
  status?: string;
  result?: {
    final_video_url?: string;
    video_url?: string;
    video_with_audio_url?: string;
    output_url?: string;
    url?: string;
    clip_urls?: string[];
    clips?: Array<{ url: string; name?: string }>;
    audio_url?: string;
    srt_url?: string;
    thumbnail_url?: string;
    duration?: number;
    duration_seconds?: number;
    resolution?: string;
    processing_time?: number;
    processing_time_seconds?: number;
    file_size?: number;
    file_size_mb?: number;
    word_count?: number;
    segments_count?: number;
    text?: string;
    model_used?: string;
    generation_time?: number;
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
  // eslint-disable-next-line no-unused-vars
  pollJobStatus: (...args: [string, string]) => void;
  // eslint-disable-next-line no-unused-vars
  renderJobResult: (...args: [string, JobResult | null, React.ReactNode]) => React.ReactNode;
  voices: VoiceInfo[];
}
