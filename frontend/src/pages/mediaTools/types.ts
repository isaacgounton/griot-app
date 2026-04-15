import React from 'react';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface MediaMetadata {
  filesize?: number;
  filesize_mb?: number;
  duration?: number;
  duration_formatted?: string;
  format?: string;
  overall_bitrate?: number;
  overall_bitrate_mbps?: number;
  has_video?: boolean;
  has_audio?: boolean;
  video_codec?: string;
  video_codec_long?: string;
  width?: number;
  height?: number;
  resolution?: string;
  fps?: number;
  video_bitrate?: number;
  video_bitrate_mbps?: number;
  pixel_format?: string;
  audio_codec?: string;
  audio_codec_long?: string;
  audio_channels?: number;
  audio_sample_rate?: number;
  audio_sample_rate_khz?: number;
  audio_bitrate?: number;
  audio_bitrate_kbps?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface SupportedFormats {
  [category: string]: {
    [format: string]: {
      codec?: string;
      description?: string;
    };
  };
}

export interface JobResult {
  job_id: string;
  status?: string;
  result?: {
    file_url?: string;
    supported_formats?: SupportedFormats;
    metadata?: MediaMetadata;
    transcript?: string;
    [key: string]: string | number | boolean | SupportedFormats | MediaMetadata | undefined;
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
  supportedFormats: {
    supported_formats?: SupportedFormats;
    quality_presets?: string[];
    total_formats?: number;
  } | null;
}
