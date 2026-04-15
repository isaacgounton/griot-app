/**
 * Universal AnyLLM Service - Can be used anywhere in the app
 */

import { Provider, Model, Message, StreamChunk, CompletionRequest } from '../types/anyllm';
import { fetchProviders, fetchDefaultProvider, fetchModels, createStreamingCompletion } from '../utils/anyllm';

export interface LLMConfig {
  provider?: string;
  model?: string;
  temperature?: number;
  apiKey?: string;
}

export interface CompletionOptions {
  // eslint-disable-next-line no-unused-vars
  onChunk?: (chunk: StreamChunk) => void;
  onComplete?: () => void;
  // eslint-disable-next-line no-unused-vars
  onError?: (error: string) => void;
  onStart?: () => void;
  signal?: AbortSignal;
}

class UniversalAnyLLMService {
  private static instance: UniversalAnyLLMService;
  private providers: Provider[] = [];
  private modelsCache: Map<string, Model[]> = new Map();
  private initialized: boolean = false;

  private constructor() {}

  static getInstance(): UniversalAnyLLMService {
    if (!UniversalAnyLLMService.instance) {
      UniversalAnyLLMService.instance = new UniversalAnyLLMService();
    }
    return UniversalAnyLLMService.instance;
  }

  /**
   * Initialize the service and load providers
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      this.providers = await fetchProviders();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize AnyLLM service:', error);
      throw error;
    }
  }

  /**
   * Get all available providers
   */
  async getProviders(): Promise<Provider[]> {
    if (!this.initialized) {
      await this.initialize();
    }
    return this.providers;
  }

  /**
   * Get the server-configured default provider
   */
  async getDefaultProvider(): Promise<string> {
    return fetchDefaultProvider();
  }

  /**
   * Get models for a specific provider (with caching)
   */
  async getModels(provider: string): Promise<Model[]> {
    if (!this.initialized) {
      await this.initialize();
    }

    // Check cache first
    if (this.modelsCache.has(provider)) {
      return this.modelsCache.get(provider)!;
    }

    try {
      const models = await fetchModels(provider);
      this.modelsCache.set(provider, models);
      return models;
    } catch (error) {
      console.error(`Failed to fetch models for provider ${provider}:`, error);
      throw error;
    }
  }

  /**
   * Simple completion with automatic provider/model selection
   */
  async complete(
    prompt: string,
    options: CompletionOptions & LLMConfig = {}
  ): Promise<string> {
    const {
      provider,
      model,
      temperature = 0.7,
      onChunk,
      onComplete,
      onError,
      onStart
    } = options;

    if (!provider || !model) {
      // Auto-select first available provider and model
      const providers = await this.getProviders();
      const selectedProvider = provider || providers[0]?.name;
      if (!selectedProvider) {
        throw new Error('No providers available');
      }

      const models = await this.getModels(selectedProvider);
      const selectedModel = model || models[0]?.id;
      if (!selectedModel) {
        throw new Error('No models available');
      }

      return this.completeWithProvider(selectedProvider, selectedModel, prompt, {
        temperature,
        onChunk,
        onComplete,
        onError,
        onStart
      });
    }

    return this.completeWithProvider(provider, model, prompt, {
      temperature,
      onChunk,
      onComplete,
      onError,
      onStart
    });
  }

  /**
   * Complete with specific provider and model
   */
  async completeWithProvider(
    provider: string,
    model: string,
    prompt: string,
    options: CompletionOptions & { temperature?: number } = {}
  ): Promise<string> {
    const { temperature = 0.7, onChunk, onComplete, onError, onStart } = options;

    const messages: Message[] = [{ role: 'user', content: prompt }];
    let fullResponse = '';

    onStart?.();

    const completionRequest: CompletionRequest = {
      provider,
      model,
      messages,
      temperature,
      stream: true
    };

    return new Promise((resolve, reject) => {
      createStreamingCompletion(
        completionRequest,
        (chunk) => {
          const content = chunk.choices[0]?.delta?.content || '';
          fullResponse += content;
          onChunk?.(chunk);
        },
        () => {
          onComplete?.();
          resolve(fullResponse);
        },
        (error) => {
          onError?.(error);
          reject(new Error(error));
        }
      );
    });
  }

  /**
   * Chat conversation with message history
   */
  async chat(
    messages: Message[],
    options: CompletionOptions & LLMConfig = {}
  ): Promise<string> {
    const {
      provider,
      model,
      temperature = 0.7,
      onChunk,
      onComplete,
      onError,
      onStart
    } = options;

    if (!provider || !model) {
      // Auto-select first available provider and model
      const providers = await this.getProviders();
      const selectedProvider = provider || providers[0]?.name;
      if (!selectedProvider) {
        throw new Error('No providers available');
      }

      const models = await this.getModels(selectedProvider);
      const selectedModel = model || models[0]?.id;
      if (!selectedModel) {
        throw new Error('No models available');
      }

      return this.chatWithProvider({
        provider: selectedProvider,
        model: selectedModel,
        messages,
        temperature,
      }, {
        onChunk,
        onComplete,
        onError,
        onStart
      });
    }

    return this.chatWithProvider({
      provider,
      model,
      messages,
      temperature,
    }, {
      onChunk,
      onComplete,
      onError,
      onStart
    });
  }

  /**
   * Chat with specific provider and model (new API with CompletionRequest)
   */
  async chatWithProvider(
    completionRequest: CompletionRequest,
    options: CompletionOptions = {}
  ): Promise<string> {
    const { onChunk, onComplete, onError, onStart, signal } = options;

    let fullResponse = '';

    onStart?.();

    // Ensure stream is enabled
    const requestWithStreaming = {
      ...completionRequest,
      stream: true
    };

    return new Promise((resolve, reject) => {
      createStreamingCompletion(
        requestWithStreaming,
        (chunk) => {
          const content = chunk.choices[0]?.delta?.content || '';
          fullResponse += content;
          onChunk?.(chunk);
        },
        () => {
          onComplete?.();
          resolve(fullResponse);
        },
        (error) => {
          onError?.(error);
          reject(new Error(error));
        },
        signal,
      );
    });
  }

  /**
   * Check if service is ready
   */
  isReady(): boolean {
    return this.initialized && this.providers.length > 0;
  }

  /**
   * Clear models cache (useful for refreshing models)
   */
  clearCache(): void {
    this.modelsCache.clear();
  }

  /**
   * Get recommended provider/model for general use
   */
  async getRecommendedConfig(): Promise<{ provider: string; model: string } | null> {
    try {
      const providers = await this.getProviders();
      if (providers.length === 0) return null;

      // Try to find OpenAI first, then use first available
      const openaiProvider = providers.find(p => p.name.includes('openai'));
      const selectedProvider = openaiProvider || providers[0];

      const models = await this.getModels(selectedProvider.name);
      if (models.length === 0) return null;

      // Try to find gpt-3.5-turbo or gpt-4, then use first available
      const recommendedModel = models.find(m =>
        m.id.includes('gpt-3.5-turbo') || m.id.includes('gpt-4')
      ) || models[0];

      return {
        provider: selectedProvider.name,
        model: recommendedModel.id
      };
    } catch (error) {
      console.error('Failed to get recommended config:', error);
      return null;
    }
  }
}

// Export singleton instance
export const anyllm = UniversalAnyLLMService.getInstance();

// Export convenience functions
export const completeText = (prompt: string, options?: CompletionOptions & LLMConfig) =>
  anyllm.complete(prompt, options);

export const chatWithLLM = (messages: Message[], options?: CompletionOptions & LLMConfig) =>
  anyllm.chat(messages, options);

export const getAvailableProviders = () => anyllm.getProviders();
export const getProviderModels = (provider: string) => anyllm.getModels(provider);
