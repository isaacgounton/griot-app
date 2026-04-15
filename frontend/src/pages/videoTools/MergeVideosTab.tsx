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
import { CallMerge as MergeIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const MergeVideosTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_urls: ['', ''],
    background_audio_url: '',
    output_format: 'mp4',
    transition: 'fade',
    transition_duration: 1.5,
    max_segment_duration: 0,
    total_duration_limit: 0
  });

  const handleSubmit = async () => {
    const validUrls = form.video_urls.filter(url => url.trim());
    if (validUrls.length < 2) {
      setErrors(prev => ({ ...prev, merge: 'At least 2 video URLs are required' }));
      return;
    }

    setLoading(prev => ({ ...prev, merge: true }));
    setErrors(prev => ({ ...prev, merge: null }));
    setResults(prev => ({ ...prev, merge: null }));

    try {
      // Only send fields the backend VideoConcatenateRequest supports
      const payload: Record<string, unknown> = {
        video_urls: validUrls,
        output_format: form.output_format,
        transition: form.transition,
        transition_duration: form.transition_duration
      };
      if (form.max_segment_duration > 0) payload.max_segment_duration = form.max_segment_duration;
      if (form.total_duration_limit > 0) payload.total_duration_limit = form.total_duration_limit;

      const response = await directApi.post('/videos/merge', payload);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'merge');
      } else {
        setErrors(prev => ({ ...prev, merge: 'Failed to create merge job' }));
        setLoading(prev => ({ ...prev, merge: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, merge: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, merge: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <MergeIcon color="primary" />
              Merge Multiple Videos
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" sx={{ mb: 2 }}>Video URLs (in order)</Typography>
                {form.video_urls.map((url, index) => (
                  <Box key={index} sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <TextField
                      fullWidth
                      label={`Video ${index + 1} URL`}
                      placeholder="https://example.com/video.mp4"
                      value={url}
                      onChange={(e) => {
                        const newUrls = [...form.video_urls];
                        newUrls[index] = e.target.value;
                        setForm({ ...form, video_urls: newUrls });
                      }}
                    />
                    {form.video_urls.length > 2 && (
                      <Button
                        variant="outlined" color="error"
                        onClick={() => setForm({ ...form, video_urls: form.video_urls.filter((_, i) => i !== index) })}
                        sx={{ minWidth: 'auto', px: 2 }}
                      >
                        X
                      </Button>
                    )}
                  </Box>
                ))}
                <Button variant="outlined" onClick={() => setForm({ ...form, video_urls: [...form.video_urls, ''] })} sx={{ mt: 1 }}>
                  + Add Video URL
                </Button>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Background Audio URL (Optional)"
                  placeholder="https://example.com/music.mp3"
                  value={form.background_audio_url}
                  onChange={(e) => setForm({ ...form, background_audio_url: e.target.value })}
                  helperText="Optional background music for the merged video"
                />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Transition</InputLabel>
                  <Select value={form.transition} label="Transition" onChange={(e) => setForm({ ...form, transition: e.target.value })}>
                    <MenuItem value="none">None (Instant Cut)</MenuItem>
                    <MenuItem value="fade">Fade</MenuItem>
                    <MenuItem value="dissolve">Dissolve</MenuItem>
                    <MenuItem value="slide">Slide</MenuItem>
                    <MenuItem value="wipe">Wipe</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Transition Duration: {form.transition_duration}s</Typography>
                <Slider
                  value={form.transition_duration}
                  onChange={(_e, value) => setForm({ ...form, transition_duration: Array.isArray(value) ? value[0] : value })}
                  min={0.1} max={5.0} step={0.1}
                  disabled={form.transition === 'none'}
                />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Output Format</InputLabel>
                  <Select value={form.output_format} label="Output Format" onChange={(e) => setForm({ ...form, output_format: e.target.value })}>
                    <MenuItem value="mp4">MP4</MenuItem>
                    <MenuItem value="webm">WebM</MenuItem>
                    <MenuItem value="avi">AVI</MenuItem>
                    <MenuItem value="mov">MOV</MenuItem>
                    <MenuItem value="mkv">MKV</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.merge ? <CircularProgress size={20} /> : <MergeIcon />}
              onClick={handleSubmit}
              disabled={loading.merge || form.video_urls.filter(url => url.trim()).length < 2}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' }, maxWidth: { xs: '100%', sm: '300px' } }}
            >
              {loading.merge ? 'Merging Videos...' : 'Merge Videos'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Merge Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Add 2+ videos to merge" variant="outlined" size="small" />
              <Chip label="Videos merge in order listed" variant="outlined" size="small" />
              <Chip label="Choose smooth transitions" variant="outlined" size="small" />
              <Chip label="Add background music" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('merge', results.merge, <MergeIcon />)}
      </Grid>
    </Grid>
  );
};

export default MergeVideosTab;
