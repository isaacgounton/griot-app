import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Slider,
  Typography,
} from '@mui/material';

interface ImageProviderSettingsProps {
  imageProvider: string;
  searchSafety?: string;
  imageQuality?: string;
  guidanceScale?: number;
  inferenceSteps?: number;
  showAdvancedSettings?: boolean;
  showOnlyAiProviders?: boolean;
  onImageProviderChange: (provider: string) => void; // eslint-disable-line
  onSearchSafetyChange?: (safety: string) => void; // eslint-disable-line
  onImageQualityChange?: (quality: string) => void; // eslint-disable-line
  onGuidanceScaleChange?: (value: number) => void; // eslint-disable-line
  onInferenceStepsChange?: (value: number) => void; // eslint-disable-line
}

const imageProviders = [
  { value: 'pexels', label: '📹 Pexels', category: 'stock' },
  { value: 'pixabay', label: '🎨 Pixabay', category: 'stock' },
  { value: 'together', label: '🤖 Together.ai', category: 'ai' },
  { value: 'modal_image', label: '⚡ Modal Image', category: 'ai' },
  { value: 'pollinations', label: '🌸 Pollinations AI', category: 'ai' },
];

const safetyLevels = [
  { value: 'strict', label: '🔒 Strict' },
  { value: 'moderate', label: '⚖️ Moderate' },
  { value: 'off', label: '🔓 Off' },
];

const qualityLevels = [
  { value: 'standard', label: '📺 Standard' },
  { value: 'high', label: '🎥 High' },
  { value: 'ultra', label: '💎 Ultra' },
];

const ImageProviderSettings: React.FC<ImageProviderSettingsProps> = ({
  imageProvider,
  searchSafety = 'moderate',
  imageQuality,
  guidanceScale = 3.5,
  inferenceSteps = 4,
  showAdvancedSettings = true,
  showOnlyAiProviders = false,
  onImageProviderChange,
  onSearchSafetyChange,
  onImageQualityChange,
  onGuidanceScaleChange,
  onInferenceStepsChange,
}) => {
  const filteredProviders = showOnlyAiProviders 
    ? imageProviders.filter(p => p.category === 'ai')
    : imageProviders;

  const selectedProvider = filteredProviders.find(p => p.value === imageProvider);
  const isAiProvider = selectedProvider?.category === 'ai';
  const showQuality = imageQuality !== undefined && onImageQualityChange;
  const showGuidance = isAiProvider && showAdvancedSettings && imageProvider === 'modal_image' && onGuidanceScaleChange;
  const showSteps = isAiProvider && showAdvancedSettings && onInferenceStepsChange;

  return (
    <Box>
      <Grid container spacing={2}>
        {/* Image Provider */}
        <Grid item xs={12} sm={onSearchSafetyChange || showQuality ? 6 : 12}>
          <FormControl fullWidth size="small">
            <InputLabel>Image Provider</InputLabel>
            <Select
              value={imageProvider}
              onChange={(e) => onImageProviderChange(e.target.value)}
              label="Image Provider"
            >
              {filteredProviders.map((provider) => (
                <MenuItem key={provider.value} value={provider.value}>
                  {provider.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Content Safety */}
        {onSearchSafetyChange && (
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Content Safety</InputLabel>
              <Select
                value={searchSafety}
                onChange={(e) => onSearchSafetyChange(e.target.value)}
                label="Content Safety"
              >
                {safetyLevels.map((level) => (
                  <MenuItem key={level.value} value={level.value}>
                    {level.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}

        {/* Image Quality */}
        {showQuality && (
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Quality</InputLabel>
              <Select
                value={imageQuality}
                onChange={(e) => onImageQualityChange(e.target.value)}
                label="Quality"
              >
                {qualityLevels.map((quality) => (
                  <MenuItem key={quality.value} value={quality.value}>
                    {quality.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}

        {/* Guidance Scale (Flux only) */}
        {showGuidance && (
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Guidance: {guidanceScale}
            </Typography>
            <Slider
              value={guidanceScale}
              onChange={(_, value) => onGuidanceScaleChange(Array.isArray(value) ? value[0] : value)}
              min={1.0}
              max={20.0}
              step={0.5}
              size="small"
              marks={[
                { value: 1, label: '1' },
                { value: 7, label: '7' },
                { value: 15, label: '15' },
              ]}
            />
          </Grid>
        )}

        {/* Inference Steps */}
        {showSteps && (
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Steps: {inferenceSteps}
            </Typography>
            <Slider
              value={inferenceSteps}
              onChange={(_, value) => onInferenceStepsChange(Array.isArray(value) ? value[0] : value)}
              min={1}
              max={imageProvider === 'together' ? 12 : 50}
              step={1}
              size="small"
              marks={
                imageProvider === 'together' 
                  ? [{ value: 1, label: '1' }, { value: 4, label: '4' }, { value: 12, label: '12' }]
                  : [{ value: 1, label: '1' }, { value: 20, label: '20' }, { value: 50, label: '50' }]
              }
            />
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ImageProviderSettings;