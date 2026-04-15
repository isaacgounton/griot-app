export interface VideoAnalysisParams {
  video_url: string;
  question: string;
  model: string;
}

export interface TextGenerationParams {
  prompt: string;
  model: string;
  temperature: number;
  top_p: number;
  json_mode: boolean;
  system?: string;
  seed?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatCompletionParams {
  messages: ChatMessage[];
  model: string;
  temperature: number;
  top_p: number;
  json_mode: boolean;
  system?: string;
  seed?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
}

export interface SearchParams {
  query: string;
  model: string;
}

export interface ModelOption {
  name: string;
  label: string;
}

export interface ExamplePrompts {
  text: string[];
  vision: string[];
  chat: string[];
  search: string[];
}

export interface TextModelsResponse {
  text_models: Array<string | ModelObject>;
}

export interface ModelObject {
  name?: string;
  id?: string;
  model?: string;
}

export interface JobResult {
  job_id?: string;
  status?: string;
  result?: {
    text?: string;
    assistant_message?: string;
    model_used?: string;
    generation_time?: number;
    character_count?: number;
    message_count?: number;
    has_tool_calls?: boolean;
    response?: Record<string, unknown>;
    prompt?: string;
    content_url?: string;
  };
}

export type JobType = 'text' | 'chat' | 'search';
export type JobStatus = string | null;
