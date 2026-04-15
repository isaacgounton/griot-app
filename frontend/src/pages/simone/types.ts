import React from 'react';
import { JobStatus } from '../../types/griot';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface TopicData {
  topic: string;
  confidence: number;
  category: string;
  extracted_from: string;
  relevance_score?: number;
  key_points?: string[];
}

export interface ThreadPost {
  post_number: number;
  content: string;
  character_count: number;
}

export interface ViralContentPackage {
  content: {
    topics?: {
      topics: TopicData[];
    };
    x_thread?: {
      thread: ThreadPost[];
    };
    posts: {
      x?: string;
      linkedin?: string;
      instagram?: string;
      facebook?: string;
    };
  };
}

export interface JobResult {
  job_id: string;
  status?: string;
  result?: {
    blog_post_content?: string;
    blog_post_url?: string;
    screenshots?: string[];
    social_media_post_content?: string;
    transcription_content?: string;
    transcription_url?: string;
    viral_content_package?: ViralContentPackage;
    content_package_url?: string;
    enhanced_features?: {
      topics_included: boolean;
      x_thread_included: boolean;
      platforms_processed: string[];
      thread_config: {
        max_posts: number;
        character_limit: number;
        thread_style: string;
      };
    };
    processing_summary?: {
      total_topics?: number;
      thread_posts?: number;
      platforms_generated?: string[];
      screenshots_count?: number;
    };
    // YouTube Shorts specific fields
    url?: string;
    path?: string;
    duration?: number;
    original_title?: string;
    original_duration?: number;
    highlight_start?: number;
    highlight_end?: number;
    is_vertical?: boolean;
    ai_generated?: boolean;
    quality?: string;
    thumbnail_url?: string;
    processing_stats?: {
      download_size?: number;
      audio_extracted?: boolean;
      transcription_segments?: number;
      ai_highlight_detected?: boolean;
      highlight_extracted?: boolean;
      dynamic_crop_applied?: boolean;
      optimized_for_shorts?: boolean;
      thumbnail_created?: boolean;
      uploaded_to_s3?: boolean;
    };
    quality_check?: {
      file_size?: number;
      duration?: number;
      resolution?: string;
      bitrate?: number;
      av_sync?: boolean;
      has_audio?: boolean;
      has_video?: boolean;
    };
    features_used?: {
      speaker_tracking?: boolean;
      audio_enhancement?: boolean;
      smooth_transitions?: boolean;
      dynamic_cropping?: boolean;
    };
    [key: string]: string | number | boolean | string[] | ViralContentPackage | object | undefined;
  };
  error?: string | null;
}

export interface SelectedJobForScheduling {
  id: string;
  job_id: string;
  operation: string;
  status: JobStatus;
  result: {
    scheduling: {
      available: boolean;
      content_type: string;
      suggested_content: string;
    };
    [key: string]: unknown;
  };
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
  handleScheduleClick: (toolName: string, result: JobResult) => void;
}
