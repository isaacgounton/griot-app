import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  TextField,
  Typography
} from '@mui/material';
import {
  SmartDisplay as VideoAnalysisIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { pollinationsApi } from '../../utils/api';
import { ModelObject, ModelOption, TextModelsResponse, VideoAnalysisParams } from '../../types/pollinations';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const MAX_VIDEO_SIZE_BYTES = 25 * 1024 * 1024;

const EXAMPLE_PROMPTS = [
  'Summarize the main actions in this video',
  'Describe the setting, mood, and camera movement',
  'List the key visual events in order',
  'Identify any on-screen text, products, or branding',
  'Create a short social-media caption based on this video'
];

const VideoAnalysisTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, errors, setErrors, results, setResults, jobStatuses, pollJobStatus } = ctx;

  const [textModels, setTextModels] = useState<ModelOption[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [modelError, setModelError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const initializedModelRef = useRef(false);

  const [form, setForm] = useState<VideoAnalysisParams>({
    video_url: '',
    question: 'Describe this video in detail',
    model: ''
  });

  useEffect(() => {
    const loadModels = async () => {
      try {
        setLoadingModels(true);
        setModelError(null);
        const response = await pollinationsApi.listTextModels();

        if (!response.success || !response.data) {
          throw new Error(response.error || 'Failed to fetch text models');
        }

        const data = response.data as unknown as TextModelsResponse;
        const models = (data.text_models || []).map((model): ModelOption => {
          let name = '';
          if (typeof model === 'string') {
            name = model;
          } else {
            const modelObj = model as ModelObject;
            name = modelObj.name || modelObj.id || modelObj.model || String(model);
          }

          const label =
            name === 'openai' ? 'OpenAI' :
            name === 'mistral' ? 'Mistral' :
            name === 'anthropic' ? 'Claude' :
            name.charAt(0).toUpperCase() + name.slice(1);

          return { name, label };
        });

        setTextModels(models.length > 0 ? models : [
          { name: 'openai', label: 'OpenAI' },
          { name: 'mistral', label: 'Mistral' },
          { name: 'anthropic', label: 'Claude' }
        ]);
      } catch (err) {
        setModelError(err instanceof Error ? err.message : 'Failed to load models');
        setTextModels([
          { name: 'openai', label: 'OpenAI' },
          { name: 'mistral', label: 'Mistral' },
          { name: 'anthropic', label: 'Claude' }
        ]);
      } finally {
        setLoadingModels(false);
      }
    };

    loadModels();
  }, []);

  useEffect(() => {
    if (textModels.length > 0 && !initializedModelRef.current) {
      setForm((prev) => ({ ...prev, model: prev.model || textModels[0].name }));
      initializedModelRef.current = true;
    }
  }, [textModels]);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [selectedFile]);

  const analysisResult = results.videoanalysis?.result;
  const isLoading = !!loading.videoanalysis;
  const error = errors.videoanalysis;
  const jobStatus = jobStatuses.videoanalysis;

  const canSubmit = useMemo(() => {
    return !!form.question.trim() && (!!form.video_url.trim() || !!selectedFile);
  }, [form.question, form.video_url, selectedFile]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('video/')) {
      setErrors((prev) => ({ ...prev, videoanalysis: 'Please select a valid video file' }));
      return;
    }

    if (file.size > MAX_VIDEO_SIZE_BYTES) {
      setErrors((prev) => ({ ...prev, videoanalysis: 'File size must be less than 25MB' }));
      return;
    }

    setSelectedFile(file);
    setErrors((prev) => ({ ...prev, videoanalysis: null }));
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      setErrors((prev) => ({ ...prev, videoanalysis: 'Provide a video URL or upload a video, plus a question' }));
      return;
    }

    setLoading((prev) => ({ ...prev, videoanalysis: true }));
    setErrors((prev) => ({ ...prev, videoanalysis: null }));
    setResults((prev) => ({ ...prev, videoanalysis: null }));

    try {
      const response = selectedFile
        ? await pollinationsApi.analyzeUploadedVideo(selectedFile, form.question, form.model)
        : await pollinationsApi.analyzeVideo({
            video_url: form.video_url,
            question: form.question,
            model: form.model
          });

      if (response.success && response.data?.job_id) {
        pollJobStatus(response.data.job_id, 'videoanalysis');
        return;
      }

      setErrors((prev) => ({ ...prev, videoanalysis: response.error || 'Failed to analyze video' }));
      setLoading((prev) => ({ ...prev, videoanalysis: false }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setErrors((prev) => ({ ...prev, videoanalysis: message }));
      setLoading((prev) => ({ ...prev, videoanalysis: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <VideoAnalysisIcon color="primary" />
              Analyze Video Content
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://example.com/video.mp4"
                  value={form.video_url}
                  onChange={(e) => setForm((prev) => ({ ...prev, video_url: e.target.value }))}
                  helperText="Public video URL, or leave blank and upload a file below"
                  sx={{ mb: 2 }}
                />

                <input
                  accept="video/*"
                  style={{ display: 'none' }}
                  id="video-analysis-upload"
                  type="file"
                  onChange={handleFileChange}
                />
                <label htmlFor="video-analysis-upload">
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
                    {selectedFile ? `Selected: ${selectedFile.name}` : 'Upload Video File'}
                  </Button>
                </label>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Max file size: 25MB
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Question"
                  placeholder="Summarize the main actions, identify on-screen text, or describe the scene"
                  value={form.question}
                  onChange={(e) => setForm((prev) => ({ ...prev, question: e.target.value }))}
                  helperText="Describe what you want extracted from the video"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>AI Model</InputLabel>
                  <Select
                    value={form.model}
                    label="AI Model"
                    onChange={(e) => setForm((prev) => ({ ...prev, model: e.target.value }))}
                    disabled={loadingModels}
                  >
                    {loadingModels ? (
                      <MenuItem disabled>Loading models...</MenuItem>
                    ) : (
                      textModels.map((model) => (
                        <MenuItem key={model.name} value={model.name}>
                          {model.label}
                        </MenuItem>
                      ))
                    )}
                  </Select>
                </FormControl>
                {modelError && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                    {modelError}
                  </Typography>
                )}
              </Grid>

              {previewUrl && (
                <Grid item xs={12}>
                  <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 2, overflow: 'hidden' }}>
                    <video
                      src={previewUrl}
                      controls
                      style={{ width: '100%', maxHeight: '260px', display: 'block' }}
                    />
                  </Box>
                </Grid>
              )}
              {selectedFile && !previewUrl && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Selected file: {selectedFile.name}
                  </Typography>
                </Grid>
              )}
              {selectedFile && form.video_url.trim() && (
                <Grid item xs={12}>
                  <Alert severity="info">
                    Uploaded file will be used. Clear it if you want to analyze the URL instead.
                  </Alert>
                </Grid>
              )}
              {error && (
                <Grid item xs={12}>
                  <Alert severity="error">{error}</Alert>
                </Grid>
              )}
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={isLoading ? <CircularProgress size={20} /> : <VideoAnalysisIcon />}
              onClick={handleSubmit}
              disabled={isLoading || !canSubmit}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {isLoading ? 'Analyzing...' : 'Analyze Video'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <VideoAnalysisIcon color="primary" fontSize="small" />
              Analysis Result
              {isLoading && <CircularProgress size={18} sx={{ ml: 1 }} />}
            </Typography>

            {isLoading && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress sx={{ mb: 1, height: 6, borderRadius: 3 }} />
                <Typography variant="body2" color="text.secondary">
                  Status: {jobStatus || 'Processing...'}
                </Typography>
              </Box>
            )}

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
            )}

            {analysisResult?.text && (
              <>
                <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
                  Video analysis completed successfully.
                </Alert>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                    Analysis Output:
                  </Typography>
                  <Box sx={{ p: 1.5, bgcolor: '#f8fafc', borderRadius: 1, maxHeight: 260, overflow: 'auto' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                      {analysisResult.text}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => navigator.clipboard.writeText(String(analysisResult.text || ''))}
                    sx={{ fontSize: '0.7rem', px: 1 }}
                  >
                    Copy
                  </Button>
                  {analysisResult.video_url && (
                    <Button
                      variant="outlined"
                      size="small"
                      href={String(analysisResult.video_url)}
                      target="_blank"
                      sx={{ fontSize: '0.7rem', px: 1 }}
                    >
                      Open Video
                    </Button>
                  )}
                </Box>
                {(analysisResult.model_used || analysisResult.generation_time) && (
                  <Box sx={{ p: 1.5, bgcolor: '#f8fafc', borderRadius: 1, fontSize: '0.7rem' }}>
                    {analysisResult.model_used && (
                      <Box sx={{ mb: 1 }}><strong>Model:</strong> {String(analysisResult.model_used)}</Box>
                    )}
                    {analysisResult.generation_time && (
                      <Box><strong>Time:</strong> {Number(analysisResult.generation_time).toFixed(1)}s</Box>
                    )}
                  </Box>
                )}
              </>
            )}

            {!isLoading && !error && !analysisResult && (
              <>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Analyze uploaded or remote videos for:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {EXAMPLE_PROMPTS.map((prompt) => (
                    <Chip
                      key={prompt}
                      label={prompt}
                      onClick={() => setForm((prev) => ({ ...prev, question: prompt }))}
                      sx={{
                        justifyContent: 'flex-start',
                        height: 'auto',
                        cursor: 'pointer',
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
  );
};

export default VideoAnalysisTab;
