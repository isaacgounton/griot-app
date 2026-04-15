export interface BackgroundMusicSettingsProps {
  // Music settings
  background_music: string;
  background_music_volume: number;
  generate_background_music?: boolean;
  music_duration?: number;
  music_prompt?: string;
  
  // Change handlers - properly typed instead of 'any'
  // eslint-disable-next-line no-unused-vars
  onChange: (field: string, value: string | number | boolean) => void;
  
  // Control which sections to show
  showMusicGeneration?: boolean;
  showMusicPrompt?: boolean;
  showAdvancedSettings?: boolean;
  
  // Optional styling
  compact?: boolean;
  hideVolumeSlider?: boolean;
  hideHeader?: boolean;
}

// Type for music generation modes
export type MusicGenerationMode = 'ai_generate' | 'stock_music' | 'none';

// Extended music option type with additional metadata
export type ExtendedMusicOption = {
  readonly value: string;
  readonly label: string;
  readonly category?: 'ai' | 'stock' | 'none';
  readonly description?: string;
};