export interface AdvancedVideoSettingsProps {
  // Video settings
  video_orientation: string;
  crossfade_duration: number;
  frame_rate: number;
  output_width?: number;
  output_height?: number;
  
  // Caption settings
  add_captions: boolean;
  caption_style: string;
  caption_color?: string;
  highlight_color?: string;
  caption_position?: string;
  font_size?: number;
  font_family?: string;
  words_per_line?: number;
  margin_v?: number;
  outline_width?: number;
  all_caps?: boolean;
  
  // Music settings
  background_music: string;
  background_music_volume: number;
  generate_background_music?: boolean;
  music_duration?: number;
  
  // AI Image settings (for aiimage-to-video)
  image_width?: number;
  image_height?: number;
  inference_steps?: number;
  guidance_scale?: number;
  image_provider?: string;
  
  // Video effects
  video_effect?: string;
  
  // Background footage settings
  footage_provider?: string;
  search_safety?: string;
  footage_quality?: string;
  search_terms_per_scene?: number;
  
  // Change handlers - properly typed instead of 'any'
  // eslint-disable-next-line no-unused-vars
  onChange: (field: string, value: string | number | boolean) => void;
  
  // Control which sections to show
  showImageSettings?: boolean;
  showMusicGeneration?: boolean;
  showVideoEffects?: boolean;
  showImageProviderSettings?: boolean;
}

// Type for video orientation options
export type VideoOrientation = {
  readonly value: string;
  readonly label: string;
  readonly width: number;  
  readonly height: number;
};

// Type for caption styles
export type CaptionStyle = {
  readonly value: string;
  readonly label: string;
};

// Type for caption colors
export type CaptionColor = {
  readonly value: string;
  readonly label: string;
};

// Type for music options
export type MusicOption = {
  readonly value: string;
  readonly label: string;
};

// Type for video effects
export type VideoEffect = {
  readonly value: string;
  readonly label: string;
};