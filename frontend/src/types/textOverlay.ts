// Text Overlay System Type Definitions

export interface TextOverlayPosition {
  x: number; // Percentage (0-100)
  y: number; // Percentage (0-100)
  alignment: 'left' | 'center' | 'right';
}

export interface TextOverlayTypography {
  fontFamily: string;
  fontSize: number; // Pixels
  fontWeight: number; // 100-900
  fontStyle: 'normal' | 'italic';
  letterSpacing: number; // Pixels
  lineHeight: number; // Multiplier (e.g., 1.4)
  textDecoration: 'none' | 'underline' | 'overline' | 'line-through';
}

export interface TextOverlayColors {
  text: string; // CSS color value
  background: string; // CSS color value (supports rgba)
  stroke: string; // CSS color value
}

export interface TextOverlayShadow {
  enabled: boolean;
  offsetX: number; // Pixels
  offsetY: number; // Pixels
  blur: number; // Pixels
  color: string; // CSS color value
}

export interface TextOverlayGradient {
  enabled: boolean;
  type: 'linear' | 'radial';
  colors: string[]; // Array of CSS color values
  direction: number; // Degrees (for linear gradients)
}

export interface TextOverlayStroke {
  enabled: boolean;
  width: number; // Pixels
}

export interface TextOverlayGlow {
  enabled: boolean;
  color: string; // CSS color value
  intensity: number; // Pixels
}

export interface TextOverlayEffects {
  shadow: TextOverlayShadow;
  gradient: TextOverlayGradient;
  stroke: TextOverlayStroke;
  glow: TextOverlayGlow;
}

export interface TextOverlayAnimation {
  enabled: boolean;
  type: 'fadeIn' | 'slideIn' | 'bounce' | 'typewriter' | 'pulse' | 'rotate';
  duration: number; // Milliseconds
  delay: number; // Milliseconds
  easing: 'linear' | 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out';
  loop: boolean;
}

export interface TextOverlayTiming {
  startTime: number; // Seconds
  duration: number; // Seconds
}

export interface ResponsiveTextOverlay {
  mobile: Partial<TextOverlayConfig>;
  tablet: Partial<TextOverlayConfig>;
}

export interface TextOverlayConfig {
  text: string;
  position: TextOverlayPosition;
  typography: TextOverlayTypography;
  colors: TextOverlayColors;
  effects: TextOverlayEffects;
  animation: TextOverlayAnimation;
  timing: TextOverlayTiming;
  responsive: ResponsiveTextOverlay;
}

// Preset and Template Types
export interface PresetTemplate {
  id: string;
  name: string;
  description: string;
  thumbnail: string; // Emoji or icon
  config: Partial<TextOverlayConfig>;
  tags: string[];
  popular: boolean;
  category?: 'social' | 'business' | 'creative' | 'minimal';
  platform?: 'tiktok' | 'instagram' | 'youtube' | 'twitter' | 'linkedin';
}

// API Response Types
export interface TextOverlayJob {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    video_url?: string;
    preview_url?: string;
    config?: TextOverlayConfig;
    metadata?: {
      duration?: number;
      resolution?: string;
      format?: string;
      file_size?: number;
    };
  };
  error?: string;
  progress?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TextOverlayPreviewRequest {
  config: TextOverlayConfig;
  width?: number;
  height?: number;
  format?: 'png' | 'jpg' | 'svg';
  quality?: number;
}

export interface TextOverlayVideoRequest {
  config: TextOverlayConfig;
  video_file?: File;
  video_url?: string;
  output_format?: 'mp4' | 'webm' | 'mov';
  quality?: 'low' | 'medium' | 'high' | 'ultra';
  resolution?: string; // e.g., "1920x1080"
}

// Hook Options and State
export interface UseTextOverlayOptions {
  apiKey?: string;
  apiBaseUrl?: string;
  autoSave?: boolean;
  autoSaveDelay?: number;
  enableHistory?: boolean;
  historyLimit?: number;
}

export interface TextOverlayState {
  config: TextOverlayConfig;
  savedConfigs: { [key: string]: TextOverlayConfig };
  currentJob: TextOverlayJob | null;
  isGenerating: boolean;
  previewUrl: string | null;
  history: TextOverlayConfig[];
  historyIndex: number;
}

// Event Types
export interface TextOverlayEvent {
  type: 'config_updated' | 'preset_applied' | 'export_completed' | 'import_completed' | 'job_completed';
  payload: any;
  timestamp: number;
}

// Validation and Error Types
export interface TextOverlayValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface TextOverlayError {
  code: string;
  message: string;
  field?: string;
  value?: any;
}

// Font and Color Palette Types
export interface FontOption {
  family: string;
  label: string;
  weights: number[];
  styles: ('normal' | 'italic')[];
  category: 'sans-serif' | 'serif' | 'monospace' | 'display' | 'handwriting';
}

export interface ColorPalette {
  name: string;
  colors: string[];
  category: 'classic' | 'modern' | 'pastel' | 'neon' | 'brand';
  description?: string;
}

// Editor UI Types
export interface EditorTab {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
}

export interface EditorSection {
  id: string;
  title: string;
  description?: string;
  collapsed?: boolean;
}

// Mobile-specific Types
export interface MobilePresetCategory {
  id: string;
  name: string;
  icon: string;
  presets: PresetTemplate[];
}

export interface MobileQuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
}

// Performance and Optimization Types
export interface TextOverlayMetrics {
  renderTime: number; // milliseconds
  configSize: number; // bytes
  previewGenerationTime: number; // milliseconds
  lastUpdated: number; // timestamp
}

export interface TextOverlayCacheEntry {
  key: string;
  config: TextOverlayConfig;
  previewUrl: string;
  timestamp: number;
  hits: number;
}

// Export all types
export * from './textOverlay';