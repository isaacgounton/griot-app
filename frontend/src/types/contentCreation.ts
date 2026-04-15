// Video Scene Types (still used by some components)
export interface VideoScene {
  text: string;
  duration: number;
  searchTerms?: string[];
}

// Video Creation Types - Topic-based approach
export interface VideoCreationRequest {
  // Core topic/script
  topic?: string;
  script?: string; // For when user provides their own script (legacy)
  custom_script?: string; // For backend compatibility - maps to script
  auto_topic?: boolean;

  // Script generation
  script_type?: string;
  script_provider?: string;
  max_duration?: number;
  language: string;

  // Voice/TTS options
  voice: string; // voice name
  tts_provider: string; // kokoro, edge
  enable_voice_over?: boolean;
  enable_built_in_audio?: boolean;
  tts_speed?: number;

  // Image generation options (for AI images)
  image_provider?: string; // together, flux
  image_model?: string;
  image_width?: number;
  image_height?: number;
  image_steps?: number;
  guidance_scale?: number;

  // Video options
  video_effect?: string;
  orientation?: string;
  resolution?: string;
  aspect_ratio?: string;
  frame_rate?: number; // 24-60 fps
  crossfade_duration?: number; // crossfade between segments (0.0-1.0s)

  // Audio options
  generate_background_music?: boolean;
  background_music?: string; // For footage-to-video: 'none', 'ai_generate', or mood name
  background_music_volume?: number;
  music_prompt?: string;
  music_duration?: number;

  // Caption options
  add_captions?: boolean;
  caption_style?: string;
  caption_color?: string;
  highlight_color?: string;
  caption_position?: string;
  font_size?: number;
  font_family?: string;
  words_per_line?: number;
  margin_v?: number;
  outline_width?: number;
  all_caps?: boolean;

  // Footage provider options
  footage_provider?: string;
  ai_video_provider?: string; // modal_video, wavespeed, pollinations - for when footage_provider is 'ai_generated'
  ai_video_model?: string; // For Pollinations: veo, seedance, seedance-pro
  media_type?: 'video' | 'image'; // IMPORTANT: determines whether to fetch videos or images
  search_safety?: string;
  footage_quality?: string;
  search_terms_per_scene?: number;
}

export interface VideoCreationResult {
  video_url: string;
  thumbnail_url?: string;
  duration?: number;
  file_size?: number;
  metadata?: {
    resolution: string;
    aspect_ratio: string;
    total_scenes: number;
    voice_used: string;
    caption_style: string;
  };
  // Dynamic properties for video results
  final_video_url?: string;
  video_with_audio_url?: string;
  output_video_url?: string;
  srt_url?: string;
  video_duration?: number;
  resolution?: string;
  processing_time?: number;
  file_size_mb?: number;
  word_count?: number;
  segments_count?: number;
  // Additional dynamic properties
  [key: string]: unknown;
}

// Research Types
export interface TopicResearchRequest {
  topic: string;
  language: string;
  video_length?: number;
  voice_provider?: string;
  voice_name?: string;
  research_depth?: 'basic' | 'detailed' | 'comprehensive';
  target_audience?: string;
  content_style?: 'educational' | 'entertaining' | 'viral' | 'informative';
}

export interface TopicResearchResult {
  video_url: string;
  script: {
    title: string;
    scenes: VideoScene[];
    total_duration: number;
    research_sources?: string[];
  };
  thumbnail_url?: string;
  metadata?: {
    research_quality: string;
    sources_used: number;
    confidence_score: number;
  };
  // Allow dynamic properties
  [key: string]: unknown;
}

// Voice Types
export interface VoiceInfo {
  name: string;
  gender: string;
  language: string;
  description?: string;
  grade?: string;
  provider: 'kokoro' | 'edge' | 'piper';
}

export interface VoiceProviderInfo {
  name: string;
  voices: VoiceInfo[];
  languages: string[];
}

// Job Status Types
export type ContentCreationJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ContentCreationJobResult {
  job_id: string;
  status: ContentCreationJobStatus;
  result?: VideoCreationResult | TopicResearchResult;
  error?: string;
  progress?: string;
  created_at?: string;
  updated_at?: string;
}

// Form State Types - Topic-based
export interface VideoCreatorFormState {
  topic: string;
  script: string; // Optional custom script
  useCustomScript: boolean; // Toggle between topic and custom script
  voiceProvider: string;
  voiceName: string;
  language: string;
  imageWidth: number;
  imageHeight: number;
  aspectRatio: string;
  frameRate?: number; // 24-60 fps
  crossfadeDuration?: number; // crossfade between segments (0.0-1.0s)
  captionStyle: string;
  captionColor?: string;
  highlightColor?: string;
  captionPosition?: string; // top_left, top_center, etc.
  fontSize?: number;
  fontFamily?: string;
  wordsPerLine?: number;
  marginV?: number;
  outlineWidth?: number;
  allCaps?: boolean;
  footageProvider: string;
  aiVideoProvider: string; // modal_video, wavespeed, pollinations
  aiVideoModel?: string; // For Pollinations: veo, seedance, seedance-pro
  enableVoiceOver: boolean;
  enableBuiltInAudio: boolean;
  searchSafety: string;
  searchTermsPerScene?: number; // Number of search terms per video segment
  enableCaptions: boolean;
  backgroundMusic: string;
  backgroundMusicVolume: number;
  musicDuration?: number;
  footageQuality: string; // Renamed from imageQuality for clarity
  scriptType: string;
  maxDuration: number;
  ttsSpeed: number;
  videoEffect: string;
  generateBackgroundMusic: boolean;
}

