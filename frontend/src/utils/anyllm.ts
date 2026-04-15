import { Provider, Model, StreamChunk, CompletionRequest } from '../types/anyllm';
import { apiClient } from './api';

// Helper function to get auth headers from apiClient
const getAuthHeaders = () => {
  // Get the API key from localStorage (same key used by apiClient)
  const apiKey = localStorage.getItem('griot_api_key');
  return {
    'Content-Type': 'application/json',
    ...(apiKey && { 'X-API-Key': apiKey })
  };
};

const API_BASE = '/api/v1/anyllm';

export async function fetchProviders(): Promise<Provider[]> {
  const response = await apiClient.get(`${API_BASE}/providers`);
  return response.data.providers;
}

export async function fetchDefaultProvider(): Promise<string> {
  const response = await apiClient.get(`${API_BASE}/providers`);
  return response.data.default_provider || 'deepseek';
}

export async function fetchModels(provider: string): Promise<Model[]> {
  try {
    const response = await apiClient.post(`${API_BASE}/list-models`, {
      provider,
    });
    return response.data.models;
  } catch (error: unknown) {
    console.error(`Failed to fetch models for provider ${provider}:`, error);

    // Handle structured error responses from backend
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: unknown; status?: number } };
      if (axiosError.response?.data) {
        const errorData = axiosError.response.data as { error?: string; message?: string; provider?: string; suggestion?: string };

        switch (errorData.error) {
          case 'API_KEY_MISSING':
            throw new Error(`${errorData.message} ${errorData.suggestion || ''}`);

          case 'INVALID_API_KEY':
            throw new Error(`${errorData.message} Please check your ${errorData.provider?.toUpperCase()}_API_KEY environment variable.`);

          case 'PROVIDER_NOT_SUPPORTED':
            throw new Error(`${errorData.message} Available providers: openai, anthropic, groq, etc.`);

          default:
            throw new Error(errorData.message || `Failed to fetch models for ${provider}`);
        }
      }

      // Handle HTTP status codes
      if (axiosError.response?.status === 400) {
        throw new Error(`Bad request for provider ${provider}. This might be due to a missing API key or unsupported provider.`);
      }

      if (axiosError.response?.status === 401) {
        throw new Error(`Authentication failed for provider ${provider}. Please check your API key.`);
      }

      if (axiosError.response?.status === 500) {
        throw new Error(`Server error while fetching models for ${provider}. Please try again later.`);
      }
    }

    // Generic error
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to fetch models for provider ${provider}: ${errorMessage}`);
  }
}

export async function createStreamingCompletion(
  request: CompletionRequest,
  onChunk: (chunk: StreamChunk) => void,
  onComplete: () => void,
  onError?: (error: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/completions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      // Handle HTTP errors
      const errorText = await response.text();
      let errorData;

      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { message: errorText };
      }

      // Handle structured error responses from backend
      if (errorData.error) {
        switch (errorData.error) {
          case 'API_KEY_MISSING':
            onError?.(`${errorData.message} ${errorData.suggestion || ''}`);
            return;

          case 'INVALID_API_KEY':
            onError?.(`${errorData.message} Please check your ${errorData.provider.toUpperCase()}_API_KEY environment variable.`);
            return;

          case 'MODEL_NOT_FOUND':
            onError?.(`${errorData.message} Please check the model name and try again.`);
            return;

          case 'SERVER_ERROR':
            onError?.(`${errorData.message} Please try again later.`);
            return;

          default:
            onError?.(errorData.message || `Failed to create completion for ${request.provider}`);
            return;
        }
      }

      // Handle HTTP status codes
      if (response.status === 400) {
        onError?.(`Bad request for provider ${request.provider}. This might be due to a missing API key, unsupported model, or invalid parameters.`);
        return;
      }

      if (response.status === 401) {
        onError?.(`Authentication failed for provider ${request.provider}. Please check your API key.`);
        return;
      }

      if (response.status === 500) {
        onError?.(`Server error while creating completion for ${request.provider}. Please try again later.`);
        return;
      }

      onError?.(`HTTP ${response.status}: ${errorData.message || 'Unknown error'}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get response reader');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue; // Skip empty lines

          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            if (data === '[DONE]') {
              onComplete();
              return;
            }

            if (data) {
              try {
                const parsedChunk = JSON.parse(data);
                if (parsedChunk.error) {
                  onError?.(parsedChunk.error);
                  return;
                }
                onChunk(parsedChunk as StreamChunk);
              } catch (e) {
                console.warn('Failed to parse chunk:', data, 'Error:', e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error: unknown) {
    console.error('Streaming completion error:', error);

    // Handle network errors, CORS issues, etc.
    if (error instanceof TypeError && error.message.includes('fetch')) {
      onError?.('Network error: Unable to connect to the server. Please check your connection and try again.');
      return;
    }

    // Generic error
    const errorMessage = error instanceof Error ? error.message : 'Streaming failed';
    onError?.(errorMessage);
  }
}