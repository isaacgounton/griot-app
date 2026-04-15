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
  Movie as AIVideoIcon
} from '@mui/icons-material';
import { directApi, pollinationsApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const AIVideoGeneratorTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [form, setForm] = useState({
    prompt: '',
    provider: 'wavespeed',
    negative_prompt: '',
    width: 832,
    height: 480,
    dimensions: '832x480',
    num_frames: 150,
    num_inference_steps: 200,
    guidance_scale: 4.5,
    seed: null as number | null,
    duration: 5,
    use_image_input: false,
    image_url: '',
    videoModel: 'veo',
    audio: false
  });

  const [videoModels, setVideoModels] = useState<{ name: string; description?: string; paid_only?: boolean }[]>([]);
  const [loadingVideoModels, setLoadingVideoModels] = useState(false);

  // Load video models for Pollinations AI
  React.useEffect(() => {
    if (form.provider === 'pollinations') {
      const loadVideoModels = async () => {
        try {
          setLoadingVideoModels(true);
          const response = await pollinationsApi.listVideoModels();
          let models: { name: string; description?: string; paid_only?: boolean }[] = [];
          if (response.success && response.data && response.data.models) {
            // Handle both rich objects and plain strings
            models = response.data.models.map((m: string | { name: string; description?: string; paid_only?: boolean }) =>
              typeof m === 'string' ? { name: m } : m
            );
          }
          setVideoModels(models);
          const modelNames = models.map(m => m.name);
          if (models.length > 0 && !modelNames.includes(form.videoModel)) {
            setForm(prev => ({ ...prev, videoModel: models[0].name }));
          }
        } catch {
          setVideoModels([]);
        } finally {
          setLoadingVideoModels(false);
        }
      };
      loadVideoModels();
    }
  }, [form.provider]);

  // Update duration when provider changes
  const prevProviderRef = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (prevProviderRef.current !== null && prevProviderRef.current !== form.provider) {
      if (form.provider === 'pollinations' && ![4, 6, 8].includes(form.duration)) {
        setForm(prev => ({ ...prev, duration: 4 }));
      } else if (form.provider === 'wavespeed' && ![5, 8].includes(form.duration)) {
        setForm(prev => ({ ...prev, duration: 5 }));
      }
    }
    prevProviderRef.current = form.provider;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.provider]);

  const handleSubmit = async () => {
    if (!form.prompt.trim()) {
      setErrors(prev => ({ ...prev, aivideo: 'Prompt is required' }));
      return;
    }
    if (form.use_image_input && !form.image_url.trim()) {
      setErrors(prev => ({ ...prev, aivideo: 'Image URL is required for image-to-video' }));
      return;
    }
    if (form.provider === 'modal_video' && (form.width % 32 !== 0 || form.height % 32 !== 0)) {
      setErrors(prev => ({ ...prev, aivideo: 'For Modal Video, width and height must be divisible by 32' }));
      return;
    }

    setLoading(prev => ({ ...prev, aivideo: true }));
    setErrors(prev => ({ ...prev, aivideo: null }));
    setResults(prev => ({ ...prev, aivideo: null }));

    try {
      const params: Record<string, unknown> = {
        prompt: form.prompt,
        provider: form.provider,
        negative_prompt: form.negative_prompt || undefined,
        width: form.width,
        height: form.height,
        num_frames: form.num_frames,
        num_inference_steps: form.num_inference_steps,
        guidance_scale: form.guidance_scale,
        seed: form.seed || undefined,
        duration: (form.provider === 'wavespeed' || form.provider === 'pollinations') ? form.duration : undefined,
        ...(form.provider === 'pollinations' && {
          video_model: form.videoModel,
          audio: form.audio,
        })
      };

      let response;
      if (form.use_image_input) {
        response = await directApi.post('/videos/generate-from-image', { ...params, image_url: form.image_url });
      } else {
        response = await directApi.post('/videos/generate', params);
      }

      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'aivideo');
      } else {
        setErrors(prev => ({ ...prev, aivideo: 'Failed to create AI video generation job' }));
        setLoading(prev => ({ ...prev, aivideo: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setErrors(prev => ({ ...prev, aivideo: error.response?.data?.detail || error.message || 'An error occurred' }));
      setLoading(prev => ({ ...prev, aivideo: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
              <AIVideoIcon color="primary" />
              AI Video Generator Settings
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              {/* Mode Toggle */}
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch checked={form.use_image_input} onChange={(e) => setForm({ ...form, use_image_input: e.target.checked })} />}
                  label="Image-to-Video (use an image as starting point)"
                />
              </Grid>

              {form.use_image_input && (
                <Grid item xs={12}>
                  <TextField fullWidth label="Image URL" placeholder="https://example.com/image.jpg" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} helperText="URL of the image to use as starting point" />
                </Grid>
              )}

              <Grid item xs={12}>
                <TextField
                  fullWidth multiline rows={3} label="Prompt"
                  placeholder={form.use_image_input ? "Describe how the image should animate" : "Describe the video you want to create"}
                  value={form.prompt}
                  onChange={(e) => setForm({ ...form, prompt: e.target.value })}
                  helperText={form.use_image_input ? "Describe the motion and animation for your image" : "Describe the video scene you want to generate"}
                />
              </Grid>

              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Advanced Options</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <TextField fullWidth multiline rows={2} label="Negative Prompt (Optional)" placeholder="What to avoid in the video" value={form.negative_prompt} onChange={(e) => setForm({ ...form, negative_prompt: e.target.value })} helperText="Describe what you don't want to see" />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField fullWidth type="number" label="Seed (Optional)" placeholder="Random" value={form.seed || ''} onChange={(e) => setForm({ ...form, seed: e.target.value ? parseInt(e.target.value) : null })} helperText="For reproducible results" />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField fullWidth type="number" label="Num Frames" value={form.num_frames} onChange={(e) => setForm({ ...form, num_frames: parseInt(e.target.value) || 150 })} inputProps={{ min: 50, max: 300 }} helperText="Number of frames to generate" />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField fullWidth type="number" label="Inference Steps" value={form.num_inference_steps} onChange={(e) => setForm({ ...form, num_inference_steps: parseInt(e.target.value) || 200 })} inputProps={{ min: 10, max: 500 }} helperText="Quality vs speed tradeoff" />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography gutterBottom>Guidance Scale: {form.guidance_scale}</Typography>
                        <Slider value={form.guidance_scale} onChange={(_e, value) => setForm({ ...form, guidance_scale: Array.isArray(value) ? value[0] : value })} min={1.0} max={15.0} step={0.1} marks={[{ value: 1.0, label: '1.0' }, { value: 7.5, label: '7.5' }, { value: 15.0, label: '15.0' }]} />
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>

              {/* Provider */}
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Provider</InputLabel>
                  <Select value={form.provider} label="Provider" onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                    <MenuItem value="wavespeed">WaveSpeed (Fast, 5-8s videos)</MenuItem>
                    <MenuItem value="modal_video">Modal Video (High Quality)</MenuItem>
                    <MenuItem value="pollinations">Pollinations AI (Multiple Models)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Pollinations-specific options */}
              {form.provider === 'pollinations' && (
                <>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth disabled={loadingVideoModels}>
                      <InputLabel>Video Model</InputLabel>
                      <Select value={form.videoModel || (videoModels.length > 0 ? videoModels[0].name : 'veo')} label="Video Model" onChange={(e) => setForm({ ...form, videoModel: e.target.value })}>
                        {videoModels.length > 0 ? videoModels.map((model) => (
                          <MenuItem key={model.name} value={model.name}>
                            {model.name}{model.paid_only ? ' (Premium)' : ''}{model.description ? ` - ${model.description}` : ''}
                          </MenuItem>
                        )) : <MenuItem value="veo">veo - Google video generation</MenuItem>}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel control={<Switch checked={form.audio ?? true} onChange={(e) => setForm({ ...form, audio: e.target.checked })} />} label="Enable Built-in Audio" />
                  </Grid>
                </>
              )}

              {/* Duration */}
              {(form.provider === 'wavespeed' || form.provider === 'pollinations') && (
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Duration</InputLabel>
                    <Select value={form.duration} label="Duration" onChange={(e) => setForm({ ...form, duration: e.target.value as number })}>
                      {form.provider === 'wavespeed' ? [
                        <MenuItem key="duration-5" value={5}>5 seconds</MenuItem>,
                        <MenuItem key="duration-8" value={8}>8 seconds</MenuItem>,
                      ] : [
                        <MenuItem key="duration-4" value={4}>4 seconds</MenuItem>,
                        <MenuItem key="duration-6" value={6}>6 seconds</MenuItem>,
                        <MenuItem key="duration-8" value={8}>8 seconds</MenuItem>,
                      ]}
                    </Select>
                  </FormControl>
                </Grid>
              )}

              {/* Dimensions */}
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Dimensions</InputLabel>
                  <Select
                    value={form.dimensions} label="Dimensions"
                    onChange={(e) => {
                      const value = e.target.value;
                      const presets: Record<string, { width: number, height: number }> = {
                        '832x480': { width: 832, height: 480 },
                        '480x832': { width: 480, height: 832 },
                        '704x704': { width: 704, height: 704 },
                        '704x480': { width: 704, height: 480 },
                        '1024x576': { width: 1024, height: 576 },
                        '512x512': { width: 512, height: 512 },
                        '480x854': { width: 480, height: 854 }
                      };
                      const preset = presets[value];
                      if (preset) {
                        setForm({ ...form, dimensions: value, width: preset.width, height: preset.height });
                      } else {
                        setForm({ ...form, dimensions: value });
                      }
                    }}
                  >
                    <MenuItem value="832x480">Landscape HD (832x480)</MenuItem>
                    <MenuItem value="480x832">Portrait HD (480x832)</MenuItem>
                    <MenuItem value="704x704">Square HD (704x704)</MenuItem>
                    <MenuItem value="704x480">Standard HD (704x480)</MenuItem>
                    <MenuItem value="1024x576">Widescreen (1024x576)</MenuItem>
                    <MenuItem value="512x512">Square Standard (512x512)</MenuItem>
                    <MenuItem value="480x854">Vertical Story (480x854)</MenuItem>
                    <MenuItem value="custom">Custom</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {form.dimensions === 'custom' && (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField fullWidth type="number" label="Width" value={form.width} onChange={(e) => { let width = parseInt(e.target.value) || 832; if (form.provider === 'modal_video') width = Math.round(width / 32) * 32; setForm({ ...form, width }); }} inputProps={{ min: 256, max: 1920, step: form.provider === 'modal_video' ? 32 : 1 }} helperText={form.provider === 'modal_video' ? 'Must be divisible by 32' : ''} />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField fullWidth type="number" label="Height" value={form.height} onChange={(e) => { let height = parseInt(e.target.value) || 480; if (form.provider === 'modal_video') height = Math.round(height / 32) * 32; setForm({ ...form, height }); }} inputProps={{ min: 256, max: 1920, step: form.provider === 'modal_video' ? 32 : 1 }} helperText={form.provider === 'modal_video' ? 'Must be divisible by 32' : ''} />
                  </Grid>
                </>
              )}
            </Grid>

            <Button
              variant="contained" size="large"
              startIcon={loading.aivideo ? <CircularProgress size={20} /> : <AIVideoIcon />}
              onClick={handleSubmit}
              disabled={loading.aivideo || !form.prompt.trim()}
              sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 3, sm: 4 }, py: { xs: 1.25, sm: 1.5 }, fontSize: { xs: '0.9rem', sm: '1rem' }, width: { xs: '100%', sm: 'auto' }, minWidth: { xs: '100%', sm: '200px' } }}
            >
              {loading.aivideo ? 'Generating...' : 'Generate Video'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Tips</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Be specific in prompts" variant="outlined" size="small" />
              <Chip label="WaveSpeed: Fast generation" variant="outlined" size="small" />
              <Chip label="Modal Video: Better quality" variant="outlined" size="small" />
              <Chip label="Higher steps = better quality" variant="outlined" size="small" />
              <Chip label="Use seed for consistency" variant="outlined" size="small" />
            </Box>
          </CardContent>
        </Card>
        {renderJobResult('aivideo', results.aivideo, <AIVideoIcon />)}
      </Grid>
    </Grid>
  );
};

export default AIVideoGeneratorTab;
