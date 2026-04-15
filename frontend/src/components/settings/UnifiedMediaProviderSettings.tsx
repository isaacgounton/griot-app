import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Slider,
  CircularProgress,
} from '@mui/material';

import {
  SEARCH_SAFETY_LEVELS,
  FOOTAGE_QUALITIES,
  AI_VIDEO_PROVIDERS
} from '../../types/contentCreation';
import { pollinationsApi, directApi } from '../../utils/api';

const MEDIA_TYPES = [
  { value: 'video', label: 'Videos' },
  { value: 'image', label: 'Images' },
] as const;

const STOCK_PROVIDERS = [
  { value: 'pexels', label: 'Pexels' },
  { value: 'pixabay', label: 'Pixabay' },
];

const AI_IMAGE_PROVIDERS = [
  { value: 'together', label: 'Together.ai' },
  { value: 'modal_image', label: 'Modal Image Dev' },
  { value: 'pollinations', label: 'Pollinations AI' },
] as const;

interface UnifiedMediaProviderSettingsProps {
  mediaType: 'video' | 'image';
  provider: 'pexels' | 'pixabay' | 'ai_generated';
  aiVideoProvider?: string;
  aiImageProvider?: string;
  aiVideoModel?: string;
  aiImageModel?: string;
  searchSafety: string;
  quality?: string;
  searchTermsPerScene?: number;
  guidanceScale?: number;
  inferenceSteps?: number;
  showAdvancedSettings?: boolean;
  onMediaTypeChange: (type: 'video' | 'image') => void;
  onProviderChange: (provider: 'pexels' | 'pixabay' | 'ai_generated') => void;
  onAiVideoProviderChange?: (provider: string) => void;
  onAiImageProviderChange?: (provider: string) => void;
  onAiVideoModelChange?: (model: string) => void;
  onAiImageModelChange?: (model: string) => void;
  onSearchSafetyChange: (safety: string) => void;
  onQualityChange?: (quality: string) => void;
  onSearchTermsPerSceneChange?: (terms: number) => void;
  onGuidanceScaleChange?: (value: number) => void;
  onInferenceStepsChange?: (value: number) => void;
}

