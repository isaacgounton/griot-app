import React, { useState } from 'react';
import {
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
  Switch,
  FormControlLabel,
  Slider
} from '@mui/material';
import { TextFields as TextOverlayIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import VideoPreviewWithOverlay from './VideoPreviewWithOverlay';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const TextOverlayTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    text: '',
    options: {
      duration: 5,
      font_size: 48,
      font_color: 'white',
      box_color: 'black',
      box_opacity: 0.8,
      box_padding: 60,
      position: 'bottom-center',
      y_offset: 50,
      line_spacing: 8,
      auto_wrap: true,
      max_chars_per_line: 25
    }
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim() || !form.text.trim()) {
      setErrors(prev => ({ ...prev, textoverlay: 'Video URL and text are required' }));
      return;
    }

    setLoading(prev => ({ ...prev, textoverlay: true }));
    setErrors(prev => ({ ...prev, textoverlay: null }));
    setResults(prev => ({ ...prev, textoverlay: null }));

    try {
      const response = await directApi.post('/videos/text-overlay', form);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'textoverlay');
      } else {
        setErrors(prev => ({ ...prev, textoverlay: 'Failed to create text overlay job' }));
        setLoading(prev => ({ ...prev, textoverlay: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, textoverlay: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, textoverlay: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <TextOverlayIcon color="primary" />
              Add Text Overlay
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://example.com/video.mp4"
                  value={form.video_url}
                  onChange={(e) => setForm({ ...form, video_url: e.target.value })}
                  helperText="URL of the video to add text overlay to"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Overlay Text"
                  placeholder="Enter text to overlay on the video..."
                  value={form.text}
                  onChange={(e) => setForm({ ...form, text: e.target.value })}
                  helperText="Text content to display on the video"
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>Quick Presets</Typography>
                <Grid container spacing={{ xs: 1, sm: 2 }}>
                  {[
                    { key: 'title', name: 'Title', desc: 'Large title at top', icon: 'T' },
                    { key: 'subtitle', name: 'Subtitle', desc: 'Bottom subtitle', icon: 'S' },
                    { key: 'watermark', name: 'Watermark', desc: 'Small corner text', icon: 'W' },
                    { key: 'alert', name: 'Alert', desc: 'Center notification', icon: '!' },
                    { key: 'caption', name: 'Caption', desc: 'Clean white caption', icon: 'C' }
                  ].map((preset) => (
                    <Grid item xs={4} sm={4} md={2.4} key={preset.key}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          border: '2px solid transparent',
                          '&:hover': { borderColor: 'primary.main', transform: 'translateY(-2px)' },
                          transition: 'all 0.2s ease-in-out'
                        }}
                        onClick={async () => {
                          try {
                            const response = await directApi.getTextOverlayPresets();
                            if (!response.success || !response.data) throw new Error(response.error || 'Failed to load presets');
                            const presetConfig = (response.data.presets as Record<string, { options?: Record<string, unknown> }> | undefined)?.[preset.key];
                            if (presetConfig && presetConfig.options) {
                              const opts = presetConfig.options;
                              setForm({
                                ...form,
                                options: {
                                  ...form.options,
                                  ...(opts as Partial<typeof form.options>),
                                  box_padding: (opts.box_padding as number) || (opts.boxborderw as number) || form.options.box_padding
                                }
                              });
                            }
                          } catch (error) {
                            console.error('Error loading preset:', error);
                          }
                        }}
                      >
                        <CardContent sx={{ p: { xs: 1, sm: 2 }, textAlign: 'center', '&:last-child': { pb: { xs: 1, sm: 2 } } }}>
                          <Typography variant="h6" sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' }, mb: 0.5 }}>{preset.icon}</Typography>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5, fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>{preset.name}</Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.7rem' } }}>{preset.desc}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Duration: {form.options.duration}s</Typography>
                <Slider
                  value={form.options.duration}
                  onChange={(_e, value) => setForm({ ...form, options: { ...form.options, duration: Array.isArray(value) ? value[0] : value } })}
                  min={1} max={60} step={1}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Font Size: {form.options.font_size}px</Typography>
                <Slider
                  value={form.options.font_size}
                  onChange={(_e, value) => setForm({ ...form, options: { ...form.options, font_size: Array.isArray(value) ? value[0] : value } })}
                  min={12} max={200} step={4}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Position</InputLabel>
                  <Select
                    value={form.options.position}
                    label="Position"
                    onChange={(e) => setForm({ ...form, options: { ...form.options, position: e.target.value } })}
                  >
                    <MenuItem value="top-left">Top Left</MenuItem>
                    <MenuItem value="top-center">Top Center</MenuItem>
                    <MenuItem value="top-right">Top Right</MenuItem>
                    <MenuItem value="center-left">Center Left</MenuItem>
                    <MenuItem value="center">Center</MenuItem>
                    <MenuItem value="center-right">Center Right</MenuItem>
                    <MenuItem value="bottom-left">Bottom Left</MenuItem>
                    <MenuItem value="bottom-center">Bottom Center</MenuItem>
                    <MenuItem value="bottom-right">Bottom Right</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Font Color"
                  value={form.options.font_color}
                  onChange={(e) => setForm({ ...form, options: { ...form.options, font_color: e.target.value } })}
                  placeholder="white, #FFFFFF"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Background Color"
                  value={form.options.box_color}
                  onChange={(e) => setForm({ ...form, options: { ...form.options, box_color: e.target.value } })}
                  placeholder="black, #000000"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Background Opacity: {Math.round(form.options.box_opacity * 100)}%</Typography>
                <Slider
                  value={form.options.box_opacity}
                  onChange={(_e, value) => setForm({ ...form, options: { ...form.options, box_opacity: Array.isArray(value) ? value[0] : value } })}
                  min={0} max={1} step={0.1}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Background Padding: {form.options.box_padding}px</Typography>
                <Slider
                  value={form.options.box_padding}
                  onChange={(_e, value) => setForm({ ...form, options: { ...form.options, box_padding: Array.isArray(value) ? value[0] : value } })}
                  min={5} max={150} step={5}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={form.options.auto_wrap}
                      onChange={(e) => setForm({ ...form, options: { ...form.options, auto_wrap: e.target.checked } })}
                    />
                  }
                  label="Auto-wrap Text"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.textoverlay ? <CircularProgress size={20} /> : <TextOverlayIcon />}
              onClick={handleSubmit}
              disabled={loading.textoverlay || !form.video_url.trim() || !form.text.trim()}
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
              {loading.textoverlay ? 'Adding Overlay...' : 'Add Text Overlay'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <VideoPreviewWithOverlay
          videoUrl={form.video_url}
          text={form.text}
          options={form.options}
        />
        {renderJobResult('textoverlay', results.textoverlay, <TextOverlayIcon />)}
      </Grid>
    </Grid>
  );
};

export default TextOverlayTab;
