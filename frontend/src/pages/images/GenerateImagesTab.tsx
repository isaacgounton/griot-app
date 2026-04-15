import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Chip
} from '@mui/material';
import {
  AutoAwesome as GenerateIcon
} from '@mui/icons-material';
import { directApi, pollinationsApi } from '../../utils/api';
import { TabContext, ImageGenerationParams, presetDimensions } from './types';

const examplePrompts = [
  'A majestic mountain landscape at sunset with golden light reflecting on a crystal clear lake',
  'Professional portrait of a young woman with curly brown hair, soft natural lighting, studio photography',
  'Modern minimalist workspace with laptop, coffee cup, and plants, clean aesthetic',
  'Futuristic cityscape at night, neon lights, cyberpunk style, detailed digital art',
  'Luxury watch on marble surface, dramatic lighting, commercial product photography'
];

const GenerateImagesTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setError, result, setResult, setPollingJobId, setJobStatus, setJobProgress, pollJobStatus, pollJobStatusPollinations, renderJobResult } = ctx;

  const isMountedRef = useRef(true);
  const lastApiCallTimeRef = useRef(0);
  const modelsCache = useRef<{ models: string[]; timestamp: number } | null>(null);
  const lastProviderRef = useRef<string | null>(null);

  const [imageModels, setImageModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [modelError, setModelError] = useState<string | null>(null);

  const [generateForm, setGenerateForm] = useState<ImageGenerationParams>({
    prompt: '',
    model: 'modal-image',
    width: 576,
    height: 1024,
    steps: 4,
    provider: 'pollinations'
  });

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Ensure generateForm provider is always an AI provider (not stock)
  useEffect(() => {
    if (generateForm.provider === 'pexels' || generateForm.provider === 'pixabay') {
      setGenerateForm(prev => ({
        ...prev,
        provider: 'pollinations'
      }));
    }
  }, [generateForm.provider]);

  // Load dynamic image models ONLY for Pollinations AI provider with aggressive caching
  useEffect(() => {
    const loadImageModels = async () => {
      if (generateForm.provider !== 'pollinations') {
        if (generateForm.provider === 'pexels' || generateForm.provider === 'pixabay') {
          setImageModels([]);
        }
        setLoadingModels(false);
        return;
      }

      const now = Date.now();
      const CACHE_DURATION = 10 * 60 * 1000;

      if (modelsCache.current && (now - modelsCache.current.timestamp) < CACHE_DURATION) {
        setImageModels(modelsCache.current.models);
        setLoadingModels(false);
        setModelError(null);
        return;
      }

      if (!isMountedRef.current) return;

      if (now - lastApiCallTimeRef.current < 30000) {
        setLoadingModels(false);
        return;
      }
      lastApiCallTimeRef.current = now;

      try {
        setLoadingModels(true);
        setModelError(null);

        await new Promise(resolve => setTimeout(resolve, 1000));

        if (!isMountedRef.current || generateForm.provider !== 'pollinations') return;

        const imageModelsResponse = await pollinationsApi.listImageModels();

        if (!isMountedRef.current) return;

        if (imageModelsResponse.success && imageModelsResponse.data && imageModelsResponse.data.models) {
          const rawModels = imageModelsResponse.data.models;
          const models = (Array.isArray(rawModels) ? rawModels : [])
            .filter((m: unknown) => typeof m === 'string' && m.length > 0)
            .map((m: unknown) => String(m).toLowerCase().trim());

          const uniqueModels = Array.from(new Set(models));

          setImageModels(uniqueModels);

          if (generateForm.provider === 'pollinations' && uniqueModels.length > 0) {
            setGenerateForm(prev => ({
              ...prev,
              model: uniqueModels[0]
            }));
          }

          modelsCache.current = {
            models: uniqueModels,
            timestamp: now
          };
        } else {
          throw new Error(imageModelsResponse.error || 'Failed to fetch image models');
        }
      } catch (err) {
        if (!isMountedRef.current) return;

        const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
        setModelError(errorMessage);

        const fallbackModels = ['flux', 'flux-realism', 'flux-cablyai', 'flux-anime', 'turbo', 'nanobanana'];
        setImageModels(fallbackModels);

        if (generateForm.provider === 'pollinations') {
          setGenerateForm(prev => ({
            ...prev,
            model: fallbackModels[0]
          }));
        }

        modelsCache.current = {
          models: fallbackModels,
          timestamp: now - (CACHE_DURATION - 60000)
        };
      } finally {
        if (isMountedRef.current) {
          setLoadingModels(false);
        }
      }
    };

    if (isMountedRef.current) {
      loadImageModels();
    } else {
      setLoadingModels(false);
    }
  }, [generateForm.provider]);

  // Update model when provider changes (with dynamic models)
  React.useEffect(() => {
    if (generateForm.provider === 'pollinations' && imageModels.length > 0) {
      setGenerateForm(prev => {
        if (!imageModels.includes(prev.model || '')) {
          return { ...prev, model: imageModels[0] };
        }
        return prev;
      });
    } else if (generateForm.provider === 'modal_image') {
      setGenerateForm(prev => ({ ...prev, model: 'modal-image' }));
    } else if (generateForm.provider === 'together') {
      if (lastProviderRef.current === 'together') {
        if (imageModels.length > 0 && !imageModels.includes(generateForm.model || '')) {
          setGenerateForm(prev => ({ ...prev, model: imageModels[0] }));
        }
        return;
      }

      lastProviderRef.current = 'together';

      const loadTogetherModels = async () => {
        try {
          setLoadingModels(true);
          const response = await directApi.listTogetherModels();
          if (response?.success && response?.data?.models) {
            const rawModels = response.data.models;
            const models = (Array.isArray(rawModels) ? rawModels : [])
              .filter((m: unknown) => typeof m === 'string' && m.length > 0)
              .map((m: unknown) => String(m).toLowerCase().trim());
            const uniqueModels = Array.from(new Set(models));
            setImageModels(uniqueModels);
            if (uniqueModels.length > 0) {
              setGenerateForm(prev => ({ ...prev, model: uniqueModels[0] }));
            }
          } else {
            setGenerateForm(prev => ({ ...prev, model: 'black-forest-labs/FLUX.1-schnell' }));
          }
        } catch (error) {
          console.error('Failed to load Together models:', error);
          setGenerateForm(prev => ({ ...prev, model: 'black-forest-labs/FLUX.1-schnell' }));
        } finally {
          setLoadingModels(false);
        }
      };
      loadTogetherModels();
    } else {
      lastProviderRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generateForm.provider]);

  const handleGenerateSubmit = async () => {
    if (!generateForm.prompt.trim()) {
      setError('Prompt is required for image generation');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response;

      if (generateForm.provider === 'pollinations') {
        const pollinationsResponse = await pollinationsApi.generateImage({
          prompt: generateForm.prompt,
          model: generateForm.model,
          width: generateForm.width,
          height: generateForm.height,
          seed: generateForm.seed,
          negative_prompt: generateForm.negative_prompt || undefined,
          enhance: false,
          nologo: true,
          safe: false,
          transparent: false
        });

        if (pollinationsResponse.success) {
          response = { data: pollinationsResponse.data };
        } else {
          throw new Error(pollinationsResponse.error || 'Failed to generate image with Pollinations AI');
        }
      } else {
        response = await directApi.post('/images/generate', generateForm);
      }

      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting image generation...');

        if (generateForm.provider === 'pollinations') {
          pollJobStatusPollinations(response.data.job_id);
        } else {
          pollJobStatus(response.data.job_id);
        }
      } else {
        setError('Failed to create image generation job');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <Paper elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3 }}>
      <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          <Grid item xs={12} lg={8}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <GenerateIcon color="primary" />
                  AI Image Generation
                </Typography>

                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Image Description Prompt"
                  placeholder="Describe the image you want to create..."
                  value={generateForm.prompt}
                  onChange={(e) => setGenerateForm({ ...generateForm, prompt: e.target.value })}
                  helperText="Be descriptive and specific for better results."
                  sx={{ mb: 3 }}
                />

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Provider</InputLabel>
                      <Select
                        value={generateForm.provider || 'modal_image'}
                        onChange={(e) => setGenerateForm({ ...generateForm, provider: e.target.value })}
                        label="Provider"
                      >
                        <MenuItem value="together">Together.ai</MenuItem>
                        <MenuItem value="modal_image">Modal Image</MenuItem>
                        <MenuItem value="pollinations">Pollinations AI</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {(generateForm.provider === 'pollinations' || generateForm.provider === 'together') && (
                    <Grid item xs={12} sm={4}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Model</InputLabel>
                        <Select
                          value={(generateForm.model && typeof generateForm.model === 'string' && imageModels.includes(generateForm.model)) ? generateForm.model : ''}
                          label="Model"
                          onChange={(e) => setGenerateForm({ ...generateForm, model: e.target.value })}
                          disabled={loadingModels}
                        >
                          {loadingModels ? (
                            <MenuItem disabled>Loading...</MenuItem>
                          ) : imageModels.length > 0 ? (
                            imageModels.map((model) => {
                              if (typeof model !== 'string') return null;
                              const displayName = model.charAt(0).toUpperCase() + model.slice(1).replace(/-/g, ' ');
                              return (
                                <MenuItem key={model} value={model}>
                                  {displayName}
                                </MenuItem>
                              );
                            })
                          ) : (
                            <MenuItem disabled>No models</MenuItem>
                          )}
                        </Select>
                        {modelError && (
                          <Typography variant="caption" color="error">{modelError}</Typography>
                        )}
                      </FormControl>
                    </Grid>
                  )}

                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Dimensions</InputLabel>
                      <Select
                        value={`${generateForm.width}x${generateForm.height}`}
                        label="Dimensions"
                        onChange={(e) => {
                          const [width, height] = e.target.value.split('x').map(Number);
                          setGenerateForm({ ...generateForm, width, height });
                        }}
                      >
                        {presetDimensions.map((preset) => (
                          <MenuItem key={preset.label} value={`${preset.width}x${preset.height}`}>
                            {preset.label} ({preset.width}x{preset.height})
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={6} sm={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Width"
                      size="small"
                      value={generateForm.width}
                      onChange={(e) => setGenerateForm({ ...generateForm, width: parseInt(e.target.value) })}
                      inputProps={{ min: 256, max: 2048, step: 64 }}
                    />
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Height"
                      size="small"
                      value={generateForm.height}
                      onChange={(e) => setGenerateForm({ ...generateForm, height: parseInt(e.target.value) })}
                      inputProps={{ min: 256, max: 2048, step: 64 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Quality Steps: {generateForm.steps}
                    </Typography>
                    <Slider
                      value={generateForm.steps}
                      onChange={(_e, value) => setGenerateForm({ ...generateForm, steps: Array.isArray(value) ? value[0] : value })}
                      min={1}
                      max={50}
                      step={1}
                      size="small"
                      marks={[
                        { value: 4, label: 'Fast' },
                        { value: 8, label: 'Balanced' },
                        { value: 16, label: 'HQ' },
                        { value: 32, label: 'Ultra' }
                      ]}
                    />
                  </Grid>
                </Grid>

                {generateForm.provider === 'pollinations' && (
                  <TextField
                    fullWidth
                    size="small"
                    label="Negative Prompt (Optional)"
                    placeholder="worst quality, blurry, distorted..."
                    value={generateForm.negative_prompt || ''}
                    onChange={(e) => setGenerateForm({ ...generateForm, negative_prompt: e.target.value })}
                    helperText="Describe what to avoid in the generated image"
                  />
                )}

                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <GenerateIcon />}
                  onClick={handleGenerateSubmit}
                  disabled={loading || !generateForm.prompt.trim()}
                  fullWidth
                  sx={{
                    mt: 3,
                    px: 4,
                    maxWidth: { sm: '300px' },
                    alignSelf: { sm: 'flex-start' }
                  }}
                >
                  {loading ? 'Generating...' : 'Generate Image'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
              <CardContent>
                {renderJobResult(0, result, <GenerateIcon />) || (
                  <>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Example Prompts
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {examplePrompts.map((prompt, index) => (
                        <Chip
                          key={index}
                          label={prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt}
                          onClick={() => setGenerateForm({ ...generateForm, prompt })}
                          sx={{
                            justifyContent: 'flex-start',
                            height: 'auto',
                            '& .MuiChip-label': {
                              display: 'block',
                              whiteSpace: 'normal',
                              textAlign: 'left',
                              padding: '8px 12px'
                            }
                          }}
                        />
                      ))}
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};

export default GenerateImagesTab;
