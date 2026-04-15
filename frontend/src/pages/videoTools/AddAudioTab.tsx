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
import { AudioFile as AddAudioIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const AddAudioTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    audio_url: '',
    video_volume: 100,
    audio_volume: 80,
    sync_mode: 'overlay',
    match_length: 'video',
    fade_in_duration: 0,
    fade_out_duration: 0
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim() || !form.audio_url.trim()) {
      setErrors(prev => ({ ...prev, addaudio: 'Video URL and Audio URL are required' }));
      return;
    }

    setLoading(prev => ({ ...prev, addaudio: true }));
    setErrors(prev => ({ ...prev, addaudio: null }));
    setResults(prev => ({ ...prev, addaudio: null }));

    try {
      const response = await directApi.post('/videos/add-audio', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'addaudio');
      } else {
        setErrors(prev => ({ ...prev, addaudio: 'Failed to create add audio job' }));
        setLoading(prev => ({ ...prev, addaudio: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, addaudio: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, addaudio: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <AddAudioIcon color="primary" />
              Add Audio to Video
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField fullWidth label="Video URL" placeholder="https://example.com/video.mp4" value={form.video_url} onChange={(e) => setForm({ ...form, video_url: e.target.value })} helperText="URL of the video to add audio to" />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Audio URL" placeholder="https://example.com/audio.mp3" value={form.audio_url} onChange={(e) => setForm({ ...form, audio_url: e.target.value })} helperText="URL of the audio file to add" />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Sync Mode</InputLabel>
                  <Select value={form.sync_mode} label="Sync Mode" onChange={(e) => setForm({ ...form, sync_mode: e.target.value })}>
                    <MenuItem value="replace">Replace Original Audio</MenuItem>
                    <MenuItem value="mix">Mix with Original</MenuItem>
                    <MenuItem value="overlay">Overlay on Original</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Match Length</InputLabel>
                  <Select value={form.match_length} label="Match Length" onChange={(e) => setForm({ ...form, match_length: e.target.value })}>
                    <MenuItem value="video">Match Video Length</MenuItem>
                    <MenuItem value="audio">Match Audio Length</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Video Volume: {form.video_volume}%</Typography>
                <Slider value={form.video_volume} onChange={(_e, value) => setForm({ ...form, video_volume: Array.isArray(value) ? value[0] : value })} min={0} max={100} step={5} />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Audio Volume: {form.audio_volume}%</Typography>
                <Slider value={form.audio_volume} onChange={(_e, value) => setForm({ ...form, audio_volume: Array.isArray(value) ? value[0] : value })} min={0} max={100} step={5} />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Fade In: {form.fade_in_duration}s</Typography>
                <Slider value={form.fade_in_duration} onChange={(_e, value) => setForm({ ...form, fade_in_duration: Array.isArray(value) ? value[0] : value })} min={0} max={10} step={0.5} />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <Typography gutterBottom>Fade Out: {form.fade_out_duration}s</Typography>
                <Slider value={form.fade_out_duration} onChange={(_e, value) => setForm({ ...form, fade_out_duration: Array.isArray(value) ? value[0] : value })} min={0} max={10} step={0.5} />
              </Grid>
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.addaudio ? <CircularProgress size={20} /> : <AddAudioIcon />}
              onClick={handleSubmit}
              disabled={loading.addaudio || !form.video_url.trim() || !form.audio_url.trim()}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' }, maxWidth: { xs: '100%', sm: '300px' } }}
            >
              {loading.addaudio ? 'Adding Audio...' : 'Add Audio'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Audio Settings Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Replace: Remove original audio" variant="outlined" size="small" />
              <Chip label="Mix: Combine with original" variant="outlined" size="small" />
              <Chip label="Overlay: Add on top" variant="outlined" size="small" />
              <Chip label="Fade effects for smooth transitions" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('addaudio', results.addaudio, <AddAudioIcon />)}
      </Grid>
    </Grid>
  );
};

export default AddAudioTab;
