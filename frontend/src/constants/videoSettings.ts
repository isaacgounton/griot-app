// Common video orientation options
export const VIDEO_ORIENTATIONS = [
  { value: 'portrait', label: 'Portrait (9:16)', width: 1080, height: 1920 },
  { value: 'landscape', label: 'Landscape (16:9)', width: 1920, height: 1080 },
  { value: 'square', label: 'Square (1:1)', width: 1080, height: 1080 }
] as const;

// Common caption styles (aligned with backend caption_styles.json presets)
// Note: The CaptionSettings component fetches styles dynamically from the API.
// This list is a reference fallback only.
export const CAPTION_STYLES = [
  { value: 'viral_bounce', label: 'Viral Bounce', description: 'Karaoke fill with bold viral look' },
  { value: 'tiktok_viral', label: 'TikTok Viral', description: 'TikTok-optimized karaoke style' },
  { value: 'instagram_reels', label: 'Instagram Reels', description: 'Reels-optimized karaoke style' },
  { value: 'youtube_standard', label: 'YouTube Standard', description: 'Clean readable subtitles' },
  { value: 'bounce', label: 'Bounce', description: 'Scale pop + karaoke fill per word' },
  { value: 'karaoke', label: 'Karaoke', description: 'Smooth word color fill' },
  { value: 'highlight', label: 'Highlight', description: 'Full text with current word colored' },
  { value: 'underline', label: 'Underline', description: 'Full text with current word underlined' },
  { value: 'word_by_word', label: 'Word by Word', description: 'One word at a time' },
  { value: 'typewriter', label: 'Typewriter', description: 'Character-by-character reveal' },
  { value: 'fade_in', label: 'Fade In', description: 'Smooth line fade-in' },
  { value: 'classic', label: 'Classic', description: 'Static subtitles' },
  { value: 'modern_neon', label: 'Modern Neon', description: 'Neon-colored karaoke' },
  { value: 'cinematic_glow', label: 'Cinematic Glow', description: 'Cinematic karaoke style' },
  { value: 'social_pop', label: 'Social Pop', description: 'Social media bounce style' },
  { value: 'dramatic', label: 'Dramatic', description: 'Large word-by-word dramatic' },
  { value: 'educational', label: 'Educational', description: 'Clear highlight for learning' },
  { value: 'corporate', label: 'Corporate', description: 'Professional clean subtitles' },
  { value: 'minimal', label: 'Minimal', description: 'Minimal static subtitles' },
  { value: 'accessibility', label: 'Accessibility', description: 'High-contrast accessible' },
] as const;

// Common caption colors (hex codes for backend compatibility)
export const CAPTION_COLORS = [
  { value: '#FFFFFF', label: 'White', name: 'white' },
  { value: '#FFFF00', label: 'Yellow', name: 'yellow' },
  { value: '#00FFFF', label: 'Cyan', name: 'cyan' },
  { value: '#00FF00', label: 'Green', name: 'green' },
  { value: '#FF0000', label: 'Red', name: 'red' },
  { value: '#0080FF', label: 'Blue', name: 'blue' },
  { value: '#8000FF', label: 'Purple', name: 'purple' },
  { value: '#FFA500', label: 'Orange', name: 'orange' },
  { value: '#FF1493', label: 'Hot Pink', name: 'hotpink' },
  { value: '#00FF80', label: 'Lime Green', name: 'limegreen' }
] as const;

// Common music options
export const MUSIC_OPTIONS = [
  { value: 'none', label: 'No Music', category: 'none', description: 'No background music will be added' },
  { value: 'ai_generate', label: 'AI Generated', category: 'ai', description: 'Generate custom music using AI' },
  { value: 'chill', label: 'Chill', category: 'stock', description: 'Relaxed and mellow background music' },
  { value: 'happy', label: 'Happy', category: 'stock', description: 'Upbeat and positive background music' },
  { value: 'dark', label: 'Dark', category: 'stock', description: 'Mysterious and atmospheric background music' },
  { value: 'hopeful', label: 'Hopeful', category: 'stock', description: 'Inspiring and uplifting background music' },
  { value: 'sad', label: 'Sad', category: 'stock', description: 'Melancholy and emotional background music' },
  { value: 'melancholic', label: 'Melancholic', category: 'stock', description: 'Thoughtful and introspective background music' },
  { value: 'euphoric', label: 'Euphoric', category: 'stock', description: 'High-energy and celebratory background music' },
  { value: 'excited', label: 'Excited', category: 'stock', description: 'Energetic and dynamic background music' },
  { value: 'uneasy', label: 'Uneasy', category: 'stock', description: 'Tense and suspenseful background music' },
  { value: 'angry', label: 'Angry', category: 'stock', description: 'Intense and aggressive background music' }
] as const;

// Music volume presets
export const MUSIC_VOLUME_PRESETS = [
  { value: 0.1, label: '10%' },
  { value: 0.2, label: '20%' },
  { value: 0.3, label: '30%' },
  { value: 0.5, label: '50%' },
  { value: 0.8, label: '80%' }
] as const;

