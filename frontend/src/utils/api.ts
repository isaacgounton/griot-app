import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  MCPRequest,
  MCPResponse,
  Job,
  CreateVideoParams,
  FootageToVideoRequest,
  AiimageToVideoRequest,
  ApiResponse
} from '../types/griot';

// Use environment variable if set (production), otherwise use relative URL (development)
// Vite proxy (configured in vite.config.ts) will handle routing to backend in development
// IMPORTANT: Always use relative URLs to avoid mixed content errors in production
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Ensure HTTPS is used in production environments AND always use relative URLs for same-origin
const getApiBaseUrl = () => {
  // If no explicit base URL is set, always use relative URLs to avoid mixed content issues
  if (!import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL === '') {
    return '/api/v1';
  }

  // If an explicit base URL is provided, check protocol
  if (API_BASE_URL.startsWith('http://')) {
    // For HTTP URLs in HTTPS environment, we must convert to HTTPS
    if (window.location.protocol === 'https:') {
      return API_BASE_URL.replace('http://', 'https://');
    }
    // If same protocol, use as-is
    return API_BASE_URL;
  }

  // If it's already https:// or relative URL, return as-is
  return API_BASE_URL;
};

// Create axios instances for different base paths
export const apiClient: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  // Don't set Content-Type here - let axios handle it automatically
});

// Create axios instance for root-level API endpoints (auth, jobs, etc.)
export const rootApiClient: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
});

// Create axios instance for MCP endpoints
export const mcpApiClient: AxiosInstance = axios.create({
  baseURL: `${getApiBaseUrl().replace('/api/v1', '')}/mcp`,
  timeout: 30000,
});

// Note: Pollinations endpoints are available at /api/v1/pollinations/*
// Use the standard apiClient instead of a separate instance

// Create axios instance for auth endpoints (/api/v1/auth/*)
export const authApiClient: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
});

// Request interceptor to add API key and set content type for non-FormData requests
const setupRequestInterceptor = (client: AxiosInstance) => {
  client.interceptors.request.use(
    (config) => {
      // Ensure HTTPS is used when the page is loaded over HTTPS
      // This prevents mixed content errors
      if (config.url && config.url.startsWith('http://') && window.location.protocol === 'https:') {
        config.url = config.url.replace('http://', 'https://');
      }

      // Also check and fix the baseURL if it's http but we're on https
      if (config.baseURL && config.baseURL.startsWith('http://') && window.location.protocol === 'https:') {
        config.baseURL = config.baseURL.replace('http://', 'https://');
      }

      // Defensive: Strip /api/v1 prefix from URL if accidentally included
      // This prevents /api/v1/api/v1 duplication issues
      if (config.url && config.baseURL && config.baseURL.includes('/api/v1')) {
        config.url = config.url.replace(/^\/api\/v1/, '');
      }

      const apiKey = localStorage.getItem('griot_api_key');
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
      }

      // Set Content-Type to application/json only if it's not FormData
      if (config.data && !(config.data instanceof FormData) && !config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json';
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
};

// Setup request interceptors for all clients
setupRequestInterceptor(apiClient);
setupRequestInterceptor(rootApiClient);
setupRequestInterceptor(mcpApiClient);
// pollinationsApiClient removed - using standard apiClient
setupRequestInterceptor(authApiClient);

// Response interceptor for error handling
const setupResponseInterceptor = (client: AxiosInstance) => {
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        // 401 Unauthorized - Invalid or expired authentication
        // Clear stored credentials and redirect to login
        localStorage.removeItem('griot_api_key');
        localStorage.removeItem('griot_user_role');
        window.location.href = '/login';
      } else if (error.response?.status === 402) {
        // 402 Payment Required - User needs an active subscription
        // Redirect to payments page instead of logging out
        window.location.href = '/dashboard/payments';
      }
      // 403 Forbidden - User is authenticated but not allowed to access this resource
      // Don't logout, just let the component handle the error
      return Promise.reject(error);
    }
  );
};

// Setup response interceptors for all clients
setupResponseInterceptor(apiClient);
setupResponseInterceptor(rootApiClient);
setupResponseInterceptor(mcpApiClient);
// pollinationsApiClient removed - using standard apiClient
setupResponseInterceptor(authApiClient);

// Authentication API Functions
export const authApi = {
  // Login with username and password
  login: async (username: string, password: string): Promise<ApiResponse<{ api_key: string; message: string }>> => {
    try {
      const response = await authApiClient.post('/auth/login', { username, password });

      if (response.data && response.data.success) {
        // Store API key in localStorage
        localStorage.setItem('griot_api_key', response.data.api_key);

        return {
          success: true,
          data: {
            api_key: response.data.api_key,
            message: response.data.message
          }
        };
      }

      return {
        success: false,
        error: 'Login failed'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Login failed'
        : 'Login failed';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Check authentication status
  getStatus: async (): Promise<ApiResponse<{ isAuthenticated: boolean; message: string }>> => {
    try {
      const response = await authApiClient.get('/auth/status');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to check auth status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Logout
  logout: (): void => {
    localStorage.removeItem('griot_api_key');
  }
};

// MCP API Functions
export const mcpApi = {
  // Send MCP message
  sendMessage: async (request: MCPRequest): Promise<MCPResponse> => {
    const response = await mcpApiClient.post('/messages', request);
    return response.data;
  },

  // Initialize MCP connection
  initialize: async (): Promise<MCPResponse> => {
    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: 'init',
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'Griot Frontend',
          version: '1.0.0'
        }
      }
    });
  },

  // List available tools
  listTools: async (): Promise<MCPResponse> => {
    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: 'list-tools',
      method: 'tools/list'
    });
  },

  // Create short video via MCP
  createShortVideo: async (params: CreateVideoParams): Promise<MCPResponse> => {
    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: `create-video-${Date.now()}`,
      method: 'tools/call',
      params: {
        name: 'create-short-video',
        arguments: params
      }
    });
  },

  // Get video status via MCP
  getVideoStatus: async (jobId: string): Promise<MCPResponse> => {
    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: `status-${jobId}`,
      method: 'tools/call',
      params: {
        name: 'get-video-status',
        arguments: {
          job_id: jobId
        }
      }
    });
  },

  // List TTS voices via MCP
  listTTSVoices: async (provider?: string, language?: string): Promise<MCPResponse> => {
    const params: Record<string, string> = {};
    if (provider) params.provider = provider;
    if (language) params.language = language;

    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: 'list-voices',
      method: 'tools/call',
      params: {
        name: 'list-tts-voices',
        arguments: params
      }
    });
  },

  // Validate voice combination via MCP
  validateVoiceCombination: async (voiceName: string, provider: string): Promise<MCPResponse> => {
    return mcpApi.sendMessage({
      jsonrpc: '2.0',
      id: 'validate-voice',
      method: 'tools/call',
      params: {
        name: 'validate-voice-combination',
        arguments: {
          voice_name: voiceName,
          provider
        }
      }
    });
  }
};

// Direct API Functions (for non-MCP endpoints)
export const directApi = {
  // Generate Script (AI Script Generation) - moved to top for proper function declaration order
  generateScript: async (params: {
    topic?: string;
    auto_topic?: boolean;
    language?: string;
    script_provider?: string;
    script_type?: string;
    max_duration?: number;
    target_words?: number;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    const response = await apiClient.post('/ai/script/generate', params);

    if (response.data && response.data.job_id) {
      return {
        success: true,
        data: response.data
      };
    }

    return {
      success: false,
      error: 'Invalid response format'
    };
  },

  // Generate Script Synchronously (AI Script Generation) - for immediate results
  generateScriptSync: async (params: {
    topic?: string;
    auto_topic?: boolean;
    language?: string;
    script_provider?: string;
    script_type?: string;
    max_duration?: number;
    target_words?: number;
  }): Promise<ApiResponse<{ script: string; word_count: number; estimated_duration: number; provider_used: string }>> => {
    // Increase timeout for script generation as it can take longer
    const response = await apiClient.post(
      '/ai/script/generate',
      {
        ...params,
        sync: true
      },
      { timeout: 60000 }
    );

    const responseData = response.data;

    if (responseData && typeof responseData === 'object' && 'script' in responseData) {
      return {
        success: true,
        data: {
          script: responseData.script || '',
          word_count: responseData.word_count || 0,
          estimated_duration: responseData.estimated_duration || 0,
          provider_used: responseData.provider_used || 'unknown'
        }
      };
    }

    if (responseData && typeof responseData === 'object' && responseData.success && responseData.data) {
      return {
        success: true,
        data: {
          script: responseData.data.script || '',
          word_count: responseData.data.word_count || 0,
          estimated_duration: responseData.data.estimated_duration || 0,
          provider_used: responseData.data.provider_used || 'unknown'
        }
      };
    }

    return {
      success: false,
      error: responseData?.error || 'Invalid response format'
    };
  },

  // Topic to Video Pipeline (Stock Videos)
  footageToVideo: async (params: FootageToVideoRequest): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/ai/footage-to-video', params);

      // Return the job_id in the expected format
      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create video'
        : 'Failed to create video';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Script to Video Pipeline (AI Images)
  aiimageToVideo: async (params: AiimageToVideoRequest): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/ai/aiimage-to-video', params);

      // Return the job_id in the expected format
      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create video with AI images'
        : 'Failed to create video with AI images';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Research Topic
  researchTopic: async (searchTerm: string, targetLanguage: string): Promise<ApiResponse<{ title: string, content: string, sources: string[], language: string }>> => {
    try {
      const response = await apiClient.post('/ai/research-topic', {
        searchTerm,
        targetLanguage
      });

      if (response.data && response.data.job_id) {
        // Poll for completion using direct API
        const jobId = response.data.job_id;

        // Poll until completion
        let attempts = 0;
        const maxAttempts = 60; // 5 minutes max
        while (attempts < maxAttempts) {
          const statusResponse = await directApi.getJobStatus(jobId);
          if (!statusResponse.success) {
            throw new Error(statusResponse.error || 'Failed to get job status');
          }

          const job = statusResponse.data;
          if (!job) {
            throw new Error('Invalid job status response');
          }

          if (job.status === 'completed' && job.result) {
            // Extract research data from job result
            const researchData = {
              title: `Research: ${searchTerm}`,
              content: job.result.summary || '',
              sources: job.result.articles?.map((article: { source?: string }) => article.source || 'Unknown') || [],
              language: targetLanguage
            };

            return {
              success: true,
              data: researchData
            };
          } else if (job.status === 'failed') {
            throw new Error(job.error || 'Research failed');
          }

          // Wait before next poll
          await new Promise(resolve => setTimeout(resolve, 5000));
          attempts++;
        }

        throw new Error('Research job timed out');
      }

      throw new Error('Invalid response from research API');
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'message' in error
        ? (error as { message: string }).message
        : 'Failed to research topic';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Video Search Query Generation
  generateVideoSearchQueries: async (params: {
    script: string;
    segment_duration?: number;
    provider?: string;
    language?: string;
  }): Promise<ApiResponse<{
    queries: Array<{
      query: string;
      start_time: number;
      end_time: number;
      duration: number;
      visual_concept: string;
    }>;
    total_duration: number;
    total_segments: number;
    provider_used: string;
  }>> => {
    const response = await apiClient.post('/ai/video-search/generate-queries', params);

    if (response.data) {
      return {
        success: true,
        data: response.data
      };
    }

    return {
      success: false,
      error: 'Invalid response format'
    };
  },

  // Image Search
  searchStockImages: async (params: {
    query: string;
    orientation?: 'landscape' | 'portrait' | 'square';
    quality?: 'standard' | 'high' | 'ultra';
    per_page?: number;
    color?: string;
    size?: 'large' | 'medium' | 'small';
    provider?: 'pexels' | 'pixabay';
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/ai/image-search/stock-images', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to search stock images'
        : 'Failed to search stock images';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Image Search Status
  getImageSearchStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      images: Array<{
        id: string;
        url: string;
        download_url: string;
        width: number;
        height: number;
        photographer?: string;
        photographer_url?: string;
        alt?: string;
        tags?: string;
        source: string;
        aspect_ratio: number;
      }>;
      total_results: number;
      page: number;
      per_page: number;
      query_used: string;
      provider_used: string;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/ai/image-search/stock-images/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get image search status'
        : 'Failed to get image search status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Browse Images (with pagination)
  browseImages: async (params: {
    query: string;
    orientation?: 'landscape' | 'portrait' | 'square';
    quality?: 'standard' | 'high' | 'ultra';
    per_page?: number;
    page?: number;
    color?: string;
    size?: 'large' | 'medium' | 'small';
    provider?: 'pexels' | 'pixabay';
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/ai/image-browse', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to browse images'
        : 'Failed to browse images';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Image Browse Status
  getImageBrowseStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      images: Array<{
        id: string;
        url: string;
        download_url: string;
        width: number;
        height: number;
        photographer?: string;
        photographer_url?: string;
        alt?: string;
        tags?: string;
        source: string;
        aspect_ratio: number;
      }>;
      total_results: number;
      page: number;
      per_page: number;
      query_used: string;
      provider_used: string;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/ai/image-browse/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get image browse status'
        : 'Failed to get image browse status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Image Providers Status
  getImageProvidersStatus: async (): Promise<ApiResponse<{
    providers: {
      [key: string]: {
        available: boolean;
        name: string;
        description: string;
        features: string[];
      };
    };
    supported_orientations: string[];
    supported_qualities: string[];
    supported_colors: string[];
    supported_sizes: string[];
  }>> => {
    try {
      const response = await apiClient.get('/ai/image-providers/status');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get image providers status'
        : 'Failed to get image providers status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // List Together AI Models
  listTogetherModels: async (): Promise<ApiResponse<{ models: string[] }>> => {
    try {
      const response = await apiClient.get('/images/models/together');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to fetch Together AI models'
        : 'Failed to fetch Together AI models';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // List Modal Image Models
  listModalModels: async (): Promise<ApiResponse<{ models: string[] }>> => {
    try {
      const response = await apiClient.get('/images/models/modal');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to fetch Modal Image models'
        : 'Failed to fetch Modal Image models';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Job Status (for any job type)
  getJobStatus: async (jobId: string): Promise<ApiResponse<Job>> => {
    try {
      const response = await rootApiClient.get(`/jobs/${jobId}/status`);

      // The jobs endpoint returns the response in the expected format already
      if (response.data && response.data.success !== undefined) {
        return response.data;
      }

      // For backwards compatibility, wrap if needed
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get job status'
        : 'Failed to get job status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // List user jobs
  listJobs: async (page = 1, limit = 20): Promise<ApiResponse<{ jobs: Job[], total: number }>> => {
    const response = await rootApiClient.get(`/jobs?page=${page}&limit=${limit}`);

    // The jobs endpoint returns the response in the expected format already
    if (response.data && response.data.success !== undefined) {
      return response.data;
    }

    // For backwards compatibility, wrap if needed
    return {
      success: true,
      data: response.data
    };
  },

  // Delete job
  deleteJob: async (jobId: string): Promise<ApiResponse<void>> => {
    try {
      const response = await rootApiClient.delete(`/jobs/${jobId}`);

      // The jobs endpoint returns the response in the expected format already
      if (response.data && response.data.success) {
        return {
          success: true,
          data: undefined
        };
      }

      // If success is false, return the error
      if (response.data && response.data.success === false) {
        return {
          success: false,
          error: response.data.message || 'Failed to delete job'
        };
      }

      // For backwards compatibility, assume success if we get a 200 response
      return {
        success: true,
        data: undefined
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to delete job'
        : 'Failed to delete job';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Document conversion APIs
  convertUrlToMarkdown: async (url: string, options?: {
    includeMetadata?: boolean;
    preserveFormatting?: boolean;
    cookiesUrl?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('url', url);
      formData.append('include_metadata', (options?.includeMetadata ?? true).toString());
      formData.append('preserve_formatting', (options?.preserveFormatting ?? true).toString());
      if (options?.cookiesUrl) {
        formData.append('cookies_url', options.cookiesUrl);
      }

      const response = await apiClient.post('/documents/to-markdown', formData);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to convert URL to Markdown'
        : 'Failed to convert URL to Markdown';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  convertFileToMarkdown: async (file: File, options?: {
    includeMetadata?: boolean;
    preserveFormatting?: boolean;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('include_metadata', (options?.includeMetadata ?? true).toString());
      formData.append('preserve_formatting', (options?.preserveFormatting ?? true).toString());

      const response = await apiClient.post('/documents/to-markdown', formData);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to convert file to Markdown'
        : 'Failed to convert file to Markdown';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  extractStructuredData: async (input: {
    inputText?: string;
    inputUrl?: string;
    inputFile?: File;
    extractionSchema: string;
    extractionPrompt: string;
    useCustomPrompt: boolean;
    model: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();

      if (input.inputText) {
        formData.append('input_text', input.inputText);
      } else if (input.inputUrl) {
        formData.append('file_url', input.inputUrl);
      } else if (input.inputFile) {
        formData.append('file', input.inputFile);
      }

      formData.append('extraction_schema', input.extractionSchema);
      formData.append('extraction_prompt', input.extractionPrompt);
      formData.append('use_custom_prompt', input.useCustomPrompt.toString());
      formData.append('model', input.model);

      const response = await apiClient.post('/documents/langextract', formData);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to extract structured data'
        : 'Failed to extract structured data';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get TTS providers and voices (using correct backend endpoints)
  getTTSProviders: async (): Promise<ApiResponse<Record<string, unknown>>> => {
    const response = await apiClient.get('/audio/tts/providers');
    return response.data;
  },

  // Get voices for provider (using correct backend endpoints)
  getVoicesForProvider: async (provider: string): Promise<ApiResponse<Record<string, unknown>>> => {
    const response = await apiClient.get(`/audio/tts/${provider}/voices`);
    return response.data;
  },

  // Dashboard APIs
  getDashboardStats: async (): Promise<ApiResponse<{
    total_videos: number;
    active_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    total_users: number;
    active_api_keys: number;
    storage_used_gb?: number;
    storage_total_gb?: number;
    avg_processing_time_seconds?: number;
  }>> => {
    const response = await apiClient.get('/dashboard/stats');
    return {
      success: true,
      data: response.data
    };
  },

  getRecentActivity: async (limit: number = 10): Promise<ApiResponse<Array<{
    id: string;
    type: string;
    title: string;
    timestamp: string;
    status: string;
    details?: string;
    operation?: string;
    progress?: number;
  }>>> => {
    const response = await apiClient.get(`/dashboard/recent-activity?limit=${limit}`);

    // The backend returns the array directly
    const data = Array.isArray(response.data) ? response.data : response.data.data || response.data;

    return {
      success: true,
      data: Array.isArray(data) ? data : []
    };
  },

  // Retry job
  retryJob: async (jobId: string): Promise<ApiResponse<void>> => {
    const response = await rootApiClient.post(`/jobs/${jobId}/retry`);

    if (response.data && response.data.success !== undefined) {
      return response.data;
    }

    return {
      success: true,
      data: response.data
    };
  },

  // Video Management APIs
  getVideos: async (params?: {
    page?: number;
    limit?: number;
    video_type?: string;
    search?: string;
  }): Promise<ApiResponse<{
    videos: Array<{
      id: string;
      title: string;
      description?: string;
      video_type: string;
      final_video_url: string;
      video_with_audio_url?: string;
      audio_url?: string;
      srt_url?: string;
      thumbnail_url?: string;
      duration_seconds?: number;
      resolution?: string;
      file_size_mb?: number;
      word_count?: number;
      segments_count?: number;
      script_text?: string;
      voice_provider?: string;
      voice_name?: string;
      language?: string;
      processing_time_seconds?: number;
      background_videos_used?: string[];
      tags?: string[];
      download_count: number;
      last_accessed?: string;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    limit: number;
  }>> => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.video_type) queryParams.append('video_type', params.video_type);
    if (params?.search) queryParams.append('search', params.search);

    const response = await apiClient.get(`/videos/?${queryParams.toString()}`);
    return {
      success: true,
      data: response.data
    };
  },

  getVideo: async (videoId: string) => {
    const response = await apiClient.get(`/videos/${videoId}/`);
    return {
      success: true,
      data: response.data
    };
  },

  updateVideo: async (videoId: string, updates: {
    title?: string;
    description?: string;
    tags?: string[];
  }) => {
    const response = await apiClient.put(`/videos/${videoId}/`, updates);
    return {
      success: true,
      data: response.data
    };
  },

  deleteVideo: async (videoId: string) => {
    const response = await apiClient.delete(`/videos/${videoId}/`);
    return {
      success: true,
      data: response.data
    };
  },

  getVideoDownloadUrl: async (videoId: string, format: string = 'mp4') => {
    const response = await apiClient.get(`/videos/${videoId}/download/?format=${format}`);
    return {
      success: true,
      data: response.data
    };
  },

  getVideoStats: async () => {
    const response = await apiClient.get('/videos/stats/overview/');
    return {
      success: true,
      data: response.data
    };
  },


  // Unified Video Generation
  generateVideo: async (params: {
    prompt: string;
    provider?: string;
    negative_prompt?: string;
    width?: number;
    height?: number;
    num_frames?: number;
    num_inference_steps?: number;
    guidance_scale?: number;
    seed?: number;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/videos/generate', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to generate LTX video'
        : 'Failed to generate video';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  generateVideoFromImage: async (params: {
    prompt: string;
    image: File;
    provider?: string;
    negative_prompt?: string;
    width?: number;
    height?: number;
    num_frames?: number;
    num_inference_steps?: number;
    guidance_scale?: number;
    seed?: number;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('prompt', params.prompt);
      formData.append('image', params.image);
      if (params.provider) formData.append('provider', params.provider);
      if (params.negative_prompt) formData.append('negative_prompt', params.negative_prompt);
      if (params.width) formData.append('width', params.width.toString());
      if (params.height) formData.append('height', params.height.toString());
      if (params.num_frames) formData.append('num_frames', params.num_frames.toString());
      if (params.num_inference_steps) formData.append('num_inference_steps', params.num_inference_steps.toString());
      if (params.guidance_scale) formData.append('guidance_scale', params.guidance_scale.toString());
      if (params.seed) formData.append('seed', params.seed.toString());

      const response = await apiClient.post('/videos/from_image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to generate LTX video from image'
        : 'Failed to generate LTX video from image';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Deprecated: Use getJobStatus instead
  getVideoStatus: async (jobId: string): Promise<ApiResponse<Job>> => {
    return directApi.getJobStatus(jobId);
  },

  // Deprecated: Use getJobStatus instead
  getVideoFromImageStatus: async (jobId: string): Promise<ApiResponse<Job>> => {
    return directApi.getJobStatus(jobId);
  },

  // WaveSpeed AI Video Generation
  generateWaveSpeedVideo: async (params: {
    prompt: string;
    model?: string;
    size?: string;
    duration?: number;
    seed?: number;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/videos/wavespeed/generate', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to generate WaveSpeed video'
        : 'Failed to generate WaveSpeed video';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  generateWaveSpeedVideoFromImage: async (params: {
    prompt: string;
    image: File;
    seed?: number;
    model?: string;
    resolution?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('prompt', params.prompt);
      formData.append('image', params.image);
      if (params.seed !== undefined) formData.append('seed', params.seed.toString());
      if (params.model) formData.append('model', params.model);
      if (params.resolution) formData.append('resolution', params.resolution);

      const response = await apiClient.post('/videos/wavespeed/image_to_video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to generate WaveSpeed video from image'
        : 'Failed to generate WaveSpeed video from image';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getWaveSpeedVideoStatus: async (jobId: string): Promise<ApiResponse<Job>> => {
    try {
      const response = await apiClient.get(`/videos/wavespeed/generate/${jobId}`);

      if (response.data) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get WaveSpeed video status'
        : 'Failed to get WaveSpeed video status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getWaveSpeedVideoFromImageStatus: async (jobId: string): Promise<ApiResponse<Job>> => {
    try {
      const response = await apiClient.get(`/videos/wavespeed/image_to_video/${jobId}`);

      if (response.data) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to get WaveSpeed video from image status'
        : 'Failed to get WaveSpeed video from image status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // POST method for axios requests
  post: async (url: string, data: Record<string, unknown> | FormData | string | number | boolean | null, config?: Record<string, unknown>): Promise<AxiosResponse> => {
    return await apiClient.post(url, data, config);
  },

  // PUT method for axios requests
  put: async (url: string, data: Record<string, unknown> | FormData | string | number | boolean | null, config?: Record<string, unknown>): Promise<AxiosResponse> => {
    return await apiClient.put(url, data, config);
  },

  // GET method for axios requests
  get: async (url: string): Promise<AxiosResponse> => {
    return await apiClient.get(url);
  },

  // GET method with extended timeout for long-running operations like polling
  getLongTimeout: async (url: string, timeoutMs: number = 120000): Promise<AxiosResponse> => {
    return await apiClient.get(url, { timeout: timeoutMs });
  },

  // DELETE method for axios requests
  delete: async (url: string): Promise<AxiosResponse> => {
    return await apiClient.delete(url);
  },

  // Admin User Management APIs
  listUsers: async (page: number = 1, limit: number = 50, search?: string, role?: string): Promise<ApiResponse<{
    users: Array<{
      id: string;
      username?: string;
      email: string;
      full_name?: string;
      role: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    }>;
    pagination: {
      total_pages: number;
      total_count: number;
      current_page: number;
      limit: number;
    };
  }>> => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString()
      });
      if (search) params.append('search', search);
      if (role) params.append('role', role);

      const response = await apiClient.get(`/admin/users/?${params.toString()}`);
      // Extract the inner data from response structure
      const data = response.data?.data || response.data;
      return {
        success: true,
        data: data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load users'
        : 'Failed to load users';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getUserStats: async (): Promise<ApiResponse<{
    success: boolean;
    stats: {
      total_users: number;
      active_users: number;
      admin_count: number;
      user_count: number;
      viewer_count: number;
    };
  }>> => {
    try {
      const response = await apiClient.get('/admin/users/stats');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load user stats'
        : 'Failed to load user stats';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getUser: async (userId: string): Promise<ApiResponse<{
    success: boolean;
    user: {
      id: string;
      username?: string;
      email: string;
      full_name?: string;
      role: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    };
  }>> => {
    try {
      const response = await apiClient.get(`/admin/users/${userId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load user'
        : 'Failed to load user';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  createUser: async (userData: {
    username?: string;
    email: string;
    full_name?: string;
    password: string;
    role: string;
    is_active: boolean;
  }): Promise<ApiResponse<{
    success: boolean;
    message: string;
    user: {
      id: string;
      username?: string;
      email: string;
      full_name?: string;
      role: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    };
  }>> => {
    try {
      const response = await apiClient.post('/admin/users/', userData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create user'
        : 'Failed to create user';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateUser: async (userId: string, userData: {
    username?: string;
    email?: string;
    full_name?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<ApiResponse<{
    success: boolean;
    message: string;
    user: {
      id: string;
      username?: string;
      email: string;
      full_name?: string;
      role: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    };
  }>> => {
    try {
      const response = await apiClient.put(`/admin/users/${userId}`, userData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update user'
        : 'Failed to update user';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  deleteUser: async (userId: string): Promise<ApiResponse<{
    success: boolean;
    message: string;
  }>> => {
    try {
      const response = await apiClient.delete(`/admin/users/${userId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to delete user'
        : 'Failed to delete user';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Settings
  getDashboardSettings: async (): Promise<ApiResponse<{
    auto_refresh: boolean;
    email_notifications: boolean;
    api_logging: boolean;
    max_concurrent_jobs: number;
    default_video_resolution: string;
    storage_retention_days: number;
  }>> => {
    try {
      const response = await apiClient.get('/dashboard/settings');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load settings'
        : 'Failed to load settings';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateDashboardSettings: async (settings: {
    auto_refresh?: boolean;
    email_notifications?: boolean;
    api_logging?: boolean;
    max_concurrent_jobs?: number;
    default_video_resolution?: string;
    storage_retention_days?: number;
  }): Promise<ApiResponse<{
    message: string;
  }>> => {
    try {
      const response = await apiClient.put('/dashboard/settings', settings);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to save settings'
        : 'Failed to save settings';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // User Profile Management
  getUserProfile: async (): Promise<ApiResponse<{
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: string;
    created_at: string;
    last_login?: string;
    is_active: boolean;
  }>> => {
    try {
      const response = await apiClient.get('/auth/profile');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load profile'
        : 'Failed to load profile';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateUserProfile: async (profileData: {
    username?: string;
    email?: string;
    full_name?: string;
  }): Promise<ApiResponse<{
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: string;
    created_at: string;
    last_login?: string;
    is_active: boolean;
  }>> => {
    try {
      const response = await apiClient.put('/auth/profile', profileData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update profile'
        : 'Failed to update profile';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  changePassword: async (passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<ApiResponse<{
    message: string;
  }>> => {
    try {
      const response = await apiClient.post('/auth/change-password', passwordData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to change password'
        : 'Failed to change password';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Avatar Upload
  uploadAvatar: async (file: File): Promise<ApiResponse<{
    id: string;
    username: string;
    email: string;
    full_name: string;
    avatar_url: string;
    role: string;
    created_at: string;
    last_login?: string;
    is_active: boolean;
  }>> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/auth/profile/avatar', formData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to upload avatar'
        : 'Failed to upload avatar';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Email Functions
  sendTestEmail: async (emailData: {
    recipient_email: string;
    subject?: string;
    message?: string;
  }): Promise<ApiResponse<{
    message: string;
    email_id?: string;
  }>> => {
    try {
      const response = await apiClient.post('/dashboard/send-test-email', emailData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to send test email'
        : 'Failed to send test email';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // System Info
  getSystemInfo: async (): Promise<ApiResponse<{
    version: string;
    api_status: string;
    database: {
      status: string;
      version?: string;
      size_mb?: number;
      tables?: number;
    };
    redis: {
      status: string;
    };
    storage: {
      status: string;
      total_gb?: number;
      used_gb?: number;
      free_gb?: number;
      usage_percent?: number;
    };
    jobs?: {
      active?: number;
      completed?: number;
      failed?: number;
      total?: number;
    };
    api_keys?: {
      total?: number;
      active?: number;
      total_usage?: number;
    };
  }>> => {
    try {
      const response = await apiClient.get('/dashboard/system-info');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load system info'
        : 'Failed to load system info';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Config Settings (env overrides)
  getConfigSettings: async (): Promise<ApiResponse<Record<string, {
    label: string;
    settings: Record<string, {
      value: string | number | boolean;
      configured: boolean;
      type: string;
      label: string;
      default: string | number | boolean;
      placeholder: string;
    }>;
  }>>> => {
    try {
      const response = await apiClient.get('/dashboard/settings/config');
      return { success: true, data: response.data };
    } catch (error: unknown) {
      const msg = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to load config'
        : 'Failed to load config';
      return { success: false, error: msg };
    }
  },

  updateConfigSettings: async (settings: Record<string, string | number | boolean>): Promise<ApiResponse<{ updated: string[]; count: number }>> => {
    try {
      const response = await apiClient.put('/dashboard/settings/config', { settings });
      return { success: true, data: response.data };
    } catch (error: unknown) {
      const msg = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to save config'
        : 'Failed to save config';
      return { success: false, error: msg };
    }
  },

  // API Keys
  listApiKeys: async (page: number = 1, limit: number = 50, search?: string, statusFilter?: string): Promise<ApiResponse<{
    api_keys: Array<{
      id: string;
      name: string;
      key: string;
      user_id: string;
      user_email: string;
      is_active: boolean;
      created_at: string;
      last_used?: string;
      expires_at?: string;
      usage_count: number;
      rate_limit: number;
      permissions: string[];
    }>;
    total: number;
    pages: number;
  }>> => {
    try {
      const params = new URLSearchParams({
        page: String(page),
        limit: String(limit)
      });
      if (search) params.append('search', search);
      if (statusFilter) params.append('status_filter', statusFilter);

      const response = await apiClient.get(`/dashboard/api-keys?${params.toString()}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load API keys'
        : 'Failed to load API keys';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getApiKey: async (keyId: string): Promise<ApiResponse<{
    id: string;
    name: string;
    key: string;
    user_id: string;
    user_email: string;
    is_active: boolean;
    created_at: string;
    last_used?: string;
    expires_at?: string;
    usage_count: number;
    rate_limit: number;
    permissions: string[];
  }>> => {
    try {
      const response = await apiClient.get(`/dashboard/api-keys/${keyId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load API key'
        : 'Failed to load API key';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  createApiKey: async (data: {
    name: string;
    user_id: string;
    rate_limit?: number;
    expires_at?: string;
    permissions?: string[];
  }): Promise<ApiResponse<{
    id: string;
    name: string;
    key: string;
    user_id: string;
    created_at: string;
  }>> => {
    try {
      const response = await apiClient.post('/dashboard/api-keys', data);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create API key'
        : 'Failed to create API key';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateApiKey: async (keyId: string, data: {
    name?: string;
    rate_limit?: number;
    is_active?: boolean;
    expires_at?: string;
    permissions?: string[];
  }): Promise<ApiResponse<{
    message: string;
  }>> => {
    try {
      const response = await apiClient.put(`/dashboard/api-keys/${keyId}`, data);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update API key'
        : 'Failed to update API key';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  deleteApiKey: async (keyId: string): Promise<ApiResponse<{
    message: string;
  }>> => {
    try {
      const response = await apiClient.delete(`/dashboard/api-keys/${keyId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to delete API key'
        : 'Failed to delete API key';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Job Cleanup
  getCleanupStatus: async (): Promise<ApiResponse<{
    last_cleanup: string;
    jobs_deleted: number;
    jobs_archived: number;
    next_cleanup?: string;
    status: string;
  }>> => {
    try {
      const response = await apiClient.get('/admin/jobs/cleanup/status');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load cleanup status'
        : 'Failed to load cleanup status';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  triggerCleanup: async (): Promise<ApiResponse<{
    success: boolean;
    message: string;
    jobs_deleted?: number;
    jobs_archived?: number;
  }>> => {
    try {
      const response = await apiClient.post('/admin/jobs/cleanup/trigger', {});
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to trigger cleanup'
        : 'Failed to trigger cleanup';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  manualCleanup: async (maxAgeHours: number): Promise<ApiResponse<{
    success: boolean;
    message: string;
    jobs_deleted?: number;
    jobs_archived?: number;
  }>> => {
    try {
      const response = await apiClient.post(`/admin/jobs/cleanup?max_age_hours=${maxAgeHours}`, {});
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to perform cleanup'
        : 'Failed to perform cleanup';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Library Management
  deleteAllLibraryContent: async (): Promise<ApiResponse<{
    message: string;
    deleted_records: number;
    deleted_s3_files: number;
    errors: number;
  }>> => {
    try {
      const response = await apiClient.delete('/library/content/all/everything?confirm=true');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to delete all library content'
        : 'Failed to delete all library content';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  cleanupOrphanedFiles: async (confirm: boolean = true, dryRun: boolean = false): Promise<ApiResponse<{
    message: string;
    total_checked: number;
    missing_files_found: number;
    deleted_records: number;
    dry_run: boolean;
    details: any[];
  }>> => {
    try {
      const response = await apiClient.post(`/library/cleanup/orphaned-files?confirm=${confirm}&dry_run=${dryRun}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to cleanup orphaned files'
        : 'Failed to cleanup orphaned files';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Postiz Schedule
  schedulePost: async (scheduleData: {
    job_id: string;
    content: string;
    integrations: string[];
    post_type: string;
    schedule_date: string;
    tags?: string[];
  }): Promise<ApiResponse<{
    success: boolean;
    message: string;
    scheduled_id?: string;
  }>> => {
    try {
      const response = await rootApiClient.post('/postiz/schedule-job', scheduleData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to schedule post'
        : 'Failed to schedule post';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Agents API Functions
  getAgents: async (): Promise<ApiResponse<Record<string, unknown>[]>> => {
    try {
      const response = await apiClient.get('/agents');
      return {
        success: true,
        data: response.data || []
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load agents'
        : 'Failed to load agents';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getAgentSessions: async (): Promise<ApiResponse<{ sessions: Record<string, unknown>[] }>> => {
    try {
      const response = await apiClient.get('/agents/sessions');
      return {
        success: true,
        data: response.data || { sessions: [] }
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load agent sessions'
        : 'Failed to load agent sessions';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  createAgentSession: async (sessionData: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post('/agents/sessions', sessionData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create agent session'
        : 'Failed to create agent session';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateAgentSession: async (sessionId: string, updates: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.put(`/agents/sessions/${sessionId}`, updates);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update agent session'
        : 'Failed to update agent session';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  importAgentSessions: async (formData: FormData): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post('/agents/sessions/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to import agent sessions'
        : 'Failed to import agent sessions';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getKnowledgeBases: async (): Promise<ApiResponse<Record<string, unknown>[]>> => {
    try {
      const response = await apiClient.get('/agents/knowledge-bases');
      return {
        success: true,
        data: response.data || []
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load knowledge bases'
        : 'Failed to load knowledge bases';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  createKnowledgeBase: async (kbData: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post('/agents/knowledge-bases', kbData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to create knowledge base'
        : 'Failed to create knowledge base';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateKnowledgeBase: async (kbId: string, updates: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.put(`/agents/knowledge-bases/${kbId}`, updates);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update knowledge base'
        : 'Failed to update knowledge base';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getUserPreferences: async (): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.get('/agents/users/preferences');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load user preferences'
        : 'Failed to load user preferences';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  updateUserPreferences: async (preferences: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.put('/agents/users/preferences', preferences);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to update user preferences'
        : 'Failed to update user preferences';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  agentSpeechToText: async (formData: FormData): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post('/agents/speech-to-text', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to transcribe audio'
        : 'Failed to transcribe audio';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  deleteAgentSession: async (sessionId: string): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.delete(`/agents/sessions/${sessionId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to delete session'
        : 'Failed to delete session';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getAgentSessionHistory: async (sessionId: string): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.get(`/agents/sessions/${sessionId}/history`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load session history'
        : 'Failed to load session history';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  exportAgentSession: async (sessionId: string, format: string = 'json'): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.get(`/agents/sessions/${sessionId}/export?format=${format}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to export session'
        : 'Failed to export session';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  sendAgentMessage: async (sessionId: string, messageData: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post(`/agents/sessions/${sessionId}/chat`, messageData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to send message'
        : 'Failed to send message';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  getTextOverlayPresets: async (): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.get('/videos/text-overlay/all-presets');
      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail ||
        (error as { message?: string }).message ||
        'Failed to load text overlay presets'
        : 'Failed to load text overlay presets';
      return {
        success: false,
        error: errorMessage
      };
    }
  }
};

// Pollinations API Functions
export const pollinationsApi = {
  // Image Generation
  generateImage: async (params: {
    prompt: string;
    model?: string;
    width?: number;
    height?: number;
    seed?: number;
    negative_prompt?: string;
    enhance?: boolean;
    nologo?: boolean;
    safe?: boolean;
    transparent?: boolean;
    image_url?: string;
    referrer?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/pollinations/image/generate', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Image Generation Status
  getImageGenerationStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      content_url: string;
      content_type: string;
      file_size: number;
      generation_time: number;
      model_used: string;
      prompt: string;
      dimensions: string;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/pollinations/image/generate/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Video Analysis
  analyzeVideo: async (params: {
    video_url?: string;
    question?: string;
    model?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/pollinations/video/analyze', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Video Analysis with Upload
  analyzeUploadedVideo: async (file: File, question: string = 'Describe this video in detail', model: string = 'openai'): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question', question);
      formData.append('model', model);

      const response = await apiClient.post('/pollinations/video/analyze-upload', formData);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Text Generation
  generateText: async (params: {
    prompt: string;
    model?: string;
    seed?: number;
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
    system?: string;
    json_mode?: boolean;
    referrer?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/pollinations/text/generate', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Chat Completions
  createChatCompletion: async (params: {
    messages: Array<{
      role: string;
      content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
    }>;
    model?: string;
    seed?: number;
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
    json_mode?: boolean;
    tools?: Array<Record<string, unknown>>;
    tool_choice?: string | Record<string, unknown>;
    referrer?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/pollinations/chat/completions', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Text Generation Status
  getTextGenerationStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      text?: string;
      response?: Record<string, unknown>;
      assistant_message?: string;
      model_used: string;
      generation_time: number;
      prompt?: string;
      character_count?: number;
      message_count?: number;
      has_tool_calls?: boolean;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/pollinations/text/generate/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Chat Completion Status
  getChatCompletionStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      response: Record<string, unknown>;
      assistant_message: string;
      model_used: string;
      generation_time: number;
      message_count: number;
      has_tool_calls: boolean;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/pollinations/chat/completions/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Synchronous Text Generation (for quick responses)
  generateTextSync: async (params: {
    prompt: string;
    model?: string;
    seed?: number;
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
    system?: string;
    json_mode?: boolean;
    referrer?: string;
  }): Promise<ApiResponse<{
    text: string;
    model_used: string;
    generation_time: number;
    prompt: string;
    character_count: number;
  }>> => {
    try {
      const response = await apiClient.post('/text/generate', {
        prompt: params.prompt,
        temperature: params.temperature,
        style: 'general',
      });

      return {
        success: true,
        data: {
          text: response.data.content,
          model_used: '',
          generation_time: 0,
          prompt: params.prompt,
          character_count: response.data.content?.length || 0,
        }
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Synchronous Chat Completion (for quick responses)
  createChatCompletionSync: async (params: {
    messages: Array<{
      role: string;
      content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
    }>;
    model?: string;
    seed?: number;
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
    json_mode?: boolean;
    tools?: Array<Record<string, unknown>>;
    tool_choice?: string | Record<string, unknown>;
    referrer?: string;
  }): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.post('/anyllm/completions', params);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Audio TTS
  generateTTS: async (params: {
    text: string;
    voice?: string;
    model?: string;
  }): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const response = await apiClient.post('/pollinations/audio/tts', params);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get TTS Status
  getTTSStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      content_url: string;
      content_type: string;
      file_size: number;
      generation_time: number;
      model_used: string;
      voice_used: string;
      text: string;
      text_length: number;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/pollinations/audio/tts/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Audio Transcription
  transcribeAudio: async (file: File, question: string = "Transcribe this audio"): Promise<ApiResponse<{ job_id: string }>> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question', question);

      const response = await apiClient.post('/pollinations/audio/transcribe', formData);

      if (response.data && response.data.job_id) {
        return {
          success: true,
          data: response.data
        };
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Get Transcription Status
  getTranscriptionStatus: async (jobId: string): Promise<ApiResponse<{
    job_id: string;
    status: string;
    result?: {
      transcription: string;
      audio_format: string;
      generation_time: number;
      file_name?: string;
      file_size: number;
      character_count: number;
    };
    error?: string;
  }>> => {
    try {
      const response = await apiClient.get(`/pollinations/audio/transcribe/${jobId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // Synchronous TTS (for quick responses)
  generateTTSSync: async (params: {
    text: string;
    voice?: string;
    model?: string;
  }): Promise<ApiResponse<{
    content_url: string;
    content_type: string;
    file_size: number;
    generation_time: number;
    model_used: string;
    voice_used: string;
    text: string;
    text_length: number;
  }>> => {
    try {
      const response = await apiClient.post('/pollinations/audio/tts', { ...params, sync: true });

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // List Available Image Models (Pollinations AI)
  listImageModels: async (): Promise<ApiResponse<{ models: string[] }>> => {
    try {
      const response = await apiClient.get('/pollinations/models/image');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  // List Available Image Edit Models (Pollinations AI) - models that support image input
  listImageEditModels: async (): Promise<ApiResponse<{ models: { name: string; description: string }[] }>> => {
    try {
      const response = await apiClient.get('/pollinations/models/image-edit');
      return { success: true, data: response.data };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return { success: false, error: errorMessage };
    }
  },

  // List Available Video Models (Pollinations AI)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  listVideoModels: async (): Promise<ApiResponse<{ models: any[] }>> => {
    try {
      const response = await apiClient.get('/pollinations/models/video');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  listTextModels: async (): Promise<ApiResponse<Record<string, unknown>>> => {
    try {
      const response = await apiClient.get('/pollinations/models/text');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  },

  listVoices: async (): Promise<ApiResponse<{
    voices: Array<{ name: string; description: string }>;
    model: string;
    total_count: number;
    note?: string;
  }>> => {
    try {
      const response = await apiClient.get('/pollinations/voices');

      return {
        success: true,
        data: response.data
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      return {
        success: false,
        error: errorMessage
      };
    }
  }
};

// Utility functions
export const apiUtils = {
  // Poll job status until completion
  pollJobStatus: async (
    jobId: string,
    onUpdate?: Function,
    pollInterval = 5000,
    maxAttempts = 120 // 10 minutes max
  ): Promise<Job> => {
    let attempts = 0;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;

          // Try MCP first, then direct API
          let job: Job;
          try {
            const mcpResponse = await mcpApi.getVideoStatus(jobId);
            if (mcpResponse.error) {
              throw new Error(mcpResponse.error.message);
            }
            job = mcpResponse.result as Job;
          } catch {
            // Fallback to direct API
            const directResponse = await directApi.getJobStatus(jobId);
            if (!directResponse.success || !directResponse.data) {
              throw new Error(directResponse.error || 'Failed to get job status');
            }
            job = directResponse.data;
          }

          onUpdate?.(job);

          if (job.status === 'completed' || job.status === 'failed') {
            resolve(job);
            return;
          }

          if (attempts >= maxAttempts) {
            reject(new Error('Polling timeout - job did not complete'));
            return;
          }

          // Continue polling
          setTimeout(poll, pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },

  // Format error message
  formatError: (error: unknown): string => {
    if (error && typeof error === 'object') {
      if ('response' in error) {
        const axiosError = error as { response?: { data?: { error?: string; message?: string; detail?: string } } };
        if (axiosError.response?.data?.detail) {
          return axiosError.response.data.detail;
        }
        if (axiosError.response?.data?.error) {
          return axiosError.response.data.error;
        }
        if (axiosError.response?.data?.message) {
          return axiosError.response.data.message;
        }
      }
      if ('message' in error) {
        return (error as { message: string }).message;
      }
    }
    return 'An unexpected error occurred';
  },

  // Check if API key is set
  hasApiKey: (): boolean => {
    return !!apiClient.defaults.headers.common['X-API-Key'];
  }
};
