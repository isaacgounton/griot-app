import React from 'react';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface DocumentResult {
  markdown_content: string;
  original_filename: string;
  file_type: string;
  word_count: number;
  character_count: number;
  processing_time: number;
}

export interface DocumentConversionResult {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: DocumentResult;
  error?: string | null;
}

export interface ExtractedEntity {
  text: string;
  value: string;
  sources: {
    start: number;
    end: number;
    text: string;
  }[];
  confidence_score?: number;
  attributes?: Record<string, string | number | boolean>;
  context?: string;
  type?: string;
  role?: string;
}

export interface LangextractResult {
  extracted_data: Record<string, ExtractedEntity[]>;
  total_extractions: number;
  processing_time: number;
  model_used: string;
  input_text_length: number;
  extraction_type?: string;
  source_grounding_enabled?: boolean;
  extraction_config?: {
    entity_types: string[];
    has_attributes: boolean;
    extraction_passes: number;
    max_workers: number;
    temperature: number;
  };
  quality_metrics?: {
    entities_with_attributes: number;
    average_confidence: number;
    unique_entity_types: number;
    processing_speed_chars_per_sec: number;
  };
}

export interface LangextractConversionResult {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: LangextractResult;
  error?: string | null;
}

/** Shared state/callbacks that each tab component receives from the parent. */
export interface TabContext {
  // Document conversion state
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  result: DocumentConversionResult | null;
  setResult: React.Dispatch<React.SetStateAction<DocumentConversionResult | null>>;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  jobStatus: 'pending' | 'processing' | 'completed' | 'failed' | null;
  setJobStatus: React.Dispatch<React.SetStateAction<'pending' | 'processing' | 'completed' | 'failed' | null>>;
  jobProgress: string;
  setJobProgress: React.Dispatch<React.SetStateAction<string>>;
  pollingJobId: string | null;
  setPollingJobId: React.Dispatch<React.SetStateAction<string | null>>;
  copied: boolean;
  setCopied: React.Dispatch<React.SetStateAction<boolean>>;

  // Extract state
  extractLoading: boolean;
  setExtractLoading: React.Dispatch<React.SetStateAction<boolean>>;
  extractResult: LangextractConversionResult | null;
  setExtractResult: React.Dispatch<React.SetStateAction<LangextractConversionResult | null>>;
  extractError: string | null;
  setExtractError: React.Dispatch<React.SetStateAction<string | null>>;
  extractJobStatus: 'pending' | 'processing' | 'completed' | 'failed' | null;
  setExtractJobStatus: React.Dispatch<React.SetStateAction<'pending' | 'processing' | 'completed' | 'failed' | null>>;
  extractJobProgress: string;
  setExtractJobProgress: React.Dispatch<React.SetStateAction<string>>;
  extractPollingJobId: string | null;
  setExtractPollingJobId: React.Dispatch<React.SetStateAction<string | null>>;

  // Shared helpers
  pollJobStatus: (jobId: string) => void;
  pollExtractJobStatus: (jobId: string) => void;
  copyToClipboard: (text: string) => void;
  downloadMarkdown: (content: string, filename: string) => void;
  getFileIcon: (filename?: string) => React.ReactNode;
}
