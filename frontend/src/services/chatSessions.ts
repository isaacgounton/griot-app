/**
 * Chat Sessions API Service
 * Handles CRUD operations for chat sessions and messages
 */

import { directApi } from '../utils/api';

export interface ChatSession {
    session_id: string;
    user_id?: string;
    model_id: string;
    provider: string;
    created_at: string;
    updated_at?: string;
    title?: string;
    description?: string;
    settings?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    tool_calls?: Array<{
        id: string;
        type: string;
        function: {
            name: string;
            arguments: string;
        };
    }>;
    metadata?: Record<string, unknown>;
    created_at: string;
    token_count?: number;
    [key: string]: unknown;
}

export interface CreateChatSessionRequest {
    model_id?: string;
    provider?: string;
    title?: string;
    settings?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface UpdateChatSessionRequest {
    title?: string;
    settings?: Record<string, unknown>;
    messages?: Array<{
        role: 'user' | 'assistant' | 'system' | 'tool';
        content: string;
        [key: string]: unknown;
    }>;
    [key: string]: unknown;
}

export interface GenerateTitleRequest {
    message: string;
    model_id?: string;
    provider?: string;
    [key: string]: unknown;
}

export interface GenerateTitleResponse {
    title: string;
    session_id: string;
}

class ChatSessionsService {
    private baseUrl = '/api/v1/chat/sessions';

    /**
     * Create a new chat session
     */
    async createSession(request: CreateChatSessionRequest = {}): Promise<ChatSession> {
        const response = await directApi.post(this.baseUrl, request);
        return response.data as ChatSession;
    }

    /**
     * List all chat sessions for the current user
     */
    async listSessions(): Promise<ChatSession[]> {
        const response = await directApi.get(this.baseUrl);
        const data = response.data as { sessions?: ChatSession[] };
        return data.sessions || [];
    }

    /**
     * Get a specific chat session by ID
     */
    async getSession(sessionId: string): Promise<ChatSession> {
        const response = await directApi.get(`${this.baseUrl}/${sessionId}`);
        return response.data as ChatSession;
    }

    /**
     * Get messages for a chat session
     */
    async getMessages(sessionId: string): Promise<ChatMessage[]> {
        const response = await directApi.get(`${this.baseUrl}/${sessionId}/messages`);
        const data = response.data as { messages?: ChatMessage[] };
        return data.messages || [];
    }

    /**
     * Update a chat session
     */
    async updateSession(sessionId: string, request: UpdateChatSessionRequest): Promise<void> {
        await directApi.put(`${this.baseUrl}/${sessionId}`, request);
    }

    /**
     * Delete a chat session
     */
    async deleteSession(sessionId: string): Promise<void> {
        await directApi.delete(`${this.baseUrl}/${sessionId}`);
    }

    /**
     * Generate an AI-based title for a chat session
     */
    async generateTitle(request: GenerateTitleRequest): Promise<string> {
        const response = await directApi.post(
            `${this.baseUrl}/generate-title`,
            request as Record<string, unknown>
        );
        const data = response.data as GenerateTitleResponse;
        return data.title;
    }
}

export const chatSessionsService = new ChatSessionsService();
