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
  YouTube as YouTubeIcon,
  ExpandMore as ExpandMoreIcon,
  AutoAwesome as SmartIcon,
  VideoFile as VideoIcon,
  Face as FaceIcon,
  VolumeUp as AudioIcon,
  CropFree as CropIcon,
  AutoFixHigh as EnhanceIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

const YouTubeShortsTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  // YouTube Shorts form state
  const [shortsForm, setShortsForm] = useState({
    video_url: '',
    max_duration: 60,
    quality: 'high',
    output_format: 'mp4',
    use_ai_highlight: true,
    crop_to_vertical: true,
    speaker_tracking: true,
    custom_start_time: null as number | null,
    custom_end_time: null as number | null,
    enhance_audio: true,
    smooth_transitions: true,
    create_thumbnail: true,
    target_resolution: '720x1280',
    audio_enhancement_level: 'speech',
    face_tracking_sensitivity: 'medium',
    cookies_url: ''
  });

  const handleShortsSubmit = async () => {
    // Validate YouTube URL
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
    if (!youtubeRegex.test(shortsForm.video_url)) {
      setErrors(prev => ({ ...prev, shorts: 'Please enter a valid YouTube URL' }));
      return;
    }

    setLoading(prev => ({ ...prev, shorts: true }));
    setErrors(prev => ({ ...prev, shorts: null }));
    setResults(prev => ({ ...prev, shorts: null }));

    try {
      const response = await directApi.post('/yt-shorts/create', shortsForm);
      if (response.data && response.data.job_id) {
        setResults(prev => ({ ...prev, shorts: response.data }));
        pollJobStatus(response.data.job_id, 'shorts');
      } else {
        setErrors(prev => ({ ...prev, shorts: 'Failed to create YouTube Shorts job' }));
        setLoading(prev => ({ ...prev, shorts: false }));
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const errorMessage = axiosErr.response?.data?.detail || axiosErr.message || 'An error occurred';
      setErrors(prev => ({ ...prev, shorts: errorMessage }));
      setLoading(prev => ({ ...prev, shorts: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} md={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <YouTubeIcon color="primary" />
              YouTube Shorts Settings
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              {/* YouTube URL */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="YouTube Video URL"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={shortsForm.video_url}
                  onChange={(e) => setShortsForm({ ...shortsForm, video_url: e.target.value })}
                  helperText="Enter the YouTube video URL to convert to shorts"
                />
              </Grid>

              {/* Cookies URL for restricted videos */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Cookies URL (Optional)"
                  placeholder="https://example.com/cookies.txt"
                  value={shortsForm.cookies_url}
                  onChange={(e) => setShortsForm({ ...shortsForm, cookies_url: e.target.value })}
                  helperText="URL to download cookies file for accessing restricted YouTube videos"
                />
              </Grid>

              {/* Basic Settings */}
              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Max Duration: {shortsForm.max_duration}s</Typography>
                <Slider
                  value={shortsForm.max_duration}
                  onChange={(_e, value) => setShortsForm({ ...shortsForm, max_duration: Array.isArray(value) ? value[0] : value })}
                  min={5}
                  max={300}
                  step={5}
                  marks={[
                    { value: 15, label: '15s' },
                    { value: 60, label: '60s' },
                    { value: 120, label: '2m' },
                    { value: 300, label: '5m' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Quality</InputLabel>
                  <Select
                    value={shortsForm.quality}
                    label="Quality"
                    onChange={(e) => setShortsForm({ ...shortsForm, quality: e.target.value })}
                  >
                    <MenuItem value="low">Low (Fast)</MenuItem>
                    <MenuItem value="medium">Medium (Balanced)</MenuItem>
                    <MenuItem value="high">High (Recommended)</MenuItem>
                    <MenuItem value="ultra">Ultra (Best Quality)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Target Resolution</InputLabel>
                  <Select
                    value={shortsForm.target_resolution}
                    label="Target Resolution"
                    onChange={(e) => setShortsForm({ ...shortsForm, target_resolution: e.target.value })}
                  >
                    <MenuItem value="480x854">480x854 (Low)</MenuItem>
                    <MenuItem value="720x1280">720x1280 (HD)</MenuItem>
                    <MenuItem value="1080x1920">1080x1920 (Full HD)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* AI and Processing Options */}
              <Grid item xs={12}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SmartIcon color="primary" />
                      AI & Processing Options
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.use_ai_highlight}
                              onChange={(e) => setShortsForm({ ...shortsForm, use_ai_highlight: e.target.checked })}
                            />
                          }
                          label="AI Highlight Detection"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Use GPT-4 to automatically detect the best segments
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.speaker_tracking}
                              onChange={(e) => setShortsForm({ ...shortsForm, speaker_tracking: e.target.checked })}
                            />
                          }
                          label="Speaker Tracking"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Advanced speaker detection and tracking
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.crop_to_vertical}
                              onChange={(e) => setShortsForm({ ...shortsForm, crop_to_vertical: e.target.checked })}
                            />
                          }
                          label="Vertical Crop (9:16)"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Dynamic face-following crop for mobile formats
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.enhance_audio}
                              onChange={(e) => setShortsForm({ ...shortsForm, enhance_audio: e.target.checked })}
                            />
                          }
                          label="Audio Enhancement"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Speech optimization and noise reduction
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.smooth_transitions}
                              onChange={(e) => setShortsForm({ ...shortsForm, smooth_transitions: e.target.checked })}
                            />
                          }
                          label="Smooth Transitions"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Add fade effects and smooth transitions
                        </Typography>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={shortsForm.create_thumbnail}
                              onChange={(e) => setShortsForm({ ...shortsForm, create_thumbnail: e.target.checked })}
                            />
                          }
                          label="Generate Thumbnail"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Create preview thumbnail automatically
                        </Typography>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>

              {/* Advanced Settings */}
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Advanced Settings</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6} md={4}>
                        <FormControl fullWidth>
                          <InputLabel>Audio Enhancement Level</InputLabel>
                          <Select
                            value={shortsForm.audio_enhancement_level}
                            label="Audio Enhancement Level"
                            onChange={(e) => setShortsForm({ ...shortsForm, audio_enhancement_level: e.target.value })}
                          >
                            <MenuItem value="speech">Speech Optimization</MenuItem>
                            <MenuItem value="music">Music Enhancement</MenuItem>
                            <MenuItem value="auto">Auto Detection</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6} md={4}>
                        <FormControl fullWidth>
                          <InputLabel>Face Tracking Sensitivity</InputLabel>
                          <Select
                            value={shortsForm.face_tracking_sensitivity}
                            label="Face Tracking Sensitivity"
                            onChange={(e) => setShortsForm({ ...shortsForm, face_tracking_sensitivity: e.target.value })}
                          >
                            <MenuItem value="low">Low</MenuItem>
                            <MenuItem value="medium">Medium</MenuItem>
                            <MenuItem value="high">High</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6} md={4}>
                        <FormControl fullWidth>
                          <InputLabel>Output Format</InputLabel>
                          <Select
                            value={shortsForm.output_format}
                            label="Output Format"
                            onChange={(e) => setShortsForm({ ...shortsForm, output_format: e.target.value })}
                          >
                            <MenuItem value="mp4">MP4 (Recommended)</MenuItem>
                            <MenuItem value="webm">WebM</MenuItem>
                            <MenuItem value="mov">MOV</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Custom Start Time (seconds)"
                          placeholder="Leave empty for AI selection"
                          value={shortsForm.custom_start_time || ''}
                          onChange={(e) => setShortsForm({
                            ...shortsForm,
                            custom_start_time: e.target.value ? parseInt(e.target.value) : null
                          })}
                          helperText="Override AI highlight detection"
                        />
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Custom End Time (seconds)"
                          placeholder="Leave empty for AI selection"
                          value={shortsForm.custom_end_time || ''}
                          onChange={(e) => setShortsForm({
                            ...shortsForm,
                            custom_end_time: e.target.value ? parseInt(e.target.value) : null
                          })}
                          helperText="Override AI highlight detection"
                        />
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.shorts ? <CircularProgress size={20} /> : <VideoIcon />}
              onClick={handleShortsSubmit}
              disabled={loading.shorts || !shortsForm.video_url.trim()}
              sx={{ mt: 3, px: 4, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.shorts ? 'Processing...' : 'Create YouTube Short'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        {renderJobResult('shorts', results.shorts, <YouTubeIcon />) || (
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Advanced Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Chip icon={<SmartIcon />} label="AI Highlight Detection" variant="outlined" />
                <Chip icon={<FaceIcon />} label="Face Tracking & Cropping" variant="outlined" />
                <Chip icon={<AudioIcon />} label="Voice Activity Detection" variant="outlined" />
                <Chip icon={<CropIcon />} label="Dynamic Vertical Crop" variant="outlined" />
                <Chip icon={<EnhanceIcon />} label="Audio Enhancement" variant="outlined" />
                <Chip icon={<VideoIcon />} label="Professional Optimization" variant="outlined" />
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                This generator uses advanced AI to automatically detect the best segments, track speakers,
                and optimize your content for YouTube Shorts, TikTok, and Instagram Reels.
              </Typography>
            </CardContent>
          </Card>
        )}
      </Grid>
    </Grid>
  );
};

export default YouTubeShortsTab;
