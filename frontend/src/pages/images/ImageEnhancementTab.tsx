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
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  AutoFixHigh as EnhanceIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext, ImageEnhancementParams } from './types';

const ImageEnhancementTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setError, result, setResult, setPollingJobId, setJobStatus, setJobProgress, pollJobStatus, renderJobResult } = ctx;

  const [enhanceForm, setEnhanceForm] = useState<ImageEnhancementParams>({
    image_url: '',
    enhance_color: 1.0,
    enhance_contrast: 1.0,
    noise_strength: 10,
    remove_artifacts: true,
    add_film_grain: false,
    vintage_effect: 0.0,
    output_format: 'png',
    output_quality: 90
  });

  const handleEnhancementSubmit = async () => {
    if (!enhanceForm.image_url.trim()) {
      setError('Image URL is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.post('/images/enhance', enhanceForm);
      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting image enhancement...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to create image enhancement job');
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
                  <EnhanceIcon color="primary" />
                  Image Enhancement & Artifact Removal
                </Typography>

                <Grid container spacing={{ xs: 2, sm: 3 }}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Image URL"
                      placeholder="https://example.com/ai-generated-image.jpg"
                      value={enhanceForm.image_url}
                      onChange={(e) => setEnhanceForm({ ...enhanceForm, image_url: e.target.value })}
                      helperText="URL of the image to enhance and remove AI artifacts from"
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Color Enhancement: {enhanceForm.enhance_color}</Typography>
                    <Slider
                      value={enhanceForm.enhance_color || 1.0}
                      onChange={(_e, value) => setEnhanceForm({ ...enhanceForm, enhance_color: Array.isArray(value) ? value[0] : value })}
                      min={0.0}
                      max={2.0}
                      step={0.1}
                      marks={[
                        { value: 0.0, label: 'B&W' },
                        { value: 1.0, label: 'Normal' },
                        { value: 2.0, label: 'Enhanced' }
                      ]}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Contrast Enhancement: {enhanceForm.enhance_contrast}</Typography>
                    <Slider
                      value={enhanceForm.enhance_contrast || 1.0}
                      onChange={(_e, value) => setEnhanceForm({ ...enhanceForm, enhance_contrast: Array.isArray(value) ? value[0] : value })}
                      min={0.0}
                      max={2.0}
                      step={0.1}
                      marks={[
                        { value: 0.0, label: 'Low' },
                        { value: 1.0, label: 'Normal' },
                        { value: 2.0, label: 'High' }
                      ]}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Noise/Grain Strength: {enhanceForm.noise_strength}</Typography>
                    <Slider
                      value={enhanceForm.noise_strength || 10}
                      onChange={(_e, value) => setEnhanceForm({ ...enhanceForm, noise_strength: Array.isArray(value) ? value[0] : value })}
                      min={0}
                      max={100}
                      step={1}
                      marks={[
                        { value: 0, label: 'None' },
                        { value: 50, label: 'Medium' },
                        { value: 100, label: 'High' }
                      ]}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Vintage Effect: {enhanceForm.vintage_effect}</Typography>
                    <Slider
                      value={enhanceForm.vintage_effect || 0.0}
                      onChange={(_e, value) => setEnhanceForm({ ...enhanceForm, vintage_effect: Array.isArray(value) ? value[0] : value })}
                      min={0.0}
                      max={1.0}
                      step={0.1}
                      marks={[
                        { value: 0.0, label: 'None' },
                        { value: 0.5, label: 'Medium' },
                        { value: 1.0, label: 'Strong' }
                      ]}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={enhanceForm.remove_artifacts || true}
                          onChange={(e) => setEnhanceForm({ ...enhanceForm, remove_artifacts: e.target.checked })}
                        />
                      }
                      label="Remove AI Artifacts"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={enhanceForm.add_film_grain || false}
                          onChange={(e) => setEnhanceForm({ ...enhanceForm, add_film_grain: e.target.checked })}
                        />
                      }
                      label="Add Film Grain Effect"
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Output Format</InputLabel>
                      <Select
                        value={enhanceForm.output_format || 'png'}
                        label="Output Format"
                        onChange={(e) => setEnhanceForm({ ...enhanceForm, output_format: e.target.value })}
                      >
                        <MenuItem value="png">PNG (Best Quality)</MenuItem>
                        <MenuItem value="jpg">JPEG (Smaller Size)</MenuItem>
                        <MenuItem value="webp">WebP (Modern Format)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <EnhanceIcon />}
                  onClick={handleEnhancementSubmit}
                  disabled={loading || !enhanceForm.image_url.trim()}
                  fullWidth
                  sx={{
                    mt: 3,
                    px: 4,
                    maxWidth: { sm: '300px' },
                    alignSelf: { sm: 'flex-start' }
                  }}
                >
                  {loading ? 'Processing...' : 'Enhance Image'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
              <CardContent>
                {renderJobResult(3, result, <EnhanceIcon />) || (
                  <>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Enhancement Tips
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          AI Artifacts
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Enable "Remove AI Artifacts" for images generated by AI models to reduce unnatural patterns.
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Color Enhancement
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Boost color vibrancy for dull images. Values above 1.0 increase saturation.
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Film Grain
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Add subtle texture to make digital images look more like traditional photography.
                        </Typography>
                      </Box>
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

export default ImageEnhancementTab;