// Music duration presets
export const MUSIC_DURATION_PRESETS = [
  { value: 30, label: '30s' },
  { value: 60, label: '1m' },
  { value: 120, label: '2m' },
  { value: 180, label: '3m' },
  { value: 300, label: '5m' }
] as const;

// Common video effects
export const VIDEO_EFFECTS = [
  { value: 'zoom', label: 'Zoom Effect' },
  { value: 'pan', label: 'Pan Effect' },
  { value: 'ken_burns', label: 'Ken Burns Effect' },
  { value: 'fade', label: 'Fade Transition' }
] as const;

// Caption font families (aligned with available fonts in /fonts directory)
export const CAPTION_FONT_FAMILIES = [
  // Sans-serif - Popular for captions
  { value: 'Arial-Bold', label: 'Arial Bold', category: 'sans-serif', recommended: true },
  { value: 'Helvetica-Bold', label: 'Helvetica Bold', category: 'sans-serif', recommended: true },
  { value: 'Roboto-Bold', label: 'Roboto Bold', category: 'sans-serif', recommended: true },
  { value: 'Montserrat-Bold', label: 'Montserrat Bold', category: 'sans-serif', recommended: true },
  { value: 'OpenSans-Bold', label: 'Open Sans Bold', category: 'sans-serif', recommended: true },
  
  // Display fonts - Great for viral content
  { value: 'Oswald-VariableFont_wght', label: 'Oswald Bold', category: 'display', recommended: true },
  { value: 'PermanentMarker-Regular', label: 'Permanent Marker', category: 'display', recommended: false },
  { value: 'LuckiestGuy-Regular', label: 'Luckiest Guy', category: 'display', recommended: false },
  { value: 'FrederickatheGreat-Regular', label: 'Fredericka the Great', category: 'display', recommended: false },
  { value: 'Pacifico-Regular', label: 'Pacifico', category: 'script', recommended: false },
  { value: 'Shrikhand-Regular', label: 'Shrikhand', category: 'display', recommended: false },
  
  // Additional options
  { value: 'DejaVuSans-Bold', label: 'DejaVu Sans Bold', category: 'sans-serif', recommended: false },
  { value: 'ComicNeue-Bold', label: 'Comic Neue Bold', category: 'casual', recommended: false },
  { value: 'TheBoldFont', label: 'The Bold Font', category: 'display', recommended: false },
  
  // Serif options
  { value: 'DejaVuSerif-Bold', label: 'DejaVu Serif Bold', category: 'serif', recommended: false },
  { value: 'LibreBaskerville-Bold', label: 'Libre Baskerville Bold', category: 'serif', recommended: false },
  { value: 'EBGaramond12-Regular', label: 'EB Garamond', category: 'serif', recommended: false },
  
  // System fallbacks
  { value: 'times', label: 'Times', category: 'serif', recommended: false },
  { value: 'georgia', label: 'Georgia', category: 'serif', recommended: false }
] as const;

// Image-to-Video effect types
export const IMAGE_EFFECT_TYPES = [
  { value: 'none', label: 'No Effect', description: 'Static image with no motion', icon: '📷' },
  { value: 'zoom', label: 'Zoom In', description: 'Smooth zoom-in effect', icon: '🔍' },
  { value: 'zoom_out', label: 'Zoom Out', description: 'Smooth zoom-out (reveal) effect', icon: '🔎' },
  { value: 'pan', label: 'Pan Effect', description: 'Horizontal or vertical panning', icon: '↔️' },
  { value: 'ken_burns', label: 'Ken Burns Effect', description: 'Professional documentary-style movement', icon: '🎬' }
] as const;

// Pan directions for pan effect
export const PAN_DIRECTIONS = [
  { value: 'left_to_right', label: 'Left to Right', icon: '→' },
  { value: 'right_to_left', label: 'Right to Left', icon: '←' },
  { value: 'top_to_bottom', label: 'Top to Bottom', icon: '↓' },
  { value: 'bottom_to_top', label: 'Bottom to Top', icon: '↑' },
  { value: 'diagonal_top_left', label: 'Diagonal (Top-Left)', icon: '↖️' },
  { value: 'diagonal_top_right', label: 'Diagonal (Top-Right)', icon: '↗️' },
  { value: 'diagonal_bottom_left', label: 'Diagonal (Bottom-Left)', icon: '↙️' },
  { value: 'diagonal_bottom_right', label: 'Diagonal (Bottom-Right)', icon: '↘️' }
] as const;

// Zoom speed presets
export const ZOOM_SPEED_PRESETS = [
  { value: 5, label: 'Very Slow', description: 'Subtle, barely noticeable zoom' },
  { value: 10, label: 'Slow', description: 'Gentle zoom effect (recommended)' },
  { value: 20, label: 'Medium', description: 'Moderate zoom effect' },
  { value: 35, label: 'Fast', description: 'Quick, dynamic zoom' },
  { value: 50, label: 'Very Fast', description: 'Rapid zoom effect' }
] as const;