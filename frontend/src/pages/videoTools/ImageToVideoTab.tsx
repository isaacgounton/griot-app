import React, { useState, useEffect } from 'react';
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
  Switch,
  FormControlLabel,
  Slider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Transform as TransformIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import VoiceSelector from '../../components/settings/VoiceSelectorSettings';
import { TabContext } from './types';

// Aligned with backend ImageToVideoRequest model
interface ImageToVideoParams extends Record<string, unknown> {
  image_url: string;
  video_length?: number;
  frame_rate?: number;
  zoom_speed?: number;        // 0-100 scale (backend)
  narrator_speech_text?: string;
  voice?: string;
  provider?: string;           // was tts_provider - aligned with backend
  language?: string;
  narrator_audio_url?: string;
  narrator_vol?: number;
  background_music_url?: string;
  background_music_vol?: number;
  should_add_captions?: boolean;
  caption_properties?: {
    max_words_per_line?: number;
    font_size?: number;
    font_family?: string;
    line_color?: string;       // was color - aligned with VideoCaptionProperties
    position?: string;
    outline_color?: string;    // was stroke_color
    outline_width?: number;    // was stroke_width
    background_color?: string; // was box_color
    background_opacity?: number; // was box_opacity
    alignment?: string;
    spacing?: number;          // was line_spacing
    style?: string;            // was animation
  };
  zoom_direction?: string;     // frontend-only, transformed to effect_type + pan_direction
}

interface Props {
  ctx: TabContext;
}

const exampleImages = [
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
  'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800',
  'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800',
  'https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800'
];

const ImageToVideoTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult, voices } = ctx;

  const [form, setForm] = useState<ImageToVideoParams>({
    image_url: '',
    video_length: 10,
    frame_rate: 30,
    zoom_speed: 10,              // 0-100 scale (was 1.0)
    zoom_direction: 'zoom_in',
    narrator_speech_text: '',
    voice: 'af_heart',
    provider: 'kokoro',          // was tts_provider
    language: 'en',
    narrator_vol: 80,
    background_music_url: '',
    background_music_vol: 20,
    should_add_captions: false,
    caption_properties: {
      max_words_per_line: 10,
      font_size: 48,
      font_family: 'Arial Bold',
      line_color: 'white',       // was color
      position: 'bottom_center',
      outline_color: 'black',    // was stroke_color
      outline_width: 2,          // was stroke_width
      background_color: 'rgba(0,0,0,0.7)', // was box_color
      background_opacity: 0.7,   // was box_opacity
      alignment: 'center',
      spacing: 1,                // was line_spacing (backend expects int)
      style: 'classic'           // was animation:'fade_in'
    }
  });

  // Set default voice from loaded voices
  useEffect(() => {
    if (voices.length > 0) {
      const defaultVoice = voices.find(v => v.provider === 'kokoro' && v.language.toLowerCase().split(/[-_]/)[0] === 'en') ||
        voices.find(v => v.language.toLowerCase().split(/[-_]/)[0] === 'en') ||
        voices[0];

      if (defaultVoice) {
        setForm(prev => ({
          ...prev,
          provider: defaultVoice.provider,
          voice: defaultVoice.name,
          language: defaultVoice.language
        }));
      }
    }
  }, [voices]);

  const handleSubmit = async () => {
    if (!form.image_url.trim()) {
      setErrors(prev => ({ ...prev, videogen: 'Image URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, videogen: true }));
    setErrors(prev => ({ ...prev, videogen: null }));
    setResults(prev => ({ ...prev, videogen: null }));

    try {
      // Transform zoom_direction to effect_type + pan_direction for backend
      const { zoom_direction, ...apiData } = form;
      const directionMap: Record<string, { effect_type: string; pan_direction?: string }> = {
        'zoom_in': { effect_type: 'zoom' },
        'zoom_out': { effect_type: 'zoom_out' },
        'pan_left': { effect_type: 'pan', pan_direction: 'right_to_left' },
        'pan_right': { effect_type: 'pan', pan_direction: 'left_to_right' },
        'pan_up': { effect_type: 'pan', pan_direction: 'bottom_to_top' },
        'pan_down': { effect_type: 'pan', pan_direction: 'top_to_bottom' },
        'static': { effect_type: 'none' },
      };
      const effectMapping = directionMap[zoom_direction || 'zoom_in'] || { effect_type: 'zoom' };
      const payload = { ...apiData, ...effectMapping };

      const response = await directApi.post('/videos/generations', payload);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'videogen');
      } else {
        setErrors(prev => ({ ...prev, videogen: 'Failed to create image-to-video job: No job ID returned' }));
        setLoading(prev => ({ ...prev, videogen: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { status: number; statusText: string; data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      // Pydantic 422 errors return detail as array of {type, loc, msg} — stringify them
      const errorMessage = Array.isArray(detail)
        ? detail.map((d: { msg?: string; loc?: unknown[] }) => d.msg || JSON.stringify(d)).join('; ')
        : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, videogen: errorMessage }));
      setLoading(prev => ({ ...prev, videogen: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography
              variant="h6"
              sx={{
                mb: { xs: 2, sm: 3 },
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                flexWrap: 'wrap'
              }}
            >
              <TransformIcon color="primary" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
              Image to Video Settings
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              {/* Image URL */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Image URL"
                  placeholder="https://example.com/image.jpg"
                  value={form.image_url}
                  onChange={(e) => setForm({ ...form, image_url: e.target.value })}
                  helperText="URL of the image to convert to video"
                />
              </Grid>

              {/* Video Length - max 30 (backend limit) */}
              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Video Length: {form.video_length}s</Typography>
                <Slider
                  value={form.video_length}
                  onChange={(_e, value) => setForm({ ...form, video_length: Array.isArray(value) ? value[0] : value })}
                  min={5}
                  max={30}
                  step={1}
                  marks={[
                    { value: 5, label: '5s' },
                    { value: 15, label: '15s' },
                    { value: 30, label: '30s' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Frame Rate (FPS)"
                  value={form.frame_rate}
                  onChange={(e) => setForm({ ...form, frame_rate: parseInt(e.target.value) })}
                  inputProps={{ min: 15, max: 60 }}
                />
              </Grid>

              {/* Motion Effect */}
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Motion Effect</InputLabel>
                  <Select
                    value={form.zoom_direction}
                    label="Motion Effect"
                    onChange={(e) => setForm({ ...form, zoom_direction: e.target.value })}
                  >
                    <MenuItem value="zoom_in">Zoom In</MenuItem>
                    <MenuItem value="zoom_out">Zoom Out</MenuItem>
                    <MenuItem value="pan_left">Pan Left</MenuItem>
                    <MenuItem value="pan_right">Pan Right</MenuItem>
                    <MenuItem value="pan_up">Pan Up</MenuItem>
                    <MenuItem value="pan_down">Pan Down</MenuItem>
                    <MenuItem value="static">Static (No Movement)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Zoom Speed - 0 to 100 scale (backend) */}
              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom>Zoom Speed: {form.zoom_speed}</Typography>
                <Slider
                  value={form.zoom_speed}
                  onChange={(_e, value) => setForm({ ...form, zoom_speed: Array.isArray(value) ? value[0] : value })}
                  min={0}
                  max={100}
                  step={1}
                  marks={[
                    { value: 0, label: 'Still' },
                    { value: 25, label: 'Slow' },
                    { value: 50, label: 'Normal' },
                    { value: 100, label: 'Fast' }
                  ]}
                />
              </Grid>

              {/* Audio Settings */}
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Audio Settings (Optional)</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={3}
                          label="Narrator Text (Text-to-Speech)"
                          placeholder="Enter text to convert to speech narration..."
                          value={form.narrator_speech_text}
                          onChange={(e) => setForm({ ...form, narrator_speech_text: e.target.value })}
                          helperText="Text will be converted to speech and added as narration"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <VoiceSelector
                          voiceProvider={form.provider || 'kokoro'}
                          voiceName={form.voice || 'af_heart'}
                          language={form.language || 'en'}
                          voices={voices}
                          onVoiceProviderChange={(provider) => setForm(prev => ({ ...prev, provider }))}
                          onVoiceNameChange={(name) => setForm(prev => ({ ...prev, voice: name }))}
                          onLanguageChange={(language) => setForm(prev => ({ ...prev, language }))}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <Typography gutterBottom>Narrator Volume: {form.narrator_vol}%</Typography>
                        <Slider
                          value={form.narrator_vol}
                          onChange={(_e, value) => setForm({ ...form, narrator_vol: Array.isArray(value) ? value[0] : value })}
                          min={0}
                          max={100}
                          step={5}
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Background Music URL (Optional)"
                          placeholder="https://example.com/music.mp3 or YouTube URL"
                          value={form.background_music_url}
                          onChange={(e) => setForm({ ...form, background_music_url: e.target.value })}
                          helperText="URL to background music (supports YouTube URLs)"
                        />
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <Typography gutterBottom>Background Music Volume: {form.background_music_vol}%</Typography>
                        <Slider
                          value={form.background_music_vol}
                          onChange={(_e, value) => setForm({ ...form, background_music_vol: Array.isArray(value) ? value[0] : value })}
                          min={0}
                          max={100}
                          step={5}
                        />
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>

              {/* Caption Settings - field names aligned with VideoCaptionProperties */}
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Caption Settings</Typography>
                    <Box sx={{ ml: 2 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={form.should_add_captions}
                            onChange={(e) => setForm({ ...form, should_add_captions: e.target.checked })}
                          />
                        }
                        label="Enable Captions"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Font Size"
                          value={form.caption_properties?.font_size || 48}
                          onChange={(e) => setForm({
                            ...form,
                            caption_properties: { ...form.caption_properties, font_size: parseInt(e.target.value) }
                          })}
                          inputProps={{ min: 12, max: 120 }}
                          helperText="Font size in pixels"
                        />
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel>Font Family</InputLabel>
                          <Select
                            value={form.caption_properties?.font_family || 'Arial Bold'}
                            label="Font Family"
                            onChange={(e) => setForm({
                              ...form,
                              caption_properties: { ...form.caption_properties, font_family: e.target.value }
                            })}
                          >
                            <MenuItem value="Arial Bold">Arial Bold</MenuItem>
                            <MenuItem value="Helvetica Bold">Helvetica Bold</MenuItem>
                            <MenuItem value="Times New Roman Bold">Times Bold</MenuItem>
                            <MenuItem value="Impact">Impact</MenuItem>
                            <MenuItem value="Montserrat Bold">Montserrat Bold</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6} md={4}>
                        <FormControl fullWidth>
                          <InputLabel>Position</InputLabel>
                          <Select
                            value={form.caption_properties?.position || 'bottom_center'}
                            label="Position"
                            onChange={(e) => setForm({
                              ...form,
                              caption_properties: { ...form.caption_properties, position: e.target.value }
                            })}
                          >
                            <MenuItem value="top">Top</MenuItem>
                            <MenuItem value="center">Center</MenuItem>
                            <MenuItem value="bottom_center">Bottom</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6} md={4}>
                        <FormControl fullWidth>
                          <InputLabel>Caption Style</InputLabel>
                          <Select
                            value={form.caption_properties?.style || 'classic'}
                            label="Caption Style"
                            onChange={(e) => setForm({
                              ...form,
                              caption_properties: { ...form.caption_properties, style: e.target.value }
                            })}
                          >
                            <MenuItem value="classic">Classic</MenuItem>
                            <MenuItem value="karaoke">Karaoke</MenuItem>
                            <MenuItem value="bounce">Bounce</MenuItem>
                            <MenuItem value="viral_bounce">Viral Bounce</MenuItem>
                            <MenuItem value="typewriter">Typewriter</MenuItem>
                            <MenuItem value="word_by_word">Word by Word</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12} sm={6} md={4}>
                        <TextField
                          fullWidth
                          type="number"
                          label="Words Per Line"
                          value={form.caption_properties?.max_words_per_line || 10}
                          onChange={(e) => setForm({
                            ...form,
                            caption_properties: { ...form.caption_properties, max_words_per_line: parseInt(e.target.value) }
                          })}
                          inputProps={{ min: 1, max: 20 }}
                          helperText="Max words per line"
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
              startIcon={loading.videogen ? <CircularProgress size={20} /> : <TransformIcon />}
              onClick={handleSubmit}
              disabled={loading.videogen || !form.image_url.trim()}
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
              {loading.videogen ? 'Processing...' : 'Create Video'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Example Images
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Click any image to use as your source.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {exampleImages.map((url, index) => (
                <Box key={index}>
                  <img
                    src={url}
                    alt={`Example ${index + 1}`}
                    style={{
                      width: '100%',
                      height: '80px',
                      objectFit: 'cover',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      border: form.image_url === url ? '2px solid #1976d2' : '1px solid #e0e0e0'
                    }}
                    onClick={() => setForm({ ...form, image_url: url })}
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setForm({ ...form, image_url: url })}
                    sx={{ mt: 1, width: '100%' }}
                  >
                    Use This Image
                  </Button>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        {renderJobResult('videogen', results.videogen, <TransformIcon />)}
      </Grid>
    </Grid>
  );
};

export default ImageToVideoTab;
