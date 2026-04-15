import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  FormControlLabel,
  Switch,
  Slider,
} from '@mui/material';
import { AxiosError } from 'axios';

import { CAPTION_COLORS, CAPTION_FONT_FAMILIES } from '../../constants/videoSettings';
import { CAPTION_POSITIONS } from '../../types/contentCreation';
import { useAuth } from '../../contexts/AuthContext';
import { directApi } from '../../utils/api';

interface CaptionSettingsProps {
  enableCaptions: boolean;
  captionStyle: string;
  captionColor?: string;
  highlightColor?: string;
  captionPosition?: string;
  fontSize?: number;
  fontFamily?: string;
  wordsPerLine?: number;
  marginV?: number;
  outlineWidth?: number;
  allCaps?: boolean;
  onEnableCaptionsChange: (enabled: boolean) => void; // eslint-disable-line
  onCaptionStyleChange: (style: string) => void; // eslint-disable-line
  onCaptionColorChange?: (color: string) => void; // eslint-disable-line
  onHighlightColorChange?: (color: string) => void; // eslint-disable-line
  onCaptionPositionChange?: (position: string) => void; // eslint-disable-line
  onFontSizeChange?: (size: number) => void; // eslint-disable-line
  onFontFamilyChange?: (family: string) => void; // eslint-disable-line
  onWordsPerLineChange?: (words: number) => void; // eslint-disable-line
  onMarginVChange?: (margin: number) => void; // eslint-disable-line
  onOutlineWidthChange?: (width: number) => void; // eslint-disable-line
  onAllCapsChange?: (caps: boolean) => void; // eslint-disable-line
}

// Default presets for caption styles (fallback when API is unavailable)
// Keys must match the style names returned by the API
const STYLE_PRESETS: Record<string, {
  captionColor: string;
  highlightColor: string;
  fontSize: number;
  fontFamily: string;
  wordsPerLine: number;
  position: string;
  margin_v: number;
  outline_width: number;
  all_caps: boolean;
}> = {
  'viral_bounce': { captionColor: '#FFFFFF', highlightColor: '#FFFF00', fontSize: 56, fontFamily: 'Arial-Bold', wordsPerLine: 3, position: 'bottom_center', margin_v: 100, outline_width: 6, all_caps: true },
  'tiktok_viral': { captionColor: '#FFFFFF', highlightColor: '#FFFF00', fontSize: 56, fontFamily: 'Arial-Bold', wordsPerLine: 3, position: 'bottom_center', margin_v: 100, outline_width: 6, all_caps: true },
  'youtube_standard': { captionColor: '#FFFFFF', highlightColor: '#FFFF00', fontSize: 44, fontFamily: 'Arial-Bold', wordsPerLine: 10, position: 'bottom_center', margin_v: 80, outline_width: 3, all_caps: false },
  'instagram_reels': { captionColor: '#FFFFFF', highlightColor: '#FF69B4', fontSize: 52, fontFamily: 'Arial-Bold', wordsPerLine: 3, position: 'bottom_center', margin_v: 95, outline_width: 4, all_caps: true },
  'educational': { captionColor: '#FFFFFF', highlightColor: '#00FFFF', fontSize: 40, fontFamily: 'Arial-Bold', wordsPerLine: 8, position: 'bottom_center', margin_v: 85, outline_width: 3, all_caps: false },
  'accessibility': { captionColor: '#FFFF00', highlightColor: '#FFFFFF', fontSize: 48, fontFamily: 'Arial-Bold', wordsPerLine: 8, position: 'bottom_center', margin_v: 100, outline_width: 5, all_caps: false },
  'corporate': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 36, fontFamily: 'Arial-Bold', wordsPerLine: 12, position: 'bottom_center', margin_v: 70, outline_width: 2, all_caps: false },
  'dramatic': { captionColor: '#FFFFFF', highlightColor: '#FF0000', fontSize: 72, fontFamily: 'Arial-Bold', wordsPerLine: 1, position: 'middle_center', margin_v: 40, outline_width: 8, all_caps: true },
  'minimal': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 36, fontFamily: 'Helvetica-Bold', wordsPerLine: 10, position: 'bottom_center', margin_v: 70, outline_width: 1, all_caps: false },
  'classic': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 44, fontFamily: 'Arial-Bold', wordsPerLine: 8, position: 'bottom_center', margin_v: 80, outline_width: 3, all_caps: false },
  'karaoke': { captionColor: '#FFFFFF', highlightColor: '#FFFF00', fontSize: 52, fontFamily: 'Arial-Bold', wordsPerLine: 5, position: 'bottom_center', margin_v: 85, outline_width: 4, all_caps: false },
  'highlight': { captionColor: '#FFFFFF', highlightColor: '#FFFF00', fontSize: 44, fontFamily: 'Arial-Bold', wordsPerLine: 8, position: 'bottom_center', margin_v: 80, outline_width: 3, all_caps: false },
  'underline': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 42, fontFamily: 'Arial-Bold', wordsPerLine: 10, position: 'bottom_center', margin_v: 75, outline_width: 2, all_caps: false },
  'word_by_word': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 60, fontFamily: 'Arial-Bold', wordsPerLine: 2, position: 'middle_center', margin_v: 50, outline_width: 6, all_caps: true },
  'modern_neon': { captionColor: '#00FFFF', highlightColor: '#FFFFFF', fontSize: 58, fontFamily: 'Arial-Bold', wordsPerLine: 3, position: 'bottom_center', margin_v: 95, outline_width: 8, all_caps: true },
  'cinematic_glow': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 52, fontFamily: 'DejaVuSerif-Bold', wordsPerLine: 6, position: 'bottom_center', margin_v: 85, outline_width: 5, all_caps: false },
  'social_pop': { captionColor: '#FFFFFF', highlightColor: '#FF1493', fontSize: 54, fontFamily: 'Arial-Bold', wordsPerLine: 4, position: 'bottom_center', margin_v: 90, outline_width: 5, all_caps: true },
  'bounce': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 48, fontFamily: 'Arial-Bold', wordsPerLine: 6, position: 'bottom_center', margin_v: 90, outline_width: 4, all_caps: false },
  'typewriter': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 48, fontFamily: 'DejaVuSans-Bold', wordsPerLine: 8, position: 'bottom_center', margin_v: 80, outline_width: 3, all_caps: false },
  'fade_in': { captionColor: '#FFFFFF', highlightColor: '#FFFFFF', fontSize: 46, fontFamily: 'Arial-Bold', wordsPerLine: 7, position: 'bottom_center', margin_v: 85, outline_width: 3, all_caps: false },
};

