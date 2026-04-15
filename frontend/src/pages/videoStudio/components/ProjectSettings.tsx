import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Box,
  Select, MenuItem, FormControl, InputLabel, Slider,
  Typography, Stack, Divider, CircularProgress,
} from '@mui/material';
import type { ProjectSettings as ProjectSettingsType } from '../types';
import { useVoices } from '../../../hooks/useContentCreation';
import { MUSIC_OPTIONS } from '../../../constants/videoSettings';
import { directApi, pollinationsApi } from '../../../utils/api';
import CaptionSettings from '../../../components/settings/CaptionSettings';

interface ProjectSettingsDialogProps {
  open: boolean;
  onClose: () => void;
  settings: ProjectSettingsType;
  onSave: (settings: Record<string, unknown>) => void;
}


const RESOLUTIONS = [
  { label: '9:16 Portrait (1080x1920)', width: 1080, height: 1920 },
  { label: '16:9 Landscape (1920x1080)', width: 1920, height: 1080 },
  { label: '1:1 Square (1080x1080)', width: 1080, height: 1080 },
  { label: '4:5 Instagram (1080x1350)', width: 1080, height: 1350 },
];

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
  { code: 'pt', name: 'Português' },
  { code: 'ru', name: 'Русский' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
  { code: 'zh', name: '中文' },
  { code: 'ar', name: 'العربية' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'tr', name: 'Türkçe' },
  { code: 'nl', name: 'Nederlands' },
  { code: 'pl', name: 'Polski' },
];

export default function ProjectSettingsDialog({ open, onClose, settings, onSave }: ProjectSettingsDialogProps) {
  const [local, setLocal] = React.useState<Record<string, unknown>>({});
  const { voices, voiceProviders, loading: voicesLoading, fetchVoices } = useVoices();

  useEffect(() => {
    setLocal({});
  }, [open]);

  // Fetch voices when dialog opens
  useEffect(() => {
    if (open && voices.length === 0) fetchVoices();
  }, [open, voices.length, fetchVoices]);

  const get = <T,>(key: string, fallback: T): T => {
    if (key in local) return local[key] as T;
    return (settings as unknown as Record<string, unknown>)[key] as T ?? fallback;
  };

  const set = (key: string, value: unknown) => {
    setLocal(prev => ({ ...prev, [key]: value }));
  };

  // Helpers for nested caption_properties
  const getCaptionProp = <T,>(key: string, fallback: T): T => {
    const localCp = local.caption_properties as Record<string, unknown> | undefined;
    if (localCp && key in localCp) return localCp[key] as T;
    return (settings.caption_properties as Record<string, unknown>)?.[key] as T ?? fallback;
  };

  const setCaptionProp = (key: string, value: unknown) => {
    setLocal(prev => ({
      ...prev,
      caption_properties: {
        ...(settings.caption_properties || {}),
        ...(prev.caption_properties as Record<string, unknown> || {}),
        [key]: value,
      },
    }));
  };

  // ── Dynamic model fetching ─────────────────────────────────────
  const [videoModels, setVideoModels] = useState<string[]>([]);
  const [imageModels, setImageModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  const currentFootageProvider = get<string>('footage_provider', 'pexels');
  const currentMediaType = get<string>('media_type', 'video');
  const currentAiVideoProvider = get<string>('ai_video_provider', 'pollinations');
  const currentAiImageProvider = get<string>('ai_image_provider', 'pollinations');

  // Helper to normalize model arrays from API responses
  const parseModels = useCallback((rawModels: unknown[]): string[] => {
    const models = rawModels
      .map((m: unknown) => {
        if (typeof m === 'string') return m;
        if (m && typeof m === 'object' && 'name' in m) return String((m as { name: string }).name);
        return '';
      })
      .filter((m: string) => m.length > 0)
      .map((m: string) => m.toLowerCase().trim());
    return Array.from(new Set(models));
  }, []);

  // Fetch video models when AI video provider changes
  useEffect(() => {
    if (currentFootageProvider !== 'ai_generated' || currentMediaType !== 'video') {
      setVideoModels([]);
      return;
    }

    const loadVideoModels = async () => {
      setLoadingModels(true);
      try {
        if (currentAiVideoProvider === 'pollinations') {
          const response = await pollinationsApi.listVideoModels();
          if (response?.success && response?.data?.models) {
            setVideoModels(parseModels(response.data.models));
          } else {
            setVideoModels(['veo', 'seedance', 'seedance-pro', 'wan']);
          }
        } else if (currentAiVideoProvider === 'wavespeed') {
          // WaveSpeed has no model listing API — use known models from service
          setVideoModels(['wan-2.2', 'minimax-video-02', 'minimax-video-01']);
        } else if (currentAiVideoProvider === 'modal_video') {
          setVideoModels(['ltx-video']);
        } else if (currentAiVideoProvider === 'comfyui') {
          setVideoModels(['default']);
        }
      } catch (error) {
        console.error('Failed to load video models:', error);
        setVideoModels(['veo', 'seedance', 'seedance-pro']);
      } finally {
        setLoadingModels(false);
      }
    };
    loadVideoModels();
  }, [currentFootageProvider, currentMediaType, currentAiVideoProvider, parseModels]);

  // Fetch image models when AI image provider changes
  useEffect(() => {
    if (currentFootageProvider !== 'ai_generated' || currentMediaType !== 'image') {
      setImageModels([]);
      return;
    }

    const loadImageModels = async () => {
      setLoadingModels(true);
      try {
        if (currentAiImageProvider === 'pollinations') {
          const response = await pollinationsApi.listImageModels();
          if (response?.success && response?.data?.models) {
            setImageModels(parseModels(response.data.models));
          } else {
            setImageModels(['flux', 'turbo']);
          }
        } else if (currentAiImageProvider === 'together') {
          const response = await directApi.listTogetherModels();
          if (response?.success && response?.data?.models) {
            setImageModels(parseModels(response.data.models));
          } else {
            setImageModels(['black-forest-labs/FLUX.1-schnell']);
          }
        } else if (currentAiImageProvider === 'modal_image') {
          const response = await directApi.listModalModels();
          if (response?.success && response?.data?.models) {
            setImageModels(parseModels(response.data.models));
          } else {
            setImageModels(['modal-image']);
          }
        }
      } catch (error) {
        console.error('Failed to load image models:', error);
        setImageModels(['flux']);
      } finally {
        setLoadingModels(false);
      }
    };
    loadImageModels();
  }, [currentFootageProvider, currentMediaType, currentAiImageProvider, parseModels]);

  const handleSave = () => {
    onSave(local);
    onClose();
  };

  const currentRes = get<{ width: number; height: number }>('resolution', { width: 1080, height: 1920 });
  const resIndex = RESOLUTIONS.findIndex(r => r.width === currentRes.width && r.height === currentRes.height);
  const currentProvider = get('tts_provider', 'kokoro');
  const currentLanguage = get('language', 'en');

  const currentVoiceName = get('voice_name', '');

  // Filter voices by current provider and language
  const filteredVoices = useMemo(() => {
    const filtered = voices.filter(v => {
      const matchProvider = v.provider === currentProvider;
      const matchLang = !currentLanguage || v.language?.startsWith(currentLanguage);
      return matchProvider && matchLang;
    });
    // Always include the currently selected voice so the dropdown shows it
    if (currentVoiceName && !filtered.some(v => v.name === currentVoiceName)) {
      const selected = voices.find(v => v.name === currentVoiceName);
      if (selected) filtered.unshift(selected);
    }
    return filtered;
  }, [voices, currentProvider, currentLanguage, currentVoiceName]);

  // Available providers from fetched data
  const providerNames = voiceProviders.length > 0
    ? voiceProviders.map(p => p.name)
    : ['kokoro', 'edge', 'piper'];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Project Settings</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ mt: 1 }}>
          {/* ── Resolution ──────────────────────────────────────────── */}
          <FormControl size="small" fullWidth>
            <InputLabel>Resolution</InputLabel>
            <Select
              value={resIndex >= 0 ? resIndex : 0}
              label="Resolution"
              onChange={e => {
                const r = RESOLUTIONS[e.target.value as number];
                set('resolution', { width: r.width, height: r.height });
              }}
            >
              {RESOLUTIONS.map((r, i) => (
                <MenuItem key={i} value={i}>{r.label}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <Divider>Voice</Divider>

          {/* Voice Provider */}
          <FormControl size="small" fullWidth>
            <InputLabel>Voice Provider</InputLabel>
            <Select
              value={currentProvider}
              label="Voice Provider"
              onChange={e => {
                set('tts_provider', e.target.value);
                // Reset voice name when switching providers
                set('voice_name', '');
              }}
            >
              {providerNames.map(p => (
                <MenuItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Language */}
          <FormControl size="small" fullWidth>
            <InputLabel>Language</InputLabel>
            <Select
              value={currentLanguage}
              label="Language"
              onChange={e => set('language', e.target.value)}
            >
              {LANGUAGES.map(l => (
                <MenuItem key={l.code} value={l.code}>{l.name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Voice Name — Dropdown */}
          <FormControl size="small" fullWidth>
            <InputLabel>Voice</InputLabel>
            <Select
              value={currentVoiceName}
              label="Voice"
              onChange={e => set('voice_name', e.target.value)}
              disabled={voicesLoading}
              startAdornment={voicesLoading ? <CircularProgress size={16} sx={{ mr: 1 }} /> : undefined}
              renderValue={(val) => {
                if (!val) return '';
                const v = voices.find(voice => voice.name === val);
                return v ? v.name : String(val);
              }}
            >
              {filteredVoices.length > 0 ? (
                filteredVoices.map(v => (
                  <MenuItem key={v.name} value={v.name}>
                    {v.name}
                    {v.gender && <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>({v.gender})</Typography>}
                  </MenuItem>
                ))
              ) : (
                <MenuItem value="" disabled>
                  {voicesLoading ? 'Loading voices...' : 'No voices available for this provider/language'}
                </MenuItem>
              )}
            </Select>
          </FormControl>

          {/* Voice Speed */}
          <Box>
            <Typography variant="caption" color="text.secondary">
              Voice Speed: {get('voice_speed', 1.0)}x
            </Typography>
            <Slider
              value={get('voice_speed', 1.0)}
              onChange={(_, v) => set('voice_speed', v)}
              min={0.5}
              max={2.0}
              step={0.1}
              size="small"
            />
          </Box>

          <Divider>Captions</Divider>

          <CaptionSettings
            enableCaptions={getCaptionProp('enable_captions', true)}
            captionStyle={get('caption_style', 'viral_bounce')}
            captionColor={getCaptionProp('caption_color', '#FFFFFF')}
            highlightColor={getCaptionProp('highlight_color', '#FFFF00')}
            captionPosition={getCaptionProp('caption_position', 'bottom_center')}
            fontSize={getCaptionProp('font_size', 48)}
            fontFamily={getCaptionProp('font_family', 'Arial-Bold')}
            wordsPerLine={getCaptionProp('words_per_line', 6)}
            marginV={getCaptionProp('margin_v', 100)}
            outlineWidth={getCaptionProp('outline_width', 4)}
            allCaps={getCaptionProp('all_caps', false)}
            onEnableCaptionsChange={v => setCaptionProp('enable_captions', v)}
            onCaptionStyleChange={v => set('caption_style', v)}
            onCaptionColorChange={v => setCaptionProp('caption_color', v)}
            onHighlightColorChange={v => setCaptionProp('highlight_color', v)}
            onCaptionPositionChange={v => setCaptionProp('caption_position', v)}
            onFontSizeChange={v => setCaptionProp('font_size', v)}
            onFontFamilyChange={v => setCaptionProp('font_family', v)}
            onWordsPerLineChange={v => setCaptionProp('words_per_line', v)}
            onMarginVChange={v => setCaptionProp('margin_v', v)}
            onOutlineWidthChange={v => setCaptionProp('outline_width', v)}
            onAllCapsChange={v => setCaptionProp('all_caps', v)}
          />

          <Divider>Background Music</Divider>

          {/* Music Style */}
          <FormControl size="small" fullWidth>
            <InputLabel>Music Style</InputLabel>
            <Select
              value={get('background_music', 'none')}
              label="Music Style"
              onChange={e => set('background_music', e.target.value)}
            >
              {MUSIC_OPTIONS.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Music Volume */}
          {get('background_music', 'none') !== 'none' && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Music Volume: {Math.round(get('background_music_volume', 0.3) * 100)}%
              </Typography>
              <Slider
                value={get('background_music_volume', 0.3)}
                onChange={(_, v) => set('background_music_volume', v)}
                min={0.05}
                max={1.0}
                step={0.05}
                size="small"
              />
            </Box>
          )}

          <Divider>Media</Divider>

          {/* Media Type */}
          <FormControl size="small" fullWidth>
            <InputLabel>Default Media Type</InputLabel>
            <Select
              value={get('media_type', 'video')}
              label="Default Media Type"
              onChange={e => set('media_type', e.target.value)}
            >
              <MenuItem value="video">Video</MenuItem>
              <MenuItem value="image">Image</MenuItem>
            </Select>
          </FormControl>

          {/* Footage Provider */}
          <FormControl size="small" fullWidth>
            <InputLabel>Footage Source</InputLabel>
            <Select
              value={get('footage_provider', 'pexels')}
              label="Footage Source"
              onChange={e => set('footage_provider', e.target.value)}
            >
              <MenuItem value="pexels">Pexels (Stock)</MenuItem>
              <MenuItem value="pixabay">Pixabay (Stock)</MenuItem>
              <MenuItem value="ai_generated">AI Generated</MenuItem>
            </Select>
          </FormControl>

          {/* AI Video Provider + Model (when footage=AI & media=video) */}
          {currentFootageProvider === 'ai_generated' && currentMediaType === 'video' && (
            <>
              <FormControl size="small" fullWidth>
                <InputLabel>AI Video Provider</InputLabel>
                <Select
                  value={get('ai_video_provider', 'pollinations')}
                  label="AI Video Provider"
                  onChange={e => {
                    set('ai_video_provider', e.target.value);
                    set('ai_video_model', '');
                  }}
                >
                  <MenuItem value="pollinations">Pollinations AI</MenuItem>
                  <MenuItem value="wavespeed">WaveSpeed AI</MenuItem>
                  <MenuItem value="modal_video">Modal Video (LTX)</MenuItem>
                  <MenuItem value="comfyui">ComfyUI</MenuItem>
                </Select>
              </FormControl>

              {videoModels.length > 0 && (
                <FormControl size="small" fullWidth>
                  <InputLabel>Video Model</InputLabel>
                  <Select
                    value={get('ai_video_model', videoModels[0] || '')}
                    label="Video Model"
                    onChange={e => set('ai_video_model', e.target.value)}
                    disabled={loadingModels}
                    startAdornment={loadingModels ? <CircularProgress size={16} sx={{ mr: 1 }} /> : undefined}
                  >
                    {videoModels.map(m => (
                      <MenuItem key={m} value={m}>
                        {m.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              {loadingModels && videoModels.length === 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="caption" color="text.secondary">Loading models...</Typography>
                </Box>
              )}
            </>
          )}

          {/* AI Image Provider + Model (when footage=AI & media=image) */}
          {currentFootageProvider === 'ai_generated' && currentMediaType === 'image' && (
            <>
              <FormControl size="small" fullWidth>
                <InputLabel>AI Image Provider</InputLabel>
                <Select
                  value={get('ai_image_provider', 'pollinations')}
                  label="AI Image Provider"
                  onChange={e => {
                    set('ai_image_provider', e.target.value);
                    set('ai_image_model', '');
                  }}
                >
                  <MenuItem value="together">Together.ai</MenuItem>
                  <MenuItem value="modal_image">Modal Image</MenuItem>
                  <MenuItem value="pollinations">Pollinations AI</MenuItem>
                </Select>
              </FormControl>

              {imageModels.length > 0 && (
                <FormControl size="small" fullWidth>
                  <InputLabel>Image Model</InputLabel>
                  <Select
                    value={get('ai_image_model', imageModels[0] || '')}
                    label="Image Model"
                    onChange={e => set('ai_image_model', e.target.value)}
                    disabled={loadingModels}
                    startAdornment={loadingModels ? <CircularProgress size={16} sx={{ mr: 1 }} /> : undefined}
                  >
                    {imageModels.map(m => (
                      <MenuItem key={m} value={m}>
                        {m.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              {loadingModels && imageModels.length === 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="caption" color="text.secondary">Loading models...</Typography>
                </Box>
              )}
            </>
          )}

          <Divider>Effects &amp; Transitions</Divider>

          {/* Effect Type */}
          <FormControl size="small" fullWidth>
            <InputLabel>Scene Effect</InputLabel>
            <Select
              value={get('effect_type', 'none')}
              label="Scene Effect"
              onChange={e => set('effect_type', e.target.value)}
            >
              <MenuItem value="none">None</MenuItem>
              <MenuItem value="zoom">Zoom</MenuItem>
              <MenuItem value="pan">Pan</MenuItem>
              <MenuItem value="ken_burns">Ken Burns (Zoom + Pan)</MenuItem>
              <MenuItem value="fade">Fade</MenuItem>
            </Select>
          </FormControl>

          {/* Zoom Speed (shown for zoom or ken_burns) */}
          {(get<string>('effect_type', 'none') === 'zoom' || get<string>('effect_type', 'none') === 'ken_burns') && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Zoom Speed: {get('zoom_speed', 25)}%
              </Typography>
              <Slider
                value={get('zoom_speed', 25)}
                onChange={(_, v) => set('zoom_speed', v)}
                min={5}
                max={100}
                step={5}
                size="small"
              />
            </Box>
          )}

          {/* Pan Direction (shown for pan or ken_burns) */}
          {(get<string>('effect_type', 'none') === 'pan' || get<string>('effect_type', 'none') === 'ken_burns') && (
            <FormControl size="small" fullWidth>
              <InputLabel>Pan Direction</InputLabel>
              <Select
                value={get('pan_direction', 'left_to_right')}
                label="Pan Direction"
                onChange={e => set('pan_direction', e.target.value)}
              >
                <MenuItem value="left_to_right">Left to Right</MenuItem>
                <MenuItem value="right_to_left">Right to Left</MenuItem>
                <MenuItem value="top_to_bottom">Top to Bottom</MenuItem>
                <MenuItem value="bottom_to_top">Bottom to Top</MenuItem>
              </Select>
            </FormControl>
          )}

          {/* Crossfade Duration */}
          <Box>
            <Typography variant="caption" color="text.secondary">
              Crossfade Duration: {get('crossfade_duration', 0.3)}s
            </Typography>
            <Slider
              value={get('crossfade_duration', 0.3)}
              onChange={(_, v) => set('crossfade_duration', v)}
              min={0}
              max={2.0}
              step={0.1}
              size="small"
            />
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>Save</Button>
      </DialogActions>
    </Dialog>
  );
}
