import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Slider
} from '@mui/material';
import { ViewModule as FramesIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const ExtractFramesTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    interval: 1.0,
    format: 'jpg',
    quality: 85,
    max_frames: 100
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim()) {
      setErrors(prev => ({ ...prev, frames: 'Video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, frames: true }));
    setErrors(prev => ({ ...prev, frames: null }));
    setResults(prev => ({ ...prev, frames: null }));

    try {
      const response = await directApi.post('/videos/frames', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'frames');
      } else {
        setErrors(prev => ({ ...prev, frames: 'Failed to create frames job' }));
        setLoading(prev => ({ ...prev, frames: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, frames: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, frames: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <FramesIcon color="primary" />
              Extract Video Frames
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField fullWidth label="Video URL" placeholder="https://example.com/video.mp4" value={form.video_url} onChange={(e) => setForm({ ...form, video_url: e.target.value })} helperText="URL of the video to extract frames from" />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Interval: {form.interval}s</Typography>
                <Slider value={form.interval} onChange={(_e, value) => setForm({ ...form, interval: Array.isArray(value) ? value[0] : value })} min={0.1} max={10.0} step={0.1} marks={[{ value: 0.1, label: '0.1s' }, { value: 1.0, label: '1s' }, { value: 5.0, label: '5s' }, { value: 10.0, label: '10s' }]} />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Format</InputLabel>
                  <Select value={form.format} label="Format" onChange={(e) => setForm({ ...form, format: e.target.value })}>
                    <MenuItem value="jpg">JPG</MenuItem>
                    <MenuItem value="png">PNG</MenuItem>
                    <MenuItem value="webp">WebP</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Quality: {form.quality}%</Typography>
                <Slider value={form.quality} onChange={(_e, value) => setForm({ ...form, quality: Array.isArray(value) ? value[0] : value })} min={10} max={100} step={5} />
              </Grid>

              <Grid item xs={12}>
                <Typography gutterBottom>Max Frames: {form.max_frames || 'Unlimited'}</Typography>
                <Slider value={form.max_frames} onChange={(_e, value) => setForm({ ...form, max_frames: Array.isArray(value) ? value[0] : value })} min={10} max={1000} step={10} marks={[{ value: 10, label: '10' }, { value: 100, label: '100' }, { value: 500, label: '500' }, { value: 1000, label: '1000' }]} />
              </Grid>
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.frames ? <CircularProgress size={20} /> : <FramesIcon />}
              onClick={handleSubmit}
              disabled={loading.frames || !form.video_url.trim()}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' }, maxWidth: { xs: '100%', sm: '300px' } }}
            >
              {loading.frames ? 'Extracting...' : 'Extract Frames'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Frame Extraction Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Extract frames at intervals" variant="outlined" size="small" />
              <Chip label="0.1s for smooth animation" variant="outlined" size="small" />
              <Chip label="1-5s for key moments" variant="outlined" size="small" />
              <Chip label="High quality for editing" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('frames', results.frames, <FramesIcon />)}
      </Grid>
    </Grid>
  );
};

export default ExtractFramesTab;