const CaptionSettings: React.FC<CaptionSettingsProps> = ({
  enableCaptions,
  captionStyle,
  captionColor,
  highlightColor,
  captionPosition,
  fontSize,
  fontFamily,
  wordsPerLine,
  marginV,
  outlineWidth,
  allCaps,
  onEnableCaptionsChange,
  onCaptionStyleChange,
  onCaptionColorChange,
  onHighlightColorChange,
  onCaptionPositionChange,
  onFontSizeChange,
  onFontFamilyChange,
  onWordsPerLineChange,
  onMarginVChange,
  onOutlineWidthChange,
  onAllCapsChange,
}) => {
  const { apiKey } = useAuth();
  const [captionStyles, setCaptionStyles] = useState<Array<{ value: string; label: string }>>([]);
  const [captionPresets, setCaptionPresets] = useState<Record<string, Record<string, unknown>>>({});
  const [stylesFetched, setStylesFetched] = useState(false);

  // Fetch caption styles from API - only once on mount
  useEffect(() => {
    if (stylesFetched) return;
    
    const fetchCaptionStyles = async () => {
      try {
        const res = await directApi.getLongTimeout('/videos/caption-styles/presets', 60000);
        if (res.data?.available_styles) {
          const styles = res.data.available_styles.map((s: string) => ({
            value: s,
            label: s.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
          }));
          setCaptionStyles(styles);
          setCaptionPresets(res.data.presets || {});
          setStylesFetched(true);
        }
      } catch {
        // Fallback styles
        const fallback = Object.keys(STYLE_PRESETS).map(s => ({
          value: s, label: s.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
        }));
        setCaptionStyles(fallback);
        setStylesFetched(true);
      }
    };
    fetchCaptionStyles();
  }, [stylesFetched]);

  const handleStyleChange = async (newStyle: string) => {
    onCaptionStyleChange(newStyle);
    
    // Get preset values
    let preset = captionPresets[newStyle] || STYLE_PRESETS[newStyle];
    
    if (!preset && apiKey) {
      try {
        const res = await directApi.get(`/videos/caption-styles/presets/${newStyle}`);
        preset = res.data?.preset;
      } catch (e) {
        const err = e as AxiosError;
        console.warn(`Failed to fetch preset for ${newStyle}: ${err.response?.status}`);
      }
    }
    
    if (!preset) preset = STYLE_PRESETS[newStyle] || STYLE_PRESETS['viral_bounce'];
    
    // Apply preset
    const p = preset as Record<string, unknown>;
    if (onCaptionColorChange && p.caption_color) onCaptionColorChange(p.caption_color as string);
    if (onCaptionColorChange && p.captionColor) onCaptionColorChange(p.captionColor as string);
    if (onHighlightColorChange && p.highlight_color) onHighlightColorChange(p.highlight_color as string);
    if (onHighlightColorChange && p.highlightColor) onHighlightColorChange(p.highlightColor as string);
    if (onFontSizeChange && typeof p.font_size === 'number') onFontSizeChange(p.font_size);
    if (onFontSizeChange && typeof p.fontSize === 'number') onFontSizeChange(p.fontSize);
    if (onFontFamilyChange && p.font_family) onFontFamilyChange(p.font_family as string);
    if (onFontFamilyChange && p.fontFamily) onFontFamilyChange(p.fontFamily as string);
    if (onWordsPerLineChange && typeof p.words_per_line === 'number') onWordsPerLineChange(p.words_per_line);
    if (onWordsPerLineChange && typeof p.wordsPerLine === 'number') onWordsPerLineChange(p.wordsPerLine);
    if (onCaptionPositionChange && p.caption_position) onCaptionPositionChange(p.caption_position as string);
    if (onCaptionPositionChange && p.position) onCaptionPositionChange(p.position as string);
    if (onMarginVChange && typeof p.margin_v === 'number') onMarginVChange(p.margin_v);
    if (onMarginVChange && typeof p.marginV === 'number') onMarginVChange(p.marginV);
    if (onOutlineWidthChange && typeof p.outline_width === 'number') onOutlineWidthChange(p.outline_width);
    if (onOutlineWidthChange && typeof p.outlineWidth === 'number') onOutlineWidthChange(p.outlineWidth);
    if (onAllCapsChange && typeof p.all_caps === 'boolean') onAllCapsChange(p.all_caps);
    if (onAllCapsChange && typeof p.allCaps === 'boolean') onAllCapsChange(p.allCaps);
  };

  const ColorSwatch = ({ color }: { color: string }) => (
    <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: color, border: color === '#FFFFFF' ? '1px solid #ccc' : 'none', mr: 1 }} />
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={6} md={3}>
          <FormControlLabel
            control={<Switch checked={enableCaptions} onChange={(e) => onEnableCaptionsChange(e.target.checked)} />}
            label="Enable Captions"
          />
        </Grid>

        {enableCaptions && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Style</InputLabel>
                <Select value={captionStyles.length ? captionStyle : ''} onChange={(e) => handleStyleChange(e.target.value)} label="Style">
                  {captionStyles.map((s) => <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>

            {captionColor !== undefined && onCaptionColorChange && (
              <Grid item xs={6} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Color</InputLabel>
                  <Select value={captionColor} onChange={(e) => onCaptionColorChange(e.target.value)} label="Color">
                    {CAPTION_COLORS.map((c) => (
                      <MenuItem key={c.value} value={c.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}><ColorSwatch color={c.value} />{c.label}</Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {highlightColor !== undefined && onHighlightColorChange && (
              <Grid item xs={6} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Highlight</InputLabel>
                  <Select value={highlightColor} onChange={(e) => onHighlightColorChange(e.target.value)} label="Highlight">
                    {CAPTION_COLORS.map((c) => (
                      <MenuItem key={c.value} value={c.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}><ColorSwatch color={c.value} />{c.label}</Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {captionPosition !== undefined && onCaptionPositionChange && (
              <Grid item xs={6} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Position</InputLabel>
                  <Select value={captionPosition || 'bottom_center'} onChange={(e) => onCaptionPositionChange(e.target.value)} label="Position">
                    {CAPTION_POSITIONS.map((p) => (
                      <MenuItem key={p} value={p}>
                        {p.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {fontFamily !== undefined && onFontFamilyChange && (
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Font</InputLabel>
                  <Select value={fontFamily || 'Arial-Bold'} onChange={(e) => onFontFamilyChange(e.target.value)} label="Font">
                    {CAPTION_FONT_FAMILIES.map((f) => <MenuItem key={f.value} value={f.value}>{f.label}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {fontSize !== undefined && onFontSizeChange && (
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" gutterBottom>Font Size: {fontSize}px</Typography>
                <Slider
                  value={fontSize} onChange={(_, v) => onFontSizeChange(Array.isArray(v) ? v[0] : v)}
                  min={24} max={120} step={2} size="small"
                  marks={[{ value: 36, label: '36' }, { value: 56, label: '56' }, { value: 72, label: '72' }]}
                />
              </Grid>
            )}

            {wordsPerLine !== undefined && onWordsPerLineChange && (
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" gutterBottom>Words/Line: {wordsPerLine}</Typography>
                <Slider
                  value={wordsPerLine} onChange={(_, v) => onWordsPerLineChange(Array.isArray(v) ? v[0] : v)}
                  min={1} max={15} step={1} size="small"
                  marks={[{ value: 3, label: '3' }, { value: 6, label: '6' }, { value: 10, label: '10' }]}
                />
              </Grid>
            )}

            {marginV !== undefined && onMarginVChange && (
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" gutterBottom>Vertical Margin: {marginV}px</Typography>
                <Slider
                  value={marginV} onChange={(_, v) => onMarginVChange(Array.isArray(v) ? v[0] : v)}
                  min={0} max={200} step={5} size="small"
                  marks={[{ value: 50, label: '50' }, { value: 100, label: '100' }, { value: 150, label: '150' }]}
                />
              </Grid>
            )}

            {outlineWidth !== undefined && onOutlineWidthChange && (
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" gutterBottom>Outline Width: {outlineWidth}px</Typography>
                <Slider
                  value={outlineWidth} onChange={(_, v) => onOutlineWidthChange(Array.isArray(v) ? v[0] : v)}
                  min={0} max={10} step={1} size="small"
                  marks={[{ value: 2, label: '2' }, { value: 4, label: '4' }, { value: 6, label: '6' }]}
                />
              </Grid>
            )}

            {allCaps !== undefined && onAllCapsChange && (
              <Grid item xs={12} sm={6} md={3}>
                <FormControlLabel
                  control={<Switch checked={allCaps} onChange={(e) => onAllCapsChange(e.target.checked)} />}
                  label="All Caps"
                />
              </Grid>
            )}
          </>
        )}
      </Grid>
    </Box>
  );
};

export default CaptionSettings;