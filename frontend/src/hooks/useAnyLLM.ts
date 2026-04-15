/**
 * React hooks for AnyLLM integration
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Provider, Model, Message } from '../types/anyllm';
import { anyllm, LLMConfig, CompletionOptions } from '../services/anyllm';

export interface UseAnyLLMOptions {
  autoInitialize?: boolean;
  defaultProvider?: string;
  defaultModel?: string;
  defaultTemperature?: number;
}

export interface UseAnyLLMReturn {
  // State
  providers: Provider[];
  models: Model[];
  loading: boolean;
  error: string | null;
  initialized: boolean;

  // Current config
  currentProvider: string | null;
  currentModel: string | null;

  // Actions
  initialize: () => Promise<void>;
  setProvider: (provider: string) => Promise<void>;
  setModel: (model: string) => void;
  complete: (prompt: string, options?: CompletionOptions) => Promise<string>;
  chat: (messages: Message[], options?: CompletionOptions) => Promise<string>;
  clearError: () => void;
  refreshModels: () => Promise<void>;
}

/**
 * Main hook for AnyLLM integration
 */
export const useAnyLLM = (options: UseAnyLLMOptions = {}): UseAnyLLMReturn => {
  const {
    autoInitialize = true,
    defaultProvider,
    defaultModel,
    defaultTemperature = 0.7
  } = options;

  // State
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [currentProvider, setCurrentProvider] = useState<string | null>(defaultProvider || null);
  const [currentModel, setCurrentModel] = useState<string | null>(defaultModel || null);

  // Initialize
  const initialize = useCallback(async () => {
    if (initialized) return;

    try {
      setLoading(true);
      setError(null);

      await anyllm.initialize();
      const providerList = await anyllm.getProviders();
      setProviders(providerList);

      // Auto-select first provider if none specified
      if (!currentProvider && providerList.length > 0) {
        const provider = defaultProvider || providerList[0].name;
        setCurrentProvider(provider);

        // Load models for the provider
        const modelList = await anyllm.getModels(provider);
        setModels(modelList);

        // Auto-select first model if none specified
        if (!currentModel && modelList.length > 0) {
          const model = defaultModel || modelList[0].id;
          setCurrentModel(model);
        }
      }

      setInitialized(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize AnyLLM');
    } finally {
      setLoading(false);
    }
  }, [initialized, currentProvider, currentModel, defaultProvider, defaultModel]);

  // Set provider and load models
  const setProvider = useCallback(async (provider: string) => {
    try {
      setLoading(true);
      setError(null);

      const modelList = await anyllm.getModels(provider);
      setModels(modelList);
      setCurrentProvider(provider);

      // Reset model selection
      setCurrentModel(null);

      // Auto-select first model if available
      if (modelList.length > 0) {
        setCurrentModel(modelList[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setLoading(false);
    }
  }, []);

  // Set model
  const setModel = useCallback((model: string) => {
    setCurrentModel(model);
  }, []);

  // Complete text
  const complete = useCallback(async (prompt: string, options: CompletionOptions = {}) => {
    if (!currentProvider || !currentModel) {
      throw new Error('Provider and model must be selected');
    }

    return anyllm.completeWithProvider(currentProvider, currentModel, prompt, {
      temperature: defaultTemperature,
      ...options
    });
  }, [currentProvider, currentModel, defaultTemperature]);

  // Chat with messages
  const chat = useCallback(async (messages: Message[], options: CompletionOptions = {}) => {
    if (!currentProvider || !currentModel) {
      throw new Error('Provider and model must be selected');
    }

    return anyllm.chatWithProvider({
      provider: currentProvider,
      model: currentModel,
      messages,
      temperature: defaultTemperature,
    }, options);
  }, [currentProvider, currentModel, defaultTemperature]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Refresh models
  const refreshModels = useCallback(async () => {
    if (!currentProvider) return;

    try {
      setLoading(true);
      anyllm.clearCache();
      const modelList = await anyllm.getModels(currentProvider);
      setModels(modelList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh models');
    } finally {
      setLoading(false);
    }
  }, [currentProvider]);

  // Auto-initialize
  useEffect(() => {
    if (autoInitialize) {
      initialize();
    }
  }, [autoInitialize, initialize]);

  return {
    providers,
    models,
    loading,
    error,
    initialized,
    currentProvider,
    currentModel,
    initialize,
    setProvider,
    setModel,
    complete,
    chat,
    clearError,
    refreshModels
  };
};

/**
 * Simple hook for quick text completion
 */
export const useAnyLLMComplete = (config?: LLMConfig) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const complete = useCallback(async (prompt: string, options?: CompletionOptions) => {
    try {
      setLoading(true);
      setError(null);

      const result = await anyllm.complete(prompt, {
        ...config,
        ...options
      });

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Completion failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [config]);

  return { complete, loading, error, clearError: () => setError(null) };
};

/**
 * Hook for chat conversations
 */
export const useAnyLLMChat = (config?: LLMConfig) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string, options?: CompletionOptions) => {
    try {
      setLoading(true);
      setError(null);

      const userMessage: Message = { role: 'user', content };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);

      let assistantContent = '';

      const result = await anyllm.chat(newMessages, {
        ...config,
        ...options,
        onChunk: (chunk) => {
          const content = chunk.choices[0]?.delta?.content || '';
          assistantContent += content;
          setMessages(prev => [
            ...prev.slice(0, -1),
            { role: 'assistant', content: assistantContent }
          ]);
        },
        onStart: () => {
          setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
        }
      });

      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: result }
      ]);

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chat failed';
      setError(errorMessage);

      // Remove the empty assistant message on error
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.role === 'assistant' && !lastMessage.content) {
          return prev.slice(0, -1);
        }
        return prev;
      });

      throw err;
    } finally {
      setLoading(false);
    }
  }, [messages, config]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearMessages();
    setLoading(false);
    setError(null);
  }, [clearMessages]);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
    reset,
    clearError: () => setError(null)
  };
};