import React from 'react';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface ImageGenerationParams extends Record<string, unknown> {
  prompt: string;
  model?: string;
  width?: number;
  height?: number;
  steps?: number;
  provider?: string;
  seed?: number;
  negative_prompt?: string;
}

export interface OverlayImage {
  url: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  rotation?: number;
  opacity?: number;
  z_index?: number;
}

export interface ImageEditParams extends Record<string, unknown> {
  base_image_url: string;
  overlay_images: OverlayImage[];
  output_format?: string;
  output_quality?: number;
  output_width?: number;
  output_height?: number;
  maintain_aspect_ratio?: boolean;
  stitch_mode?: boolean;
  stitch_direction?: string;
  stitch_spacing?: number;
  stitch_max_width?: number;
  stitch_max_height?: number;
}

export interface PollinationsEditParams {
  prompt: string;
  model: string;
  negative_prompt?: string;
  seed?: number;
}

export interface ImageEnhancementParams extends Record<string, unknown> {
  image_url: string;
  enhance_color?: number;
  enhance_contrast?: number;
  noise_strength?: number;
  remove_artifacts?: boolean;
  add_film_grain?: boolean;
  vintage_effect?: number;
  output_format?: string;
  output_quality?: number;
}

export interface JobResult {
  job_id: string;
  status: string;
  result?: {
    image_url?: string;
    content_url?: string;
    original_image_url?: string;
    edited_image_url?: string;
    prompt_used?: string;
    model_used?: string;
    dimensions?: { width: number; height: number };
    processing_time?: number;
    width?: number;
    height?: number;
    format?: string;
    storage_path?: string;
    content_type?: string;
    file_size?: number;
    generation_time?: number;
    images?: Array<{
      id: string;
      url: string;
      download_url: string;
      width: number;
      height: number;
      photographer?: string;
      photographer_url?: string;
      alt?: string;
      tags?: string;
      source: string;
      aspect_ratio: number;
    }>;
    total_results?: number;
    page?: number;
    per_page?: number;
    query_used?: string;
    provider_used?: string;
  };
  error?: string | null;
}

/** Shared state/callbacks that each tab component receives from the parent. */
export interface TabContext {
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  result: JobResult | null;
  setResult: React.Dispatch<React.SetStateAction<JobResult | null>>;
  jobStatus: 'pending' | 'processing' | 'completed' | 'failed' | null;
  setJobStatus: React.Dispatch<React.SetStateAction<'pending' | 'processing' | 'completed' | 'failed' | null>>;
  jobProgress: string;
  setJobProgress: React.Dispatch<React.SetStateAction<string>>;
  pollingJobId: string | null;
  setPollingJobId: React.Dispatch<React.SetStateAction<string | null>>;
  previewDialog: boolean;
  setPreviewDialog: React.Dispatch<React.SetStateAction<boolean>>;
  pollJobStatus: (jobId: string) => void;
  pollJobStatusPollinations: (jobId: string) => void;
  renderJobResult: (tabIndex: number, result: JobResult | null, icon: React.ReactNode) => React.ReactNode;
}

export const presetDimensions = [
  { label: 'Square (1:1)', width: 1024, height: 1024 },
  { label: 'Portrait (2:3)', width: 768, height: 1152 },
  { label: 'Landscape (3:2)', width: 1152, height: 768 },
  { label: 'Wide (16:9)', width: 1024, height: 576 },
  { label: 'Tall (9:16)', width: 576, height: 1024 },
  { label: 'Banner (4:1)', width: 1024, height: 256 },
  { label: 'Classic (4:3)', width: 1024, height: 768 },
  { label: 'Photo (3:4)', width: 768, height: 1024 },
  { label: 'HD (16:10)', width: 1024, height: 640 },
  { label: 'Ultra Wide (21:9)', width: 1024, height: 439 }
];

export const FALLBACK_EDIT_MODELS = [
  { id: 'kontext', name: 'Kontext \u2014 In-context editing' },
];
