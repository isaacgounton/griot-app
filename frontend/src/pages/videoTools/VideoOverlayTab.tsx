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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Switch,
  FormControlLabel,
  Slider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Layers as VideoOverlayIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const VideoOverlayTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    base_image_url: '',
    overlay_videos: [{
      url: '',
      x: 0.5,
      y: 0.5,
      width: 0.3,
      height: 0.3,
      start_time: 0.0,
      end_time: null as number | null,
      opacity: 1.0,
      volume: 0.0,
      z_index: 0,
      colorkey_enabled: false,
      colorkey_color: 'green',
      colorkey_similarity: 0.1,
      colorkey_blend: 0.1
    }],
    output_duration: null as number | null,
    frame_rate: 30,
    output_width: null as number | null,
    output_height: null as number | null,
    maintain_aspect_ratio: true
  });

  const handleSubmit = async () => {
    if (!form.base_image_url.trim()) {
      setErrors(prev => ({ ...prev, videooverlay: 'Base image URL is required' }));
      return;
    }
    if (form.overlay_videos.length === 0 || !form.overlay_videos[0].url.trim()) {
      setErrors(prev => ({ ...prev, videooverlay: 'At least one overlay video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, videooverlay: true }));
    setErrors(prev => ({ ...prev, videooverlay: null }));
    setResults(prev => ({ ...prev, videooverlay: null }));

    try {
      const response = await directApi.post('/videos/edit', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'videooverlay');
      } else {
        setErrors(prev => ({ ...prev, videooverlay: 'Failed to create video overlay job' }));
        setLoading(prev => ({ ...prev, videooverlay: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, videooverlay: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, videooverlay: false }));
    }
  };

  const updateOverlayVideo = (index: number, updates: Record<string, unknown>) => {
    const updatedVideos = [...form.overlay_videos];
    updatedVideos[index] = { ...updatedVideos[index], ...updates };
    setForm({ ...form, overlay_videos: updatedVideos });
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <VideoOverlayIcon color="primary" />
              Video Overlay with Chroma Key
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth label="Base Image URL" placeholder="https://example.com/background.jpg"
                  value={form.base_image_url}
                  onChange={(e) => setForm({ ...form, base_image_url: e.target.value })}
                  helperText="Background image where videos will be overlaid"
                />
              </Grid>

              {form.overlay_videos.map((video, index) => (
                <Grid item xs={12} key={index}>
                  <Accordion defaultExpanded>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>Overlay Video {index + 1}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12}>
                          <TextField fullWidth label="Video URL" placeholder="https://example.com/overlay-video.mp4" value={video.url} onChange={(e) => updateOverlayVideo(index, { url: e.target.value })} />
                        </Grid>

                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>X Position: {video.x}</Typography>
                          <Slider value={video.x} onChange={(_e, value) => updateOverlayVideo(index, { x: Array.isArray(value) ? value[0] : value })} min={0} max={1} step={0.01} size="small" />
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>Y Position: {video.y}</Typography>
                          <Slider value={video.y} onChange={(_e, value) => updateOverlayVideo(index, { y: Array.isArray(value) ? value[0] : value })} min={0} max={1} step={0.01} size="small" />
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>Width: {video.width}</Typography>
                          <Slider value={video.width} onChange={(_e, value) => updateOverlayVideo(index, { width: Array.isArray(value) ? value[0] : value })} min={0.1} max={1} step={0.01} size="small" />
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>Height: {video.height}</Typography>
                          <Slider value={video.height} onChange={(_e, value) => updateOverlayVideo(index, { height: Array.isArray(value) ? value[0] : value })} min={0.1} max={1} step={0.01} size="small" />
                        </Grid>

                        {/* Chroma Key */}
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Chroma Key (Green Screen) Settings</Typography>
                          <FormControlLabel
                            control={<Switch checked={video.colorkey_enabled} onChange={(e) => updateOverlayVideo(index, { colorkey_enabled: e.target.checked })} />}
                            label="Enable Chroma Key"
                          />
                          {video.colorkey_enabled && (
                            <Grid container spacing={2} sx={{ mt: 1 }}>
                              <Grid item xs={12} sm={6} md={3}>
                                <FormControl fullWidth size="small">
                                  <InputLabel>Key Color</InputLabel>
                                  <Select value={video.colorkey_color} label="Key Color" onChange={(e) => updateOverlayVideo(index, { colorkey_color: e.target.value })}>
                                    <MenuItem value="green">Green</MenuItem>
                                    <MenuItem value="blue">Blue</MenuItem>
                                    <MenuItem value="red">Red</MenuItem>
                                    <MenuItem value="white">White</MenuItem>
                                    <MenuItem value="black">Black</MenuItem>
                                  </Select>
                                </FormControl>
                              </Grid>
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography gutterBottom fontSize="0.875rem">Similarity: {video.colorkey_similarity}</Typography>
                                <Slider value={video.colorkey_similarity} onChange={(_e, value) => updateOverlayVideo(index, { colorkey_similarity: Array.isArray(value) ? value[0] : value })} min={0.0} max={1.0} step={0.01} size="small" />
                              </Grid>
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography gutterBottom fontSize="0.875rem">Blend: {video.colorkey_blend}</Typography>
                                <Slider value={video.colorkey_blend} onChange={(_e, value) => updateOverlayVideo(index, { colorkey_blend: Array.isArray(value) ? value[0] : value })} min={0.0} max={1.0} step={0.01} size="small" />
                              </Grid>
                            </Grid>
                          )}
                        </Grid>

                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>Opacity: {video.opacity}</Typography>
                          <Slider value={video.opacity} onChange={(_e, value) => updateOverlayVideo(index, { opacity: Array.isArray(value) ? value[0] : value })} min={0} max={1} step={0.01} size="small" />
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography gutterBottom>Volume: {video.volume}</Typography>
                          <Slider value={video.volume} onChange={(_e, value) => updateOverlayVideo(index, { volume: Array.isArray(value) ? value[0] : value })} min={0} max={1} step={0.01} size="small" />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField fullWidth type="number" label="Start Time (seconds)" value={video.start_time} onChange={(e) => updateOverlayVideo(index, { start_time: parseFloat(e.target.value) || 0 })} size="small" />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField fullWidth type="number" label="End Time (seconds, optional)" value={video.end_time || ''} onChange={(e) => updateOverlayVideo(index, { end_time: e.target.value ? parseFloat(e.target.value) : null })} size="small" />
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                </Grid>
              ))}

              <Grid item xs={12} sm={6} lg={4}>
                <TextField fullWidth type="number" label="Frame Rate" value={form.frame_rate} onChange={(e) => setForm({ ...form, frame_rate: parseInt(e.target.value) || 30 })} inputProps={{ min: 15, max: 60 }} size="small" />
              </Grid>
              <Grid item xs={12} sm={6} lg={4}>
                <TextField fullWidth type="number" label="Output Duration (optional)" value={form.output_duration || ''} onChange={(e) => setForm({ ...form, output_duration: e.target.value ? parseFloat(e.target.value) : null })} inputProps={{ min: 0.1, max: 300 }} size="small" />
              </Grid>
              <Grid item xs={12} sm={6} lg={4}>
                <FormControlLabel
                  control={<Switch checked={form.maintain_aspect_ratio} onChange={(e) => setForm({ ...form, maintain_aspect_ratio: e.target.checked })} />}
                  label="Maintain Aspect Ratio"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.videooverlay ? <CircularProgress size={20} /> : <VideoOverlayIcon />}
              onClick={handleSubmit}
              disabled={loading.videooverlay || !form.base_image_url.trim() || !form.overlay_videos[0]?.url.trim()}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' }, maxWidth: { xs: '100%', sm: '300px' } }}
            >
              {loading.videooverlay ? 'Processing...' : 'Create Video Overlay'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Overlay Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Use green screen videos" variant="outlined" size="small" />
              <Chip label="Position with X/Y sliders" variant="outlined" size="small" />
              <Chip label="Adjust opacity & volume" variant="outlined" size="small" />
              <Chip label="Multiple videos supported" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('videooverlay', results.videooverlay, <VideoOverlayIcon />)}
      </Grid>
    </Grid>
  );
};

export default VideoOverlayTab;
