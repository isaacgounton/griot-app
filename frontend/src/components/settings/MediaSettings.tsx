import React from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  TextField,
  Slider,
} from '@mui/material';

import type { MediaSettings as MediaSettingsType } from '../../types/contentCreation';
import {
  IMAGE_PRESETS,
  ASPECT_RATIOS,
  FRAME_RATES,
  CROSSFADE_DURATIONS,
} from '../../types/contentCreation';

interface MediaSettingsProps {
  settings: MediaSettingsType;
  onChange: (settings: MediaSettingsType) => void;
}

const MediaSettings: React.FC<MediaSettingsProps> = ({
  settings,
  onChange,
}) => {
  const handleSettingChange = <K extends keyof MediaSettingsType>(
    field: K,
    value: MediaSettingsType[K]
  ) => {
    onChange({ ...settings, [field]: value });
  };

  const handlePresetChange = (presetName: string) => {
    const preset = IMAGE_PRESETS.find(p => p.name === presetName);
    if (preset) {
      onChange({
        ...settings,
        imageWidth: preset.width,
        imageHeight: preset.height,
        aspectRatio: preset.aspectRatio
      });
    }
  };

  const getCurrentPresetName = () => {
    const preset = IMAGE_PRESETS.find(p => 
      p.width === settings.imageWidth && 
      p.height === settings.imageHeight
    );
    return preset?.name || 'Custom';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={4} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Preset</InputLabel>
            <Select value={getCurrentPresetName()} onChange={(e) => handlePresetChange(e.target.value)} label="Preset">
              {IMAGE_PRESETS.map((preset) => (
                <MenuItem key={preset.name} value={preset.name}>
                  {preset.name} ({preset.width}×{preset.height})
                </MenuItem>
              ))}
              <MenuItem value="Custom">Custom</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Aspect Ratio</InputLabel>
            <Select value={settings.aspectRatio} onChange={(e) => handleSettingChange('aspectRatio', e.target.value)} label="Aspect Ratio">
              {ASPECT_RATIOS.map((ratio) => <MenuItem key={ratio} value={ratio}>{ratio}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <TextField
            label="Width"
            type="number"
            fullWidth
            size="small"
            value={settings.imageWidth}
            onChange={(e) => handleSettingChange('imageWidth', parseInt(e.target.value) || 1080)}
            inputProps={{ min: 240, max: 4096 }}
          />
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <TextField
            label="Height"
            type="number"
            fullWidth
            size="small"
            value={settings.imageHeight}
            onChange={(e) => handleSettingChange('imageHeight', parseInt(e.target.value) || 1920)}
            inputProps={{ min: 240, max: 4096 }}
          />
        </Grid>

        <Grid item xs={6} sm={4} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>FPS</InputLabel>
            <Select value={settings.frameRate || 30} onChange={(e) => handleSettingChange('frameRate', Number(e.target.value))} label="FPS">
              {FRAME_RATES.map((fps) => <MenuItem key={fps} value={fps}>{fps} FPS</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="body2" gutterBottom>Crossfade: {settings.crossfadeDuration || 0.3}s</Typography>
          <Slider
            value={settings.crossfadeDuration || 0.3}
            onChange={(_, v) => handleSettingChange('crossfadeDuration', Array.isArray(v) ? v[0] : v)}
            min={0} max={1.0} step={0.1} size="small"
            marks={CROSSFADE_DURATIONS.map(d => ({ value: d, label: `${d}s` }))}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default MediaSettings;