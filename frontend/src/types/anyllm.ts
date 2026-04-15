export interface Provider {
  name: string;
  display_name: string;
}

export interface Model {
  id: string;
  object: string;
  created?: number;
  owned_by?: string;
  parameter_info?: ModelParameterInfo;
}

export interface ModelParameterInfo {
  max_tokens_param: string;
  supports_reasoning: boolean;
  unsupported_params: string[];
  recommended_defaults: {
    temperature?: number;
    top_p?: number;
    max_tokens: number;
  };
}

export interface MessageContent {
  type: 'text' | 'image' | 'audio' | 'video';
  text?: string;
  url?: string;
  alt_text?: string;
  filename?: string;
  size?: number;
  mime_type?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string; // JSON string
  };
}

export interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: MessageContent[] | string;
  thinking?: string;
  model?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string; // for role: 'tool' messages
}

export interface StreamChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: {
    index: number;
    delta: {
      content?: string;
      thinking?: string;
      tool_calls?: {
        index: number;
        id?: string;
        type?: string;
        function?: {
          name?: string;
          arguments?: string;
        };
      }[];
    };
    finish_reason: string | null;
  }[];
}

export interface CompletionRequest {
  provider: string;
  model: string;
  messages: Message[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  response_format?: Record<string, any>;
  stream?: boolean;
  n?: number;
  stop?: string | string[];
  presence_penalty?: number;
  frequency_penalty?: number;
  seed?: number;
  user?: string;
  tools?: Record<string, any>[];
  tool_choice?: string | Record<string, any>;
  parallel_tool_calls?: boolean;
  logprobs?: boolean;
  top_logprobs?: number;
  logit_bias?: Record<string, number>;
  max_completion_tokens?: number;
  reasoning_effort?: 'minimal' | 'low' | 'medium' | 'high' | 'auto';
}

export interface CompletionSettings {
  temperature: number;
  top_p: number;
  max_tokens: number;
  presence_penalty: number;
  frequency_penalty: number;
  reasoning_effort?: 'minimal' | 'low' | 'medium' | 'high' | 'auto';
}
