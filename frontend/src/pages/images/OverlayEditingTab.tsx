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
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Edit as EditIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext, ImageEditParams, OverlayImage } from './types';

const OverlayEditingTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setError, result, setResult, setPollingJobId, setJobStatus, setJobProgress, pollJobStatus, renderJobResult } = ctx;

  const [editForm, setEditForm] = useState<ImageEditParams>({
    base_image_url: '',
    overlay_images: [],
    output_format: 'png',
    output_quality: 90,
    maintain_aspect_ratio: true,
    stitch_mode: false,
    stitch_direction: 'horizontal',
    stitch_spacing: 0,
    stitch_max_width: 1920,
    stitch_max_height: 1080
  });

  const addOverlayImage = () => {
    setEditForm(prev => ({
      ...prev,
      overlay_images: [
        ...prev.overlay_images,
        {
          url: '',
          x: 0.5,
          y: 0.5,
          width: 0.2,
          height: 0.2,
          rotation: 0,
          opacity: 1.0,
          z_index: prev.overlay_images.length
        }
      ]
    }));
  };

  const removeOverlayImage = (index: number) => {
    setEditForm(prev => ({
      ...prev,
      overlay_images: prev.overlay_images.filter((_, i) => i !== index)
    }));
  };

  const updateOverlayImage = (index: number, field: keyof OverlayImage, value: string | number | number[]) => {
    setEditForm(prev => ({
      ...prev,
      overlay_images: prev.overlay_images.map((overlay, i) =>
        i === index ? { ...overlay, [field]: value } : overlay
      )
    }));
  };

  const handleEditSubmit = async () => {
    if (!editForm.base_image_url.trim()) {
      setError('Base image URL is required');
      return;
    }

    if (editForm.overlay_images.length === 0) {
      setError('At least one overlay image is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.post('/images/edit', editForm);
      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting image editing...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to create image editing job');
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
                  <EditIcon color="primary" />
                  Image Editing & Overlay
                </Typography>

                <Grid container spacing={{ xs: 2, sm: 3 }}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Base Image URL"
                      placeholder="https://example.com/base-image.jpg"
                      value={editForm.base_image_url}
                      onChange={(e) => setEditForm({ ...editForm, base_image_url: e.target.value })}
                      helperText="URL of the base image on which overlays will be placed"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Overlay Images ({editForm.overlay_images.length})
                      </Typography>
                      <Button
                        startIcon={<AddIcon />}
                        onClick={addOverlayImage}
                        variant="outlined"
                        size="small"
                      >
                        Add Overlay
                      </Button>
                    </Box>

                    {editForm.overlay_images.map((overlay, index) => (
                      <Accordion key={index} sx={{ mb: 2 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography>
                            Overlay {index + 1} {overlay.url ? `(${overlay.url.substring(0, 50)}...)` : '(Empty)'}
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Grid container spacing={2}>
                            <Grid item xs={12}>
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <TextField
                                  fullWidth
                                  label="Image URL"
                                  placeholder="https://example.com/overlay.png"
                                  value={overlay.url}
                                  onChange={(e) => updateOverlayImage(index, 'url', e.target.value)}
                                />
                                <IconButton
                                  color="error"
                                  onClick={() => removeOverlayImage(index)}
                                  size="small"
                                >
                                  <RemoveIcon />
                                </IconButton>
                              </Box>
                            </Grid>

                            <Grid item xs={6} sm={4} md={3}>
                              <Typography gutterBottom>X Position: {overlay.x}</Typography>
                              <Slider
                                value={overlay.x}
                                onChange={(_e, value) => updateOverlayImage(index, 'x', Array.isArray(value) ? value[0] : value)}
                                min={0}
                                max={1}
                                step={0.01}
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={6} sm={4} md={3}>
                              <Typography gutterBottom>Y Position: {overlay.y}</Typography>
                              <Slider
                                value={overlay.y}
                                onChange={(_e, value) => updateOverlayImage(index, 'y', Array.isArray(value) ? value[0] : value)}
                                min={0}
                                max={1}
                                step={0.01}
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={6} sm={4} md={3}>
                              <Typography gutterBottom>Width: {overlay.width}</Typography>
                              <Slider
                                value={overlay.width || 0.2}
                                onChange={(_e, value) => updateOverlayImage(index, 'width', Array.isArray(value) ? value[0] : value)}
                                min={0.05}
                                max={1}
                                step={0.01}
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={6} sm={4} md={3}>
                              <Typography gutterBottom>Opacity: {overlay.opacity}</Typography>
                              <Slider
                                value={overlay.opacity || 1}
                                onChange={(_e, value) => updateOverlayImage(index, 'opacity', Array.isArray(value) ? value[0] : value)}
                                min={0}
                                max={1}
                                step={0.01}
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <TextField
                                fullWidth
                                type="number"
                                label="Rotation (degrees)"
                                value={overlay.rotation || 0}
                                onChange={(e) => updateOverlayImage(index, 'rotation', parseFloat(e.target.value))}
                                inputProps={{ min: 0, max: 359.99, step: 0.1 }}
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <TextField
                                fullWidth
                                type="number"
                                label="Z-Index (layer order)"
                                value={overlay.z_index || 0}
                                onChange={(e) => updateOverlayImage(index, 'z_index', parseInt(e.target.value))}
                                inputProps={{ min: 0, max: 100 }}
                                size="small"
                              />
                            </Grid>
                          </Grid>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Output Format</InputLabel>
                      <Select
                        value={editForm.output_format}
                        label="Output Format"
                        onChange={(e) => setEditForm({ ...editForm, output_format: e.target.value })}
                      >
                        <MenuItem value="png">PNG (Transparency support)</MenuItem>
                        <MenuItem value="jpg">JPEG (Smaller file size)</MenuItem>
                        <MenuItem value="webp">WebP (Modern format)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Quality: {editForm.output_quality}%</Typography>
                    <Slider
                      value={editForm.output_quality || 90}
                      onChange={(_e, value) => setEditForm({ ...editForm, output_quality: Array.isArray(value) ? value[0] : value })}
                      min={1}
                      max={100}
                      step={1}
                    />
                  </Grid>

                  {/* Image Stitching Settings */}
                  <Grid item xs={12}>
                    <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                      Image Stitching Mode
                    </Typography>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={editForm.stitch_mode || false}
                          onChange={(e) => setEditForm({ ...editForm, stitch_mode: e.target.checked })}
                        />
                      }
                      label="Enable Stitching Mode (combine images instead of overlaying)"
                      sx={{ mb: 2 }}
                    />

                    {editForm.stitch_mode && (
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} lg={4}>
                          <FormControl fullWidth>
                            <InputLabel>Stitch Direction</InputLabel>
                            <Select
                              value={editForm.stitch_direction || 'horizontal'}
                              label="Stitch Direction"
                              onChange={(e) => setEditForm({ ...editForm, stitch_direction: e.target.value })}
                            >
                              <MenuItem value="horizontal">Horizontal</MenuItem>
                              <MenuItem value="vertical">Vertical</MenuItem>
                              <MenuItem value="grid">Grid</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>

                        <Grid item xs={12} sm={6} lg={4}>
                          <Typography gutterBottom>Spacing: {editForm.stitch_spacing || 0}px</Typography>
                          <Slider
                            value={editForm.stitch_spacing || 0}
                            onChange={(_e, value) => setEditForm({ ...editForm, stitch_spacing: Array.isArray(value) ? value[0] : value })}
                            min={0}
                            max={100}
                            step={1}
                          />
                        </Grid>

                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            type="number"
                            label="Max Width"
                            value={editForm.stitch_max_width || 1920}
                            onChange={(e) => setEditForm({ ...editForm, stitch_max_width: parseInt(e.target.value) })}
                            inputProps={{ min: 100, max: 4096 }}
                            size="small"
                          />
                          <TextField
                            fullWidth
                            type="number"
                            label="Max Height"
                            value={editForm.stitch_max_height || 1080}
                            onChange={(e) => setEditForm({ ...editForm, stitch_max_height: parseInt(e.target.value) })}
                            inputProps={{ min: 100, max: 4096 }}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </Grid>
                      </Grid>
                    )}
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <EditIcon />}
                  onClick={handleEditSubmit}
                  disabled={loading || !editForm.base_image_url.trim() || editForm.overlay_images.length === 0}
                  fullWidth
                  sx={{
                    mt: 3,
                    px: 4,
                    maxWidth: { sm: '300px' },
                    alignSelf: { sm: 'flex-start' }
                  }}
                >
                  {loading ? 'Processing...' : 'Apply Edits'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
              <CardContent>
                {renderJobResult(1, result, <EditIcon />) || (
                  <>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Overlay Tips
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Positioning
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Use X/Y sliders (0-1) to position overlays. 0.5 = center, 0.0 = left/top edge.
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Layering
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Higher Z-Index values appear on top. Use opacity for transparency effects.
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                          Stitching Mode
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Combine multiple images side-by-side instead of overlaying them.
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

export default OverlayEditingTab;