const UnifiedMediaProviderSettings: React.FC<UnifiedMediaProviderSettingsProps> = ({
  mediaType,
  provider,
  aiVideoProvider,
  aiImageProvider,
  aiVideoModel,
  aiImageModel,
  searchSafety,
  quality,
  searchTermsPerScene,
  guidanceScale = 3.5,
  inferenceSteps = 4,
  showAdvancedSettings = true,
  onMediaTypeChange,
  onProviderChange,
  onAiVideoProviderChange,
  onAiImageProviderChange,
  onAiVideoModelChange,
  onAiImageModelChange,
  onSearchSafetyChange,
  onQualityChange,
  onSearchTermsPerSceneChange,
  onGuidanceScaleChange,
  onInferenceStepsChange,
}) => {
  const isAiGenerated = provider === 'ai_generated';
  const isAiImage = mediaType === 'image' && isAiGenerated;
  const currentAiImageProvider = aiImageProvider || 'together';

  const [videoModels, setVideoModels] = useState<string[]>([]);
  const [imageModels, setImageModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  const parseModels = useCallback((raw: unknown): string[] => {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((m: unknown) => (typeof m === 'object' && m !== null && 'name' in m ? (m as { name: string }).name : String(m)))
      .filter((m: string) => m.length > 0)
      .map((m: string) => m.trim());
  }, []);

  // Fetch video models when AI video provider changes
  useEffect(() => {
    if (!isAiGenerated || mediaType !== 'video') { setVideoModels([]); return; }
    const load = async () => {
      setLoadingModels(true);
      try {
        const prov = aiVideoProvider || 'pollinations';
        if (prov === 'pollinations') {
          const r = await pollinationsApi.listVideoModels();
          setVideoModels(r?.success && r?.data?.models ? parseModels(r.data.models) : ['veo', 'seedance', 'seedance-pro', 'wan']);
        } else if (prov === 'wavespeed') {
          setVideoModels(['wan-2.2', 'minimax-video-02', 'minimax-video-01']);
        } else if (prov === 'modal_video') {
          setVideoModels(['ltx-video']);
        } else if (prov === 'comfyui') {
          setVideoModels(['default']);
        }
      } catch { setVideoModels(['veo', 'seedance', 'seedance-pro']); }
      finally { setLoadingModels(false); }
    };
    load();
  }, [isAiGenerated, mediaType, aiVideoProvider, parseModels]);

  // Fetch image models when AI image provider changes
  useEffect(() => {
    if (!isAiGenerated || mediaType !== 'image') { setImageModels([]); return; }
    const load = async () => {
      setLoadingModels(true);
      try {
        if (currentAiImageProvider === 'pollinations') {
          const r = await pollinationsApi.listImageModels();
          setImageModels(r?.success && r?.data?.models ? parseModels(r.data.models) : ['flux', 'turbo']);
        } else if (currentAiImageProvider === 'together') {
          const r = await directApi.listTogetherModels();
          setImageModels(r?.success && r?.data?.models ? parseModels(r.data.models) : ['black-forest-labs/FLUX.1-schnell']);
        } else if (currentAiImageProvider === 'modal_image') {
          const r = await directApi.listModalModels();
          setImageModels(r?.success && r?.data?.models ? parseModels(r.data.models) : ['modal-image']);
        }
      } catch { setImageModels(['flux']); }
      finally { setLoadingModels(false); }
    };
    load();
  }, [isAiGenerated, mediaType, currentAiImageProvider, parseModels]);

  const allProviders = [
    ...STOCK_PROVIDERS,
    { value: 'ai_generated', label: `AI Generated ${mediaType === 'video' ? 'Videos' : 'Images'}` }
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={4} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Media Type</InputLabel>
            <Select value={mediaType} onChange={(e) => onMediaTypeChange(e.target.value as 'video' | 'image')} label="Media Type">
              {MEDIA_TYPES.map((t) => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Provider</InputLabel>
            <Select value={provider} onChange={(e) => onProviderChange(e.target.value as 'pexels' | 'pixabay' | 'ai_generated')} label="Provider">
              {allProviders.map((p) => <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>

        {isAiGenerated && mediaType === 'video' && aiVideoProvider !== undefined && onAiVideoProviderChange && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>AI Provider</InputLabel>
              <Select value={aiVideoProvider || 'pollinations'} onChange={(e) => onAiVideoProviderChange(e.target.value)} label="AI Provider">
                {AI_VIDEO_PROVIDERS.map((p) => (
                  <MenuItem key={p} value={p}>
                    {p === 'pollinations' ? 'Pollinations AI' : p === 'modal_video' ? 'Modal Video' : p === 'wavespeed' ? 'WaveSpeed AI' : 'ComfyUI'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}

        {isAiGenerated && mediaType === 'video' && videoModels.length > 0 && onAiVideoModelChange && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Video Model</InputLabel>
              <Select
                value={aiVideoModel && videoModels.includes(aiVideoModel) ? aiVideoModel : videoModels[0] || ''}
                onChange={(e) => onAiVideoModelChange(e.target.value)}
                label="Video Model"
                endAdornment={loadingModels ? <CircularProgress size={16} sx={{ mr: 2 }} /> : undefined}
              >
                {videoModels.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        )}

        {isAiGenerated && mediaType === 'image' && onAiImageProviderChange && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>AI Provider</InputLabel>
              <Select value={currentAiImageProvider} onChange={(e) => onAiImageProviderChange(e.target.value)} label="AI Provider">
                {AI_IMAGE_PROVIDERS.map((p) => <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        )}

        {isAiGenerated && mediaType === 'image' && imageModels.length > 0 && onAiImageModelChange && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Image Model</InputLabel>
              <Select
                value={aiImageModel && imageModels.includes(aiImageModel) ? aiImageModel : imageModels[0] || ''}
                onChange={(e) => onAiImageModelChange(e.target.value)}
                label="Image Model"
                endAdornment={loadingModels ? <CircularProgress size={16} sx={{ mr: 2 }} /> : undefined}
              >
                {imageModels.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        )}

        <Grid item xs={6} sm={4} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Safety</InputLabel>
            <Select value={searchSafety} onChange={(e) => onSearchSafetyChange(e.target.value)} label="Safety">
              {SEARCH_SAFETY_LEVELS.map((l) => (
                <MenuItem key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {quality !== undefined && onQualityChange && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Quality</InputLabel>
              <Select value={quality || 'high'} onChange={(e) => onQualityChange(e.target.value)} label="Quality">
                {FOOTAGE_QUALITIES.map((q) => (
                  <MenuItem key={q} value={q}>{q.charAt(0).toUpperCase() + q.slice(1)}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}

        {searchTermsPerScene !== undefined && onSearchTermsPerSceneChange && !isAiGenerated && (
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Terms/Scene</InputLabel>
              <Select value={searchTermsPerScene || 3} onChange={(e) => onSearchTermsPerSceneChange(Number(e.target.value))} label="Terms/Scene">
                {[1, 2, 3, 4, 5].map((n) => <MenuItem key={n} value={n}>{n}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        )}

        {/* AI Advanced Settings */}
        {isAiImage && showAdvancedSettings && (
          <>
            {currentAiImageProvider === 'modal_image' && guidanceScale !== undefined && onGuidanceScaleChange && (
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" gutterBottom>Guidance Scale: {guidanceScale}</Typography>
                <Slider
                  value={guidanceScale} onChange={(_, v) => onGuidanceScaleChange(Array.isArray(v) ? v[0] : v)}
                  min={1.0} max={20.0} step={0.1} size="small"
                  marks={[{ value: 1, label: '1' }, { value: 7, label: '7' }, { value: 15, label: '15' }]}
                />
              </Grid>
            )}
            {inferenceSteps !== undefined && onInferenceStepsChange && (
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" gutterBottom>Inference Steps: {inferenceSteps}</Typography>
                <Slider
                  value={inferenceSteps} onChange={(_, v) => onInferenceStepsChange(Array.isArray(v) ? v[0] : v)}
                  min={1} max={currentAiImageProvider === 'together' ? 12 : 50} step={1} size="small"
                  marks={[{ value: 1, label: '1' }, { value: 4, label: '4' }, { value: 8, label: '8' }]}
                />
              </Grid>
            )}
          </>
        )}
      </Grid>
    </Box>
  );
};

export default UnifiedMediaProviderSettings;