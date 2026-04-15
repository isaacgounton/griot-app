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
import {
  Movie as VideoIcon,
  ZoomIn as ZoomIcon,
  PanTool as PanIcon,
  Videocam as KenBurnsIcon,
} from '@mui/icons-material';

import { 
  IMAGE_EFFECT_TYPES, 
  PAN_DIRECTIONS, 
  ZOOM_SPEED_PRESETS 
} from '../../constants/videoSettings';

interface ImageToVideoSettingsProps {
  effectType: string;
  zoomSpeed: number;
  panDirection?: string;
  onEffectTypeChange: (type: string) => void; // eslint-disable-line
  onZoomSpeedChange: (speed: number) => void; // eslint-disable-line
  onPanDirectionChange?: (direction: string) => void; // eslint-disable-line
}

const ImageToVideoSettings: React.FC<ImageToVideoSettingsProps> = ({
  effectType,
  zoomSpeed,
  panDirection,
  onEffectTypeChange,
  onZoomSpeedChange,
  onPanDirectionChange,
}) => {
  const isZoomEffect = effectType === 'zoom' || effectType === 'zoom_out';
  const isPanEffect = effectType === 'pan';
  const isKenBurnsEffect = effectType === 'ken_burns';
  const showSpeedSlider = isZoomEffect || isKenBurnsEffect;

  const getEffectIcon = (type: string) => {
    switch (type) {
      case 'zoom': return <ZoomIcon fontSize="small" />;
      case 'pan': return <PanIcon fontSize="small" />;
      case 'ken_burns': return <KenBurnsIcon fontSize="small" />;
      default: return <VideoIcon fontSize="small" />;
    }
  };

  return (
    <Box>
      <Grid container spacing={2}>
        {/* Effect Type */}
        <Grid item xs={12} sm={showSpeedSlider || isPanEffect ? 6 : 12}>
          <FormControl fullWidth size="small">
            <InputLabel>Motion Effect</InputLabel>
            <Select
              value={effectType}
              onChange={(e) => onEffectTypeChange(e.target.value)}
              label="Motion Effect"
            >
              {IMAGE_EFFECT_TYPES.map((effect) => (
                <MenuItem key={effect.value} value={effect.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getEffectIcon(effect.value)}
                    {effect.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Zoom Speed */}
        {showSpeedSlider && (
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Speed: {zoomSpeed}
            </Typography>
            <Slider
              value={zoomSpeed}
              onChange={(_, value) => onZoomSpeedChange(Array.isArray(value) ? value[0] : value)}
              min={0}
              max={100}
              step={5}
              marks={ZOOM_SPEED_PRESETS.map(p => ({ value: p.value, label: p.label }))}
              size="small"
            />
          </Grid>
        )}

        {/* Pan Direction */}
        {isPanEffect && onPanDirectionChange && (
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Pan Direction</InputLabel>
              <Select
                value={panDirection || 'left_to_right'}
                onChange={(e) => onPanDirectionChange(e.target.value)}
                label="Pan Direction"
              >
                {PAN_DIRECTIONS.map((dir) => (
                  <MenuItem key={dir.value} value={dir.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{dir.icon}</span>
                      {dir.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ImageToVideoSettings;