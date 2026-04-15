/**
 * Griot Service
 * Centralized service for all Griot backend API calls
 */

// Use environment variable if available, otherwise use relative URL for proxy
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Ensure HTTPS is used in production environments
const getApiBase = () => {
    // If no explicit base URL is set, always use relative URLs to avoid mixed content issues
    if (!import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL === '') {
        return '/api/v1';
    }

    // If an explicit base URL is provided, ensure it uses the correct protocol
    if (API_BASE.startsWith('http://') && window.location.protocol === 'https:') {
        // Convert HTTP to HTTPS when the page is loaded over HTTPS
        return API_BASE.replace('http://', 'https://');
    }

    // If it's an https:// URL but we're on http://, keep it as-is
    // (This handles cases where the API is on a different secure domain)
    return API_BASE;
};

interface Voice {
    id: string;
    name: string;
    language?: string;
}

interface NewsSearchResult {
    title: string;
    description: string;
    url: string;
    source: string;
    published_at?: string;
    image_url?: string;
}

interface WebSearchResult {
    title: string;
    description?: string;
    url: string;
    source: string;
    published_at?: string;
    content?: string;
}

interface ImageGenerationRequest {
    prompt: string;
    style?: string;
    size?: string;
}

interface ImageGenerationResult {
    url?: string;
    prompt?: string;
    job_id?: string;
}

interface TextToSpeechRequest {
    text: string;
    voice?: string;
    language?: string;
}

interface TextToSpeechResult {
    url?: string;
    text?: string;
    job_id?: string;
}

interface Scene {
    description: string;
    duration?: number;
}

interface ShortVideoRequest {
    scenes: Scene[];
    music?: string;
    style?: string;
}

interface ShortVideoResult {
    url: string;
    job_id?: string;
}

interface VideoGenerationRequest {
    prompt: string;
    provider?: string;
    negative_prompt?: string;
    width?: number;
    height?: number;
    num_frames?: number;
    sync?: boolean;
    num_inference_steps?: number;
    guidance_scale?: number;
    seed?: number;
    duration?: number;
}

interface VideoGenerationResult {
    job_id?: string;
    video_url?: string;
    prompt_used?: string;
    negative_prompt_used?: string;
    dimensions?: { [key: string]: number };
    num_frames?: number;
    processing_time?: number;
    provider_used?: string;
}

interface MusicTrack {
    file: string;
    title: string;
    mood: string;
    duration: number;
    start: number;
    end: number;
    url: string;
}

interface MusicTracksResponse {
    success: boolean;
    tracks: MusicTrack[];
    total: number;
    moods: string[];
}

interface MusicMoodsResponse {
    success: boolean;
    moods: string[];
    mood_counts: Record<string, number>;
    total_moods: number;
}

class GriotApiService {
    private static instance: GriotApiService;
    private apiKey: string | null = null;

    private constructor() {
        // Try to get API key from localStorage
        this.apiKey = localStorage.getItem('griot_api_key') || localStorage.getItem('api_key');
    }

    static getInstance(): GriotApiService {
        if (!GriotApiService.instance) {
            GriotApiService.instance = new GriotApiService();
        }
        return GriotApiService.instance;
    }

    /**
     * Set API key for authentication
     */
    setApiKey(key: string): void {
        this.apiKey = key;
        localStorage.setItem('griot_api_key', key);
        localStorage.setItem('api_key', key);
    }

    /**
     * Make authenticated API request
     */
    private async request<T>(
        endpoint: string,
        // eslint-disable-next-line no-undef
        options: RequestInit = {}
    ): Promise<T> {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>)
        };

        // Always get fresh API key from localStorage (don't rely on cached this.apiKey)
        // This ensures we have the latest key even if user logged in after service initialization
        const currentApiKey = localStorage.getItem('griot_api_key') || localStorage.getItem('api_key') || this.apiKey;

        if (currentApiKey) {
            headers['Authorization'] = `Bearer ${currentApiKey}`;
            headers['x-api-key'] = currentApiKey;
            headers['X-API-Key'] = currentApiKey;
        }

        let url = `${getApiBase()}${endpoint}`;

        // Ensure HTTPS is used when the page is loaded over HTTPS
        // This prevents mixed content errors
        if (url.startsWith('http://') && window.location.protocol === 'https:') {
            url = url.replace('http://', 'https://');
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Get available voices for text-to-speech
     */
    async getAvailableVoices(): Promise<Voice[]> {
        try {
            const response = await this.request<Record<string, Voice[]>>('/voices');
            // Flatten all voices from all providers into a single array
            const allVoices: Voice[] = [];
            Object.values(response).forEach(providerVoices => {
                allVoices.push(...providerVoices);
            });
            return allVoices;
        } catch (error) {
            console.error('Failed to fetch available voices:', error);
            return [];
        }
    }

    /**
     * Search for news articles
     */
    async searchNews(query: string, limit: number = 10): Promise<NewsSearchResult[]> {
        try {
            const response = await this.request<{ results: NewsSearchResult[] }>(
                `/research/news?query=${encodeURIComponent(query)}&limit=${limit}`
            );
            return response.results || [];
        } catch (error) {
            console.error('Failed to search news:', error);
            return [];
        }
    }

    /**
     * Search the web using available research providers
     */
    async searchWeb(query: string, engine: 'perplexity' | 'google' = 'perplexity', maxResults: number = 10, language: string = 'en'): Promise<WebSearchResult[]> {
        try {
            const response = await this.request<{ results: WebSearchResult[] }>(
                '/research/web',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        query,
                        engine,
                        max_results: maxResults,
                        language
                    })
                }
            );
            return response.results || [];
        } catch (error) {
            console.error('Failed to search the web:', error);
            throw error instanceof Error ? error : new Error('Unknown web search error');
        }
    }

    /**
     * Generate image from prompt
     */
    async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResult> {
        try {
            const response = await this.request<ImageGenerationResult>('/images/generate', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            return response;
        } catch (error) {
            console.error('Failed to generate image:', error);
            throw error;
        }
    }

    /**
     * Convert text to speech
     */
    async textToSpeech(request: TextToSpeechRequest): Promise<TextToSpeechResult> {
        try {
            const response = await this.request<TextToSpeechResult>('/audio/speech', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            return response;
        } catch (error) {
            console.error('Failed to generate speech:', error);
            throw error;
        }
    }

    /**
     * Create short video from scenes
     */
    async createShortVideo(request: ShortVideoRequest): Promise<ShortVideoResult> {
        try {
            const response = await this.request<ShortVideoResult>('/videos/short/create', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            return response;
        } catch (error) {
            console.error('Failed to create short video:', error);
            throw error;
        }
    }

    /**
     * Get job status
     */
    async getJobStatus(jobId: string): Promise<unknown> {
        try {
            const response = await this.request<unknown>(`/jobs/${jobId}/status`);
            return response;
        } catch (error) {
            console.error('Failed to get job status:', error);
            throw error;
        }
    }

    /**
     * Generate video from text prompt
     */
    async generateVideo(request: VideoGenerationRequest): Promise<VideoGenerationResult> {
        try {
            const response = await this.request<VideoGenerationResult>('/videos/generate', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            return response;
        } catch (error) {
            console.error('Failed to generate video:', error);
            throw error;
        }
    }

    /**
     * Get all available music tracks
     */
    async getMusicTracks(mood?: string): Promise<MusicTracksResponse> {
        try {
            const endpoint = mood ? `/music/tracks?mood=${encodeURIComponent(mood)}` : '/music/tracks';
            const response = await this.request<MusicTracksResponse>(endpoint);
            return response;
        } catch (error) {
            console.error('Failed to fetch music tracks:', error);
            throw error;
        }
    }

    /**
     * Get available music moods
     */
    async getMusicMoods(): Promise<MusicMoodsResponse> {
        try {
            const response = await this.request<MusicMoodsResponse>('/music/moods');
            return response;
        } catch (error) {
            console.error('Failed to fetch music moods:', error);
            throw error;
        }
    }

    /**
     * Get details for a specific music track
     */
    async getMusicTrack(filename: string): Promise<{ success: boolean; track: MusicTrack }> {
        try {
            const response = await this.request<{ success: boolean; track: MusicTrack }>(
                `/music/tracks/${encodeURIComponent(filename)}`
            );
            return response;
        } catch (error) {
            console.error('Failed to fetch music track:', error);
            throw error;
        }
    }
}

// Export singleton instance
export const griotApi = GriotApiService.getInstance();
