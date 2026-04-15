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
  Chip
} from '@mui/material';
import { Subtitles as CaptionsIcon } from '@mui/icons-material';
import { directApi } from '../../utils/api';
import CaptionSettings from '../../components/settings/CaptionSettings';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const CaptionsTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    video_url: '',
    captions: '',
    enable_captions: true,
    settings: {
      style: 'classic',
      font_size: 35,
      line_color: '#FFFFFF',
      word_color: '#FFFF00',
      outline_color: '#000000',
      position: 'middle_center',
      max_words_per_line: 4,
      font_family: 'Arial-Bold',
      margin_v: 100,
      outline_width: 4,
      all_caps: false
    },
    language: 'auto'
  });

  const handleSubmit = async () => {
    if (!form.video_url.trim()) {
      setErrors(prev => ({ ...prev, captions: 'Video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, captions: true }));
    setErrors(prev => ({ ...prev, captions: null }));
    setResults(prev => ({ ...prev, captions: null }));

    try {
      // Send only fields the backend CaptionRequest expects
      // (enable_captions is not in the backend model, omit it)
      const { enable_captions: _, ...payload } = form;
      const response = await directApi.post('/videos/add-captions', payload);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'captions');
      } else {
        setErrors(prev => ({ ...prev, captions: 'Failed to create captions job' }));
        setLoading(prev => ({ ...prev, captions: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, captions: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, captions: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <CaptionsIcon color="primary" />
              Add Video Captions
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://example.com/video.mp4"
                  value={form.video_url}
                  onChange={(e) => setForm(prev => ({ ...prev, video_url: e.target.value }))}
                  helperText="URL of the video to add captions to"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Caption Text (Optional)"
                  placeholder="Enter custom caption text or leave empty for auto-transcription..."
                  value={form.captions}
                  onChange={(e) => setForm(prev => ({ ...prev, captions: e.target.value }))}
                  helperText="Leave empty for automatic speech-to-text transcription"
                />
              </Grid>

              <Grid item xs={12}>
                <CaptionSettings
                  enableCaptions={form.enable_captions}
                  captionStyle={form.settings.style}
                  captionColor={form.settings.line_color}
                  highlightColor={form.settings.word_color}
                  captionPosition={form.settings.position}
                  fontSize={form.settings.font_size}
                  fontFamily={form.settings.font_family || 'Arial-Bold'}
                  wordsPerLine={form.settings.max_words_per_line}
                  marginV={form.settings.margin_v}
                  outlineWidth={form.settings.outline_width}
                  allCaps={form.settings.all_caps}
                  onEnableCaptionsChange={(enabled) => setForm(prev => ({ ...prev, enable_captions: enabled }))}
                  onCaptionStyleChange={(style) => setForm(prev => ({ ...prev, settings: { ...prev.settings, style } }))}
                  onCaptionColorChange={(color) => setForm(prev => ({ ...prev, settings: { ...prev.settings, line_color: color } }))}
                  onHighlightColorChange={(color) => setForm(prev => ({ ...prev, settings: { ...prev.settings, word_color: color } }))}
                  onCaptionPositionChange={(position) => setForm(prev => ({ ...prev, settings: { ...prev.settings, position } }))}
                  onFontSizeChange={(size) => setForm(prev => ({ ...prev, settings: { ...prev.settings, font_size: size } }))}
                  onFontFamilyChange={(family) => setForm(prev => ({ ...prev, settings: { ...prev.settings, font_family: family } }))}
                  onWordsPerLineChange={(words) => setForm(prev => ({ ...prev, settings: { ...prev.settings, max_words_per_line: words } }))}
                  onMarginVChange={(margin) => setForm(prev => ({ ...prev, settings: { ...prev.settings, margin_v: margin } }))}
                  onOutlineWidthChange={(width) => setForm(prev => ({ ...prev, settings: { ...prev.settings, outline_width: width } }))}
                  onAllCapsChange={(caps) => setForm(prev => ({ ...prev, settings: { ...prev.settings, all_caps: caps } }))}
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.captions ? <CircularProgress size={20} /> : <CaptionsIcon />}
              onClick={handleSubmit}
              disabled={loading.captions || !form.video_url.trim()}
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
              {loading.captions ? 'Adding Captions...' : 'Add Captions'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Caption Styles</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Classic Subtitles" variant="outlined" size="small" />
              <Chip label="TikTok Viral Bounce" variant="outlined" size="small" />
              <Chip label="Karaoke Highlighting" variant="outlined" size="small" />
              <Chip label="Modern Neon Glow" variant="outlined" size="small" />
              <Chip label="Auto Transcription" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('captions', results.captions, <CaptionsIcon />)}
      </Grid>
    </Grid>
  );
};

export default CaptionsTab;
