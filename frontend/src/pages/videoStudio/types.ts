export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export interface StudioScene {
  id: string;
  order_index: number;
  script_text: string;
  status: 'empty' | 'scripted' | 'audio_ready' | 'media_ready' | 'preview_ready' | 'failed';
  tts_audio_url: string | null;
  tts_audio_duration: number | null;
  word_timestamps: WordTimestamp[] | null;
  media_source_type: string | null;
  media_url: string | null;
  media_search_terms: string[] | null;
  media_prompt: string | null;
  media_provider: string | null;
  start_time: number;
  duration: number;
  transition_type: string | null;
  transition_duration: number;
  preview_url: string | null;
  thumbnail_url: string | null;
}

export interface AudioTrack {
  id: string;
  track_type: 'voiceover' | 'background_music' | 'sound_effect';
  name: string;
  audio_url: string;
  start_time: number;
  duration: number | null;
  volume: number;
  fade_in: number;
  fade_out: number;
}

export interface ProjectSettings {
  resolution: { width: number; height: number };
  frame_rate: number;
  tts_provider: string;
  voice_name: string;
  voice_speed: number;
  language: string;
  caption_style: string;
  caption_properties: Record<string, unknown>;
  background_music: string | null;
  background_music_volume: number;
  crossfade_duration: number;
  footage_provider: string;
  ai_video_provider: string;
  ai_image_provider: string;
  media_type: string;
}

export interface StudioProject {
  id: string;
  name: string;
  description: string | null;
  status: 'draft' | 'generating' | 'completed' | 'failed';
  settings: ProjectSettings;
  scenes: StudioScene[];
  audio_tracks: AudioTrack[];
  total_duration: number;
  final_video_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  status: string;
  scene_count: number;
  total_duration: number;
  thumbnail_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

export const SCENE_STATUS_LABELS: Record<string, string> = {
  empty: 'Empty',
  scripted: 'Script Ready',
  audio_ready: 'Audio Ready',
  media_ready: 'Media Ready',
  preview_ready: 'Preview Ready',
  failed: 'Failed',
};

export const SCENE_STATUS_COLORS: Record<string, string> = {
  empty: '#9e9e9e',
  scripted: '#ff9800',
  audio_ready: '#2196f3',
  media_ready: '#4caf50',
  preview_ready: '#8bc34a',
  failed: '#f44336',
};

// ── Quick Create / Scene Builder form state ───────────────────────────

export interface FormState {
  topic: string;
  script: string;
  useCustomScript: boolean;
  voiceProvider: string;
  voiceName: string;
  language: string;
  enableVoiceOver: boolean;
  enableBuiltInAudio: boolean;
  imageWidth: number;
  imageHeight: number;
  aspectRatio: string;
  captionStyle: string;
  captionColor: string;
  highlightColor: string;
  captionPosition: string;
  fontSize: number;
  fontFamily: string;
  wordsPerLine: number;
  marginV: number;
  outlineWidth: number;
  allCaps: boolean;
  footageProvider: string;
  aiVideoProvider: string;
  aiVideoModel: string;
  aiVideoAudio: boolean;
  searchSafety: string;
  enableCaptions: boolean;
  backgroundMusic: string;
  backgroundMusicVolume: number;
  musicDuration: number;
  footageQuality: string;
  scriptType: string;
  maxDuration: number;
  ttsSpeed: number;
  videoEffect: string;
  generateBackgroundMusic: boolean;
  frameRate: number;
  crossfadeDuration: number;
  searchTermsPerScene: number;
  mediaType: string;
  aiImageProvider: string;
  aiImageModel: string;
  guidanceScale: number;
  inferenceSteps: number;
  effectType: string;
  zoomSpeed: number;
  panDirection: string;
  kenBurnsKeypoints: Array<{ time: number; x: number; y: number; zoom: number }>;
  autoDiscovery: boolean;
  researchDepth: string;
  targetAudience: string;
  contentStyle: string;
  scenes: Array<{ text: string; duration: number; searchTerms: string[] }>;
}

export const DEFAULT_FORM_STATE: FormState = {
  topic: '', script: '', useCustomScript: true,
  voiceProvider: 'edge', voiceName: 'en-US-AriaNeural', language: 'en',
  enableVoiceOver: true, enableBuiltInAudio: false,
  imageWidth: 1080, imageHeight: 1920, aspectRatio: '9:16',
  captionStyle: 'viral_bounce', captionColor: '#FFFFFF', highlightColor: '#FFFF00',
  captionPosition: 'bottom_center', fontSize: 48, fontFamily: 'Arial-Bold',
  wordsPerLine: 6, marginV: 100, outlineWidth: 4, allCaps: false,
  footageProvider: 'ai_generated', aiVideoProvider: 'pollinations',
  aiVideoModel: 'veo', aiVideoAudio: false,
  searchSafety: 'moderate', enableCaptions: true,
  backgroundMusic: 'chill', backgroundMusicVolume: 0.3, musicDuration: 60,
  footageQuality: 'high', scriptType: 'facts', maxDuration: 60,
  ttsSpeed: 1.0, videoEffect: 'ken_burns', generateBackgroundMusic: false,
  frameRate: 30, crossfadeDuration: 0.3, searchTermsPerScene: 3,
  mediaType: 'video', aiImageProvider: 'together',
  aiImageModel: 'black-forest-labs/flux.1-schnell',
  guidanceScale: 3.5, inferenceSteps: 4,
  effectType: 'ken_burns', zoomSpeed: 50, panDirection: 'left_to_right',
  kenBurnsKeypoints: [], autoDiscovery: false,
  researchDepth: 'basic', targetAudience: 'general', contentStyle: 'entertaining',
  scenes: [{ text: '', duration: 3, searchTerms: [''] }],
};