export interface TopicResearchFormState {
  topic: string;
  language: string;
  videoLength: number;
  voiceProvider: string;
  voiceName: string;
  researchDepth: 'basic' | 'detailed' | 'comprehensive';
  targetAudience: string;
  contentStyle: 'educational' | 'entertaining' | 'viral' | 'informative';
}

// Consolidated Settings Types
export interface MediaSettings {
  // Video Format & Quality
  imageWidth: number;
  imageHeight: number;
  aspectRatio: string;
  frameRate?: number; // 24-60 fps
  crossfadeDuration?: number; // crossfade between segments
  captionStyle: string;
  captionColor?: string;
  captionPosition?: string; // top, center, bottom
  enableCaptions: boolean;
  backgroundMusic: string;
  backgroundMusicVolume: number;
  musicDuration?: number;

  // Video Footage Provider Settings
  footageProvider: string; // Renamed from imageProvider for clarity
  searchSafety: string;
  footageQuality?: string; // Renamed from imageQuality for clarity
  searchTermsPerScene?: number;
}

// Legacy types for backwards compatibility
export interface VideoSettings {
  resolution: string;
  aspectRatio: string;
  captionStyle: string;
  enableCaptions: boolean;
  enableBackgroundMusic: boolean;
  musicVolume: number;
}

export interface ImageProviderSettings {
  provider: string;
  searchSafety: string;
  imageQuality?: string;
  searchTermsPerScene?: number;
}

// UI State Types
export interface ContentCreationUIState {
  currentTab: number;
  isLoading: boolean;
  error: string | null;
  showAdvancedSettings: boolean;
  jobId: string | null;
  jobStatus: ContentCreationJobStatus | null;
  progress: string;
}

// Constants
export const VOICE_PROVIDERS = ['kokoro', 'edge', 'piper'] as const;
export const LANGUAGES = ['en', 'fr', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'] as const;

// Image Dimensions (replacing resolution concept)
export const IMAGE_PRESETS = [
  { name: 'Portrait (TikTok/Reels)', width: 1080, height: 1920, aspectRatio: '9:16' },
  { name: 'Landscape (YouTube)', width: 1920, height: 1080, aspectRatio: '16:9' },
  { name: 'Square (Instagram)', width: 1080, height: 1080, aspectRatio: '1:1' },
  { name: 'Portrait (Stories)', width: 1080, height: 1350, aspectRatio: '4:5' },
  { name: 'HD Portrait', width: 720, height: 1280, aspectRatio: '9:16' },
  { name: 'HD Landscape', width: 1280, height: 720, aspectRatio: '16:9' },
] as const;

export const ASPECT_RATIOS = ['9:16', '16:9', '1:1', '4:5'] as const;
export const RESEARCH_DEPTHS = ['basic', 'detailed', 'comprehensive'] as const;
export const CONTENT_STYLES = ['educational', 'entertaining', 'viral', 'informative'] as const;
// Video footage providers and quality settings
export const FOOTAGE_PROVIDERS = ['pexels', 'pixabay', 'ai_generated'] as const;
export const AI_VIDEO_PROVIDERS = ['pollinations', 'modal_video', 'wavespeed', 'comfyui'] as const;
export const SEARCH_SAFETY_LEVELS = ['strict', 'moderate', 'off'] as const;
export const FOOTAGE_QUALITIES = ['standard', 'high', 'ultra'] as const;
export const FRAME_RATES = [24, 30, 60] as const;
export const CROSSFADE_DURATIONS = [0.0, 0.2, 0.3, 0.5, 0.8, 1.0] as const;
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

export type VoiceProvider = typeof VOICE_PROVIDERS[number];
export type Language = typeof LANGUAGES[number];
export type ImagePreset = typeof IMAGE_PRESETS[number];
export type AspectRatio = typeof ASPECT_RATIOS[number];
export type ResearchDepth = typeof RESEARCH_DEPTHS[number];
export type ContentStyle = typeof CONTENT_STYLES[number];
// Accurate type names for video footage parameters
export type FootageProvider = typeof FOOTAGE_PROVIDERS[number];
export type AIVideoProvider = typeof AI_VIDEO_PROVIDERS[number];
export type SearchSafetyLevel = typeof SEARCH_SAFETY_LEVELS[number];
export type FootageQuality = typeof FOOTAGE_QUALITIES[number];
export type FrameRate = typeof FRAME_RATES[number];
export type CrossfadeDuration = typeof CROSSFADE_DURATIONS[number];
export type CaptionPosition = typeof CAPTION_POSITIONS[number];