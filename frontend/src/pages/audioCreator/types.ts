import React from 'react';

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export interface Voice {
  id: string;
  name?: string;
  label?: string;
  language?: string;
  display_name?: string;
  description?: string;
  gender?: string;
  grade?: string;
  engine?: string;
  quality?: string;
  available?: boolean;
  downloaded?: boolean;
  [key: string]: unknown;
}

export interface VoicesData {
  [provider: string]: Voice[];
}

export interface ModelsData {
  models?: { [provider: string]: ModelItem[] };
}

export interface ProvidersData {
  providers?: string[];
  formats?: { [provider: string]: string[] };
  models?: { [provider: string]: ModelItem[] };
  default_provider?: string;
}

export interface ModelItem {
  id: string;
  name: string;
}

export interface TranscriptionSegment {
  start: number;
  end: number;
  text: string;
  confidence?: number;
}

export interface TranscriptionWord {
  word: string;
  start: number;
  end: number;
  probability: number;
}

export interface TTSJobResult {
  audio_url: string;
  tts_engine?: string;
  voice?: string;
  response_format?: string;
  estimated_duration?: number;
  word_count?: number;
  model_used?: string;
}

export interface MusicJobResult {
  audio_url: string;
  model_used?: string;
  estimated_duration?: number;
}

export interface TranscriptionJobResult {
  text?: string;
  srt_url?: string;
  segments?: TranscriptionSegment[];
  words?: TranscriptionWord[];
  duration?: number;
  language?: string;
  language_probability?: number;
  word_count?: number;
  estimated_duration?: number;
}

export type JobResult = TTSJobResult | MusicJobResult | TranscriptionJobResult;

export interface ApiResult {
  job_id: string;
  status?: string;
  jobResult?: JobResult;
  [key: string]: unknown;
}

/** Shared state/callbacks that each tab component receives from the parent. */
export interface TabContext {
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  result: ApiResult | null;
  setResult: React.Dispatch<React.SetStateAction<ApiResult | null>>;
  jobStatus: 'pending' | 'processing' | 'completed' | 'failed' | null;
  setJobStatus: React.Dispatch<React.SetStateAction<'pending' | 'processing' | 'completed' | 'failed' | null>>;
  jobProgress: string;
  setJobProgress: React.Dispatch<React.SetStateAction<string>>;
  pollingJobId: string | null;
  setPollingJobId: React.Dispatch<React.SetStateAction<string | null>>;
  pollJobStatus: (jobId: string) => void;
  renderJobResult: (tabIndex: number) => React.ReactNode;
  AudioPlayer: React.FC<{ audioUrl: string; title: string }>;
  voices: VoicesData;
  models: ModelsData;
  providers: ProvidersData;
  loadingVoices: boolean;
}
