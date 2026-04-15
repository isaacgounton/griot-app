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
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  PhotoCamera as FluxIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { directApi, pollinationsApi } from '../../utils/api';
import { TabContext, PollinationsEditParams, FALLBACK_EDIT_MODELS } from './types';

const AIImageEditingTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setError, result, setResult, setPollingJobId, setJobStatus, setJobProgress, pollJobStatus, renderJobResult } = ctx;

  const [pollinationsEditForm, setPollinationsEditForm] = useState<PollinationsEditParams>({
    prompt: '',
    model: 'kontext',
    negative_prompt: '',
    seed: undefined
  });

  const [imageEditModels, setImageEditModels] = useState<{ id: string; name: string }[]>(FALLBACK_EDIT_MODELS);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Fetch image edit models from API
  useEffect(() => {
    const loadEditModels = async () => {
      try {
        const resp = await pollinationsApi.listImageEditModels();
        if (resp.success && resp.data?.models?.length) {
          setImageEditModels(resp.data.models.map(m => ({
            id: m.name,
            name: m.description || m.name,
          })));
        }
      } catch {
        // Keep fallback models
      }
    };
    loadEditModels();
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }

      setSelectedFile(file);

      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);
      setError(null);
    }
  };

  const handleFluxEditSubmit = async () => {
    if (!selectedFile) {
      setError('Please select an image file to edit');
      return;
    }

    if (!pollinationsEditForm.prompt.trim()) {
      setError('Edit prompt is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('prompt', pollinationsEditForm.prompt);
      formData.append('model', pollinationsEditForm.model || 'kontext');

      if (pollinationsEditForm.negative_prompt?.trim()) {
        formData.append('negative_prompt', pollinationsEditForm.negative_prompt);
      }
      if (pollinationsEditForm.seed !== undefined && pollinationsEditForm.seed !== null) {
        formData.append('seed', pollinationsEditForm.seed.toString());
      }

      const response = await directApi.post('/images/edit_image', formData);

      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting AI image editing...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to create AI image editing job');
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
                  <FluxIcon color="primary" />
                  AI Image Editing
                </Typography>

                <Grid container spacing={{ xs: 2, sm: 3 }}>
                  {/* File Upload Section */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                        Upload Image to Edit
                      </Typography>
                      <input
                        accept="image/*"
                        style={{ display: 'none' }}
                        id="image-upload"
                        type="file"
                        onChange={handleFileChange}
                      />
                      <label htmlFor="image-upload">
                        <Button
                          variant="outlined"
                          component="span"
                          startIcon={<UploadIcon />}
                          fullWidth
                          sx={{
                            py: 2,
                            borderStyle: 'dashed',
                            borderWidth: 2,
                            borderColor: selectedFile ? 'success.main' : 'grey.300'
                          }}
                        >
                          {selectedFile ? `Selected: ${selectedFile.name}` : 'Choose Image File (PNG, JPG, JPEG)'}
                        </Button>
                      </label>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Max file size: 10MB - Aspect ratio must be between 3:7 and 7:3
                      </Typography>
                    </Box>

                    {/* Image Preview */}
                    {previewUrl && (
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Preview:</Typography>
                        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f8fafc' }}>
                          <img
                            src={previewUrl}
                            alt="Preview"
                            style={{
                              maxWidth: '100%',
                              maxHeight: '200px',
                              borderRadius: '8px',
                              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                            }}
                          />
                        </Paper>
                      </Box>
                    )}
                  </Grid>

                  {/* Editing Parameters */}
                  <Grid item xs={12} md={6}>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={3}
                          label="Edit Description"
                          placeholder="Describe how you want to modify the image..."
                          value={pollinationsEditForm.prompt}
                          onChange={(e) => setPollinationsEditForm({ ...pollinationsEditForm, prompt: e.target.value })}
                          helperText="Be specific about the changes you want to make"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Editing Model</InputLabel>
                          <Select
                            value={pollinationsEditForm.model}
                            label="Editing Model"
                            onChange={(e) => setPollinationsEditForm({ ...pollinationsEditForm, model: e.target.value })}
                          >
                            {imageEditModels.map((m) => (
                              <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Negative Prompt (Optional)"
                          placeholder="worst quality, blurry, distorted..."
                          value={pollinationsEditForm.negative_prompt || ''}
                          onChange={(e) => setPollinationsEditForm({ ...pollinationsEditForm, negative_prompt: e.target.value })}
                          helperText="Describe what to avoid in the result"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          size="small"
                          type="number"
                          label="Seed (Optional)"
                          placeholder="Leave empty for random"
                          value={pollinationsEditForm.seed || ''}
                          onChange={(e) => setPollinationsEditForm({
                            ...pollinationsEditForm,
                            seed: e.target.value ? parseInt(e.target.value) : undefined
                          })}
                          helperText="Use a specific seed for reproducible results"
                        />
                      </Grid>
                    </Grid>
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <FluxIcon />}
                  onClick={handleFluxEditSubmit}
                  disabled={loading || !selectedFile || !pollinationsEditForm.prompt.trim()}
                  fullWidth
                  sx={{
                    mt: 3,
                    px: 4,
                    maxWidth: { sm: '300px' },
                    alignSelf: { sm: 'flex-start' }
                  }}
                >
                  {loading ? 'Editing Image...' : 'Edit Image'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
              <CardContent>
                {renderJobResult(2, result, <FluxIcon />) || (
                  <>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      AI Editing Tips
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Be Specific
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Describe exactly what changes you want. "Make it brighter" works better than "improve it".
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Guidance Scale
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Higher values (7-10) follow your prompt more closely. Lower values (2-4) are more creative.
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Inference Steps
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          More steps (20-50) usually give better quality but take longer to process.
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

export default AIImageEditingTab;
