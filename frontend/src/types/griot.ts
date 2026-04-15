// Griot Types - Adapted for Frontend

// Job Management
export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum JobType {
  SHORT_VIDEO_CREATION = 'short_video_creation',
  FOOTAGE_TO_VIDEO = 'footage_to_video',
  AIIMAGE_TO_VIDEO = 'aiimage_to_video',
  AI_SCRIPT_GENERATION = 'ai_script_generation',
  VIDEO_SEARCH_QUERY_GENERATION = 'video_search_query_generation'
}

export interface Job {
  job_id: string;
  id?: string; // Alternative ID field for compatibility
  type?: JobType; // Job type
  status: JobStatus;
  operation?: string; // Job operation type
  params?: Record<string, any>; // Job input parameters
  result?: any;
  error?: string;
  progress?: number;
  created_at?: string;
  updated_at?: string;
}

export interface JobResponse {
  job_id: string;
}

// MCP Protocol Types
export interface MCPRequest {
  jsonrpc: string;
  id?: string;
  method: string;
  params?: Record<string, any>;
}

export interface MCPResponse {
  jsonrpc: string;
  id?: string;
  result?: Record<string, any>;
  error?: Record<string, any>;
}

// Video Creation Types
export interface Scene {
  text: string;
  searchTerms: string[];
  duration?: number;
}

export interface VideoConfig {
  voice_provider?: string;
  voice_name?: string;
  language?: string;
  background_music?: string;
  resolution?: string;
  fps?: number;
  orientation?: 'portrait' | 'landscape' | 'square';
  caption_style?: string;
  caption_color?: string;
  caption_position?: string;
  max_duration?: number;
}

export interface CreateVideoParams {
  scenes: Scene[];
  voice_provider?: string;
  voice_name?: string;
  language?: string;
  background_music?: string;
  resolution?: string;
  fps?: number;
  caption_style?: string;
  caption_color?: string;
  caption_position?: string;
  max_duration?: number;
}

// Short Video Creation
export interface ShortVideoCreationRequest {
  topic?: string;
  auto_topic?: boolean;
  language?: string;
  script_provider?: string;
  script_type?: string;
  max_duration?: number;
  voice?: string;
  tts_provider?: string;
  tts_speed?: number;
  video_orientation?: string;
  segment_duration?: number;
  add_captions?: boolean;
  caption_style?: string;
  output_width?: number;
  output_height?: number;
  frame_rate?: number;
}

export interface ShortVideoCreationResult {
  final_video_url: string;
  video_with_audio_url: string;
  script_generated: string;
  audio_url: string;
  background_videos_used: string[];
  srt_url?: string;
  video_duration: number;
  processing_time: number;
  word_count: number;
  segments_count: number;
}

// Topic to Video
export interface FootageToVideoRequest {
  topic?: string;
  custom_script?: string;
  auto_topic?: boolean;
  language?: string;
  script_provider?: string;
  script_type?: string;
  max_duration?: number;
  voice?: string;
  tts_provider?: string;
  tts_speed?: number;
  enable_voice_over?: boolean;
  enable_built_in_audio?: boolean;
  orientation?: string;
  media_type?: 'video' | 'image';
  footage_provider?: string;
  ai_video_provider?: string;
  ai_video_model?: string;
  add_captions?: boolean;
  caption_style?: string;
  caption_color?: string;
  caption_position?: string;
  image_width?: number;
  image_height?: number;
  frame_rate?: number;
  crossfade_duration?: number;
  background_music?: string;
  background_music_volume?: number;
  image_provider?: string;
  guidance_scale?: number;
  footage_quality?: string;
}

export interface AiimageToVideoRequest {
  topic?: string;
  custom_script?: string;
  auto_topic?: boolean;
  language?: string;
  script_provider?: string;
  script_type?: string;
  max_duration?: number;
  voice?: string;
  tts_provider?: string;
  tts_speed?: number;
  enable_voice_over?: boolean;
  enable_built_in_audio?: boolean;
  orientation?: string;
  media_type?: 'video' | 'image';
  footage_provider?: string;
  ai_video_provider?: string;
  ai_video_model?: string;
  add_captions?: boolean;
  caption_style?: string;
  caption_color?: string;
  caption_position?: string;
  image_width?: number;
  image_height?: number;
  frame_rate?: number;
  crossfade_duration?: number;
  generate_background_music?: boolean;
  background_music?: string;
  music_duration?: number;
  background_music_volume?: number;
  video_effect?: string;
  inference_steps?: number;
  image_provider?: string;
  guidance_scale?: number;
  footage_quality?: string;
}

export interface AiimageToVideoResult {
  final_video_url: string;
  video_with_audio_url: string;
  script_generated: string;
  audio_url: string;
  generated_images: Array<{
    url: string;
    prompt: string;
    index: number;
  }>;
  background_music_url?: string;
  music_prompt_generated?: string;
  srt_url?: string;
  video_duration: number;
  processing_time: number;
  word_count: number;
  segments_count: number;
  segments_data: Array<{
    start_time: number;
    end_time: number;
    text: string;
    prompt: string;
  }>;
}

export interface FootageToVideoResult extends ShortVideoCreationResult { }

// Script Generation
export interface ScriptGenerationRequest {
  topic?: string;
  auto_topic?: boolean;
  provider?: string;
  script_type?: string;
  max_duration?: number;
  target_words?: number;
  language?: string;
  sync?: boolean;
}

export interface ScriptGenerationResult {
  script: string;
  word_count: number;
  estimated_duration: number;
  provider_used: string;
  model_used: string;
}

// Video Status
export type VideoStatus = 'processing' | 'ready' | 'failed' | 'pending';

export interface VideoDetails {
  id: string;
  status: VideoStatus;
  url?: string;
  title?: string;
  created_at?: string;
  duration?: number;
  progress?: number;
  error?: string;
}

// Voice and Provider Types
export interface VoiceInfo {
  name: string;
  display_name?: string;
  locale: string;
  gender: string;
}

export interface VoiceProvider {
  name: string;
  voices: string[];
  languages: string[];
}

export interface VoiceOptions {
  providers: string[];
  voices: Record<string, Record<string, VoiceInfo[]>>;  // provider -> language -> voice[]
  provider_info: Record<string, VoiceProvider>;
  total_voices?: number;
  source?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T> {
  page?: number;
  per_page?: number;
  total?: number;
}

// Research Types (for VideoResearcher)
export interface ResearchResult {
  title: string;
  content: string;
  sources: string[];
  language: string;
}

export interface ResearchRequest {
  searchTerm: string;
  targetLanguage: string;
}

// Error Types
export interface ApiError {
  code: number | string;
  message: string;
  details?: any;
}

// Constants
export const SCRIPT_TYPES = [
  'facts',
  'story',
  'educational',
  'motivation',
  'prayer',
  'pov',
  'conspiracy',
  'life_hacks',
  'would_you_rather',
  'before_you_die',
  'dark_psychology',
  'reddit_stories',
  'shower_thoughts',
  'daily_news'
] as const;

export const VIDEO_ORIENTATIONS = [
  'portrait',
  'landscape',
  'square'
] as const;

export const CAPTION_STYLES = [
  'viral_bounce',
  'tiktok_viral',
  'instagram_reels',
  'youtube_standard',
  'bounce',
  'karaoke',
  'highlight',
  'underline',
  'word_by_word',
  'typewriter',
  'fade_in',
  'classic',
  'modern_neon',
  'cinematic_glow',
  'social_pop',
  'dramatic',
  'educational',
  'corporate',
  'minimal',
  'accessibility',
] as const;

// Caption color options for viral styles
export const CAPTION_COLORS = [
  { name: 'Blue', value: '#007AFF', label: 'Classic Blue' },
  { name: 'Cyan', value: '#00FFFF', label: 'Viral Cyan' },
  { name: 'Yellow', value: '#FFFF00', label: 'Viral Yellow' },
  { name: 'Green', value: '#00FF00', label: 'Viral Green' },
  { name: 'Pink', value: '#FF69B4', label: 'Hot Pink' },
  { name: 'Orange', value: '#FF4500', label: 'Orange Red' },
  { name: 'Purple', value: '#8A2BE2', label: 'Blue Violet' },
  { name: 'Red', value: '#FF0000', label: 'Pure Red' },
  { name: 'White', value: '#FFFFFF', label: 'Pure White' },
  { name: 'Black', value: '#000000', label: 'Pure Black' }
] as const;

// Caption positions
export const CAPTION_POSITIONS = [
  'top_left',
  'top_center',
  'top_right',
  'middle_left',
  'middle_center',
  'middle_right',
  'bottom_left',
  'bottom_center',
  'bottom_right'
] as const;

export const TTS_PROVIDERS = [
  'kokoro',
  'edge',
  'piper'
] as const;

export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'nl', name: 'Dutch' }
] as const;

export type ScriptType = typeof SCRIPT_TYPES[number];
export type VideoOrientation = typeof VIDEO_ORIENTATIONS[number];
export type CaptionStyle = typeof CAPTION_STYLES[number];
export type CaptionColor = typeof CAPTION_COLORS[number];
export type CaptionPosition = typeof CAPTION_POSITIONS[number];
export type TTSProvider = typeof TTS_PROVIDERS[number];
export type LanguageCode = typeof LANGUAGES[number]['code'];

// Music types and constants
export interface MusicTrack {
  file: string;
  title: string;
  start: number;
  end: number;
  mood: string;
  duration: number;
}

export const MUSIC_MOODS = [
  { value: 'sad', label: 'Sad' },
  { value: 'melancholic', label: 'Melancholic' },
  { value: 'happy', label: 'Happy' },
  { value: 'euphoric', label: 'Euphoric' },
  { value: 'excited', label: 'Excited' },
  { value: 'chill', label: 'Chill' },
  { value: 'uneasy', label: 'Uneasy' },
  { value: 'angry', label: 'Angry' },
  { value: 'dark', label: 'Dark' },
  { value: 'hopeful', label: 'Hopeful' },
  { value: 'contemplative', label: 'Contemplative' },
  { value: 'funny', label: 'Funny' }
] as const;

export type MusicMood = typeof MUSIC_MOODS[number]['value'];

// Enhanced music options that combine AI generation and mood selection
export const BACKGROUND_MUSIC_OPTIONS = [
  { value: 'none', label: 'No Background Music', type: 'none' },
  { value: 'ai_generate', label: 'AI Generated Music', type: 'ai_generate' },
  ...MUSIC_MOODS.map(mood => ({
    value: mood.value,
    label: `${mood.label} (Stock Music)`,
    type: 'mood'
  }))
] as const;

export const MUSIC_OPTIONS = [
  { value: 'none', label: 'No Background Music' },
  { value: 'generate', label: 'AI Generated Music' }
] as const;

// Video creation methods
export const VIDEO_CREATION_METHODS = [
  {
    value: 'stock_videos',
    label: 'Stock Video Backgrounds',
    description: 'Use real stock footage from Pexels as video backgrounds'
  },
  {
    value: 'ai_images',
    label: 'AI Generated Images',
    description: 'Create custom AI-generated images for each scene'
  }
] as const;

// Video effects for AI image videos
export const VIDEO_EFFECTS = [
  { value: 'zoom', label: 'Zoom Effect' },
  { value: 'pan', label: 'Pan Effect' },
  { value: 'ken_burns', label: 'Ken Burns Effect' },
  { value: 'fade', label: 'Fade Transition' }
] as const;

export type VideoCreationMethod = typeof VIDEO_CREATION_METHODS[number]['value'];
export type VideoEffect = typeof VIDEO_EFFECTS[number]['value'];