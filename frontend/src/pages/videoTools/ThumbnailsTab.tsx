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
import { PhotoLibrary as ThumbnailsIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const ThumbnailsTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    timestamps: [] as number[],
    count: 5,
    format: 'jpg',
    quality: 85
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim()) {
      setErrors(prev => ({ ...prev, thumbnails: 'Video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, thumbnails: true }));
    setErrors(prev => ({ ...prev, thumbnails: null }));
    setResults(prev => ({ ...prev, thumbnails: null }));

    try {
      const response = await directApi.post('/videos/thumbnails', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'thumbnails');
      } else {
        setErrors(prev => ({ ...prev, thumbnails: 'Failed to create thumbnails job' }));
        setLoading(prev => ({ ...prev, thumbnails: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, thumbnails: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, thumbnails: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <ThumbnailsIcon color="primary" />
              Generate Video Thumbnails
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField fullWidth label="Video URL" placeholder="https://example.com/video.mp4" value={form.video_url} onChange={(e) => setForm({ ...form, video_url: e.target.value })} helperText="URL of the video to generate thumbnails from" />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Number of Thumbnails: {form.count}</Typography>
                <Slider value={form.count} onChange={(_e, value) => setForm({ ...form, count: Array.isArray(value) ? value[0] : value })} min={1} max={20} step={1} marks={[{ value: 1, label: '1' }, { value: 5, label: '5' }, { value: 10, label: '10' }, { value: 20, label: '20' }]} />
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
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.thumbnails ? <CircularProgress size={20} /> : <ThumbnailsIcon />}
              onClick={handleSubmit}
              disabled={loading.thumbnails || !form.video_url.trim()}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' }, maxWidth: { xs: '100%', sm: '300px' } }}
            >
              {loading.thumbnails ? 'Generating...' : 'Generate Thumbnails'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Thumbnail Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Generate 1-20 thumbnails" variant="outlined" size="small" />
              <Chip label="High quality for previews" variant="outlined" size="small" />
              <Chip label="JPG for web, PNG for quality" variant="outlined" size="small" />
              <Chip label="Evenly spaced across video" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('thumbnails', results.thumbnails, <ThumbnailsIcon />)}
      </Grid>
    </Grid>
  );
};

export default ThumbnailsTab;
