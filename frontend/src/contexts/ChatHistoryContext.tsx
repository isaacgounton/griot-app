/**
 * Chat History Context
 * Manages chat sessions state across the application
 */

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { chatSessionsService, ChatSession, ChatMessage } from '../services/chatSessions';

interface ChatHistoryContextType {
    sessions: ChatSession[];
    currentSession: ChatSession | null;
    currentSessionMessages: ChatMessage[];
    loading: boolean;
    error: string | null;
    sidebarOpen: boolean;
    setSidebarOpen(open: boolean): void;
    loadSessions(): Promise<void>;
    createSession(modelId?: string, provider?: string, title?: string): Promise<ChatSession>;
    selectSession(sessionId: string): Promise<void>;
    updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<void>;
    deleteSession(sessionId: string): Promise<void>;
    loadSessionMessages(sessionId: string): Promise<ChatMessage[]>;
    createNewSession(): Promise<ChatSession>;
}

const ChatHistoryContext = createContext<ChatHistoryContextType | undefined>(undefined);

interface ChatHistoryProviderProps {
    children: ReactNode;
}

export function ChatHistoryProvider({ children }: ChatHistoryProviderProps) {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
    const [currentSessionMessages, setCurrentSessionMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Load sessions on mount (only if authenticated)
    useEffect(() => {
        const apiKey = localStorage.getItem('griot_api_key');
        if (apiKey) {
            loadSessions();
        }
    }, []);

    // Save sidebar state to localStorage
    useEffect(() => {
        const saved = localStorage.getItem('chat_history_sidebar_open');
        if (saved !== null) {
            setSidebarOpen(saved === 'true');
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('chat_history_sidebar_open', String(sidebarOpen));
    }, [sidebarOpen]);

    const loadSessions = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const loadedSessions = await chatSessionsService.listSessions();
            setSessions(loadedSessions);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load sessions';
            setError(message);
            console.error('Error loading chat sessions:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createSession = useCallback(async (modelId = 'deepseek-chat', provider = 'deepseek', title?: string) => {
        setError(null);
        try {
            const newSession = await chatSessionsService.createSession({
                model_id: modelId,
                provider,
                title,
            });
            setSessions(prev => [newSession, ...prev]);
            return newSession;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to create session';
            setError(message);
            console.error('Error creating chat session:', err);
            throw err;
        }
    }, []);

    const selectSession = useCallback(async (sessionId: string) => {
        setError(null);
        try {
            const session = await chatSessionsService.getSession(sessionId);
            setCurrentSession(session);
            await loadSessionMessages(sessionId);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load session';
            setError(message);
            console.error('Error loading chat session:', err);
            throw err;
        }
    }, []);

    const updateSession = useCallback(async (sessionId: string, updates: Partial<ChatSession>) => {
        setError(null);
        try {
            await chatSessionsService.updateSession(sessionId, updates);
            setSessions(prev =>
                prev.map(s => (s.session_id === sessionId ? { ...s, ...updates } : s))
            );
            if (currentSession?.session_id === sessionId) {
                setCurrentSession(prev => prev ? { ...prev, ...updates } : null);
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to update session';
            setError(message);
            console.error('Error updating chat session:', err);
            throw err;
        }
    }, [currentSession]);

    const deleteSession = useCallback(async (sessionId: string) => {
        setError(null);
        try {
            await chatSessionsService.deleteSession(sessionId);
            // Remove from local state immediately
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            // Clear current session if it was deleted
            if (currentSession?.session_id === sessionId) {
                setCurrentSession(null);
                setCurrentSessionMessages([]);
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to delete session';
            setError(message);
            console.error('Error deleting chat session:', err);
            throw err;
        }
    }, [currentSession]);

    const loadSessionMessages = useCallback(async (sessionId: string) => {
        setError(null);
        try {
            const messages = await chatSessionsService.getMessages(sessionId);
            setCurrentSessionMessages(messages);
            return messages;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load messages';
            setError(message);
            console.error('Error loading chat messages:', err);
            return [];
        }
    }, []);

    const createNewSession = useCallback(async (): Promise<ChatSession> => {
        const newSession = await createSession();
        setCurrentSession(newSession);
        setCurrentSessionMessages([]);
        return newSession;
    }, [createSession]);

    const value: ChatHistoryContextType = {
        sessions,
        currentSession,
        currentSessionMessages,
        loading,
        error,
        sidebarOpen,
        setSidebarOpen,
        loadSessions,
        createSession,
        selectSession,
        updateSession,
        deleteSession,
        loadSessionMessages,
        createNewSession,
    };

    return (
        <ChatHistoryContext.Provider value={value}>
            {children}
        </ChatHistoryContext.Provider>
    );
}

export function useChatHistory(): ChatHistoryContextType {
    const context = useContext(ChatHistoryContext);
    if (context === undefined) {
        throw new Error('useChatHistory must be used within a ChatHistoryProvider');
    }
    return context;
}
