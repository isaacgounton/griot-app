import React from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Slider,
  TextField,
} from '@mui/material';

import { MUSIC_OPTIONS } from '../../constants/videoSettings';

interface BackgroundMusicSettingsProps {
  backgroundMusic: string;
  backgroundMusicVolume: number;
  musicDuration?: number;
  onBackgroundMusicChange: (music: string) => void;
  onBackgroundMusicVolumeChange: (volume: number) => void;
  onMusicDurationChange?: (duration: number) => void;
}

const BackgroundMusicSettings: React.FC<BackgroundMusicSettingsProps> = ({
  backgroundMusic,
  backgroundMusicVolume,
  musicDuration,
  onBackgroundMusicChange,
  onBackgroundMusicVolumeChange,
  onMusicDurationChange,
}) => {
  const isNoMusic = backgroundMusic === 'none';
  const isAiMusic = backgroundMusic === 'ai_generate';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <FormControl fullWidth size="small">
            <InputLabel>Music Style</InputLabel>
            <Select value={backgroundMusic} onChange={(e) => onBackgroundMusicChange(e.target.value)} label="Music Style">
              {MUSIC_OPTIONS.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {!isNoMusic && (
          <Grid item xs={12}>
            <Typography variant="body2" gutterBottom>Volume: {Math.round(backgroundMusicVolume * 100)}%</Typography>
            <Slider
              value={backgroundMusicVolume}
              onChange={(_, v) => onBackgroundMusicVolumeChange(Array.isArray(v) ? v[0] : v)}
              min={0} max={1} step={0.05}
              marks={[{ value: 0.1, label: '10%' }, { value: 0.3, label: '30%' }, { value: 0.5, label: '50%' }]}
              size="small"
            />
          </Grid>
        )}

        {isAiMusic && musicDuration !== undefined && onMusicDurationChange && (
          <Grid item xs={12}>
            <TextField
              fullWidth size="small"
              type="number"
              label="Duration (seconds)"
              value={musicDuration || 60}
              onChange={(e) => onMusicDurationChange(parseInt(e.target.value))}
              inputProps={{ min: 10, max: 300 }}
            />
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default BackgroundMusicSettings;