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
import { SmartToy as AIIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const AIClipsTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    ai_query: '',
    max_clips: 5,
    output_format: 'mp4',
    quality: 'medium'
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim() || !form.ai_query.trim()) {
      setErrors(prev => ({ ...prev, aiclips: 'Video URL and AI query are required' }));
      return;
    }

    setLoading(prev => ({ ...prev, aiclips: true }));
    setErrors(prev => ({ ...prev, aiclips: null }));
    setResults(prev => ({ ...prev, aiclips: null }));

    try {
      const response = await directApi.post('/videos/clips', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'aiclips');
      } else {
        setErrors(prev => ({ ...prev, aiclips: 'Failed to create AI clips job' }));
        setLoading(prev => ({ ...prev, aiclips: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, aiclips: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, aiclips: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <AIIcon color="primary" />
              AI-Powered Video Clips
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://example.com/video.mp4"
                  value={form.video_url}
                  onChange={(e) => setForm({ ...form, video_url: e.target.value })}
                  helperText="URL of the video to extract clips from"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="AI Query"
                  placeholder="Find clips discussing machine learning and AI techniques..."
                  value={form.ai_query}
                  onChange={(e) => setForm({ ...form, ai_query: e.target.value })}
                  helperText="Describe what kind of clips you want to extract"
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Max Clips: {form.max_clips}</Typography>
                <Slider
                  value={form.max_clips}
                  onChange={(_e, value) => setForm({ ...form, max_clips: Array.isArray(value) ? value[0] : value })}
                  min={1}
                  max={20}
                  step={1}
                  marks={[
                    { value: 1, label: '1' },
                    { value: 5, label: '5' },
                    { value: 10, label: '10' },
                    { value: 20, label: '20' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Output Format</InputLabel>
                  <Select
                    value={form.output_format}
                    label="Output Format"
                    onChange={(e) => setForm({ ...form, output_format: e.target.value })}
                  >
                    <MenuItem value="mp4">MP4</MenuItem>
                    <MenuItem value="webm">WebM</MenuItem>
                    <MenuItem value="avi">AVI</MenuItem>
                    <MenuItem value="mov">MOV</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Quality</InputLabel>
                  <Select
                    value={form.quality}
                    label="Quality"
                    onChange={(e) => setForm({ ...form, quality: e.target.value })}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.aiclips ? <CircularProgress size={20} /> : <AIIcon />}
              onClick={handleSubmit}
              disabled={loading.aiclips || !form.video_url.trim() || !form.ai_query.trim()}
              sx={{
                mt: { xs: 2, sm: 3 },
                px: { xs: 3, sm: 4 },
                py: { xs: 1.25, sm: 1.5 },
                fontSize: { xs: '0.9rem', sm: '1rem' },
                width: { xs: '100%', sm: 'auto' },
                minWidth: { xs: '100%', sm: '200px' },
                maxWidth: { xs: '100%', sm: '300px' }
              }}
            >
              {loading.aiclips ? 'Processing...' : 'Extract AI Clips'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              AI Query Examples
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Find funny moments" variant="outlined" size="small" onClick={() => setForm({ ...form, ai_query: "Find funny moments and jokes" })} sx={{ cursor: 'pointer' }} />
              <Chip label="Extract key points" variant="outlined" size="small" onClick={() => setForm({ ...form, ai_query: "Find segments explaining key concepts" })} sx={{ cursor: 'pointer' }} />
              <Chip label="Technical discussions" variant="outlined" size="small" onClick={() => setForm({ ...form, ai_query: "Extract technical discussions and programming topics" })} sx={{ cursor: 'pointer' }} />
              <Chip label="Q&A segments" variant="outlined" size="small" onClick={() => setForm({ ...form, ai_query: "Find question and answer sessions" })} sx={{ cursor: 'pointer' }} />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('aiclips', results.aiclips, <AIIcon />)}
      </Grid>
    </Grid>
  );
};

export default AIClipsTab;
