export interface Agent {
    id: string;
    name: string;
    description: string;
    capabilities: string[];
    type?: 'agent' | 'team' | 'workflow';
    model?: string;
    owner?: string;
    version?: string;
    tags?: string[];
    rating?: number;
    usage_count?: number;
    last_used?: string;
    is_premium?: boolean;
    category?: string;
}

export interface ModelConfig {
    provider: string;
    model: string;
    temperature: number;
    top_p: number;
    top_k: number;
    max_tokens: number;
    stream: boolean;
}

export interface ToolCall {
    id: string;
    name: string;
    arguments: Record<string, any>;
    result?: any;
    start_time?: string;
    end_time?: string;
    duration?: number;
    status?: 'pending' | 'running' | 'completed' | 'failed';
    error?: string;
}

export interface MessageMetadata {
    model?: string;
    temperature?: number;
    top_p?: number;
    top_k?: number;
    max_tokens?: number;
    tokens_used?: number;
    cost?: number;
    latency?: number;
    tools_used?: string[];
    reasoning_time?: number;
    memory_used?: string;
    knowledge_base_used?: boolean;
    session_id?: string;
    user_id?: string;
}

export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
    id?: string;
    tool_calls?: ToolCall[];
    metadata?: MessageMetadata;
    reasoning?: string;
    tokens?: number;
    model?: string;
    temperature?: number;
    parent_id?: string;
    children_ids?: string[];
    edited?: boolean;
    deleted?: boolean;
    pinned?: boolean;
    bookmarked?: boolean;
}

export interface SessionSettings {
    provider: string;
    model: string;
    temperature: number;
    top_p: number;
    top_k: number;
    max_tokens: number;
    stream: boolean;
    memory_enabled: boolean;
    knowledge_base_enabled: boolean;
    reasoning_enabled: boolean;
    tool_metadata_enabled: boolean;
    theme: 'light' | 'dark' | 'auto';
    language: string;
    export_format: 'json' | 'markdown' | 'txt' | 'csv';
    auto_save: boolean;
    auto_title: boolean;
    smart_completions: boolean;
    voice_input: boolean;
    voice_output: boolean;
    sound_effects: boolean;
    notifications: boolean;
    privacy_mode: boolean;
    debug_mode: boolean;
    experimental_features: boolean;
}

export interface SessionMetadata {
    total_messages: number;
    total_tokens: number;
    total_cost: number;
    total_duration: number;
    average_response_time: number;
    success_rate: number;
    error_count: number;
    tools_used: string[];
    models_used: string[];
    languages_used: string[];
    topics_discussed: string[];
    sentiment_score?: number;
    engagement_score?: number;
    satisfaction_score?: number;
    provider?: string;
}

export interface Session {
    session_id: string;
    agent_type: string;
    user_id?: string;
    model_id: string;
    provider: string;
    created_at: string;
    updated_at?: string;
    status: string;
    title?: string;
    description?: string;
    messages?: Message[];
    settings?: SessionSettings;
    metadata?: SessionMetadata;
    archived?: boolean;
    pinned?: boolean;
    shared?: boolean;
    share_link?: string;
    tags?: string[];
    category?: string;
}

export interface MemorySettings {
    short_term_enabled: boolean;
    long_term_enabled: boolean;
    history_runs: number;
    memory_type: 'conversation' | 'semantic' | 'episodic' | 'procedural';
    retention_days: number;
    max_memories: number;
    auto_summarize: boolean;
    compression_ratio: number;
    indexing_method: 'keyword' | 'vector' | 'hybrid';
    search_method: 'exact' | 'fuzzy' | 'semantic' | 'hybrid';
    privacy_level: 'public' | 'private' | 'encrypted';
}

export interface KnowledgeDocument {
    id: string;
    knowledge_base_id: string;
    filename: string;
    content_type: string;
    size: number;
    status: string;
    metadata?: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

export interface KnowledgeBase {
    id: string;
    name: string;
    description?: string;
    document_count: number;
    size: number;
    enabled: boolean;
    chunk_size: number;
    chunk_overlap: number;
    embedding_model?: string;
    created_at: string;
    updated_at: string;
    documents?: KnowledgeDocument[];
}
