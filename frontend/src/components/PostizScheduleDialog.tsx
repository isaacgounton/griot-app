import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
  Alert,
  Grid,
  Card,
  CardContent,
  Checkbox,
  ListItemText,
  OutlinedInput,
  IconButton,
  InputAdornment,
  SelectChangeEvent,
  CircularProgress
} from '@mui/material';
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Job } from '../types/griot';
import { AutoAwesome as AIIcon } from '@mui/icons-material';

interface PostizIntegration {
  id: string;
  name: string;
  provider: string;
}

interface JobResult {
  scheduling?: {
    suggested_content?: string;
  };
  final_video_url?: string;
  video_url?: string;
  image_url?: string;
  audio_url?: string;
  script_generated?: string;
  topic_used?: string;
}

interface PostizScheduleDialogProps {
  open: boolean;
  onClose: () => void;
  job: Job | null;
  // eslint-disable-next-line no-unused-vars
  onSchedule: (data: ScheduleData) => Promise<void>;
}

interface ScheduleData {
  jobId: string;
  content: string;
  integrations: string[];
  postType: 'now' | 'schedule' | 'draft';
  scheduleDate?: Date;
  tags: string[];
}

export const PostizScheduleDialog: React.FC<PostizScheduleDialogProps> = ({
  open,
  onClose,
  job,
  onSchedule
}) => {
  const [integrations, setIntegrations] = useState<PostizIntegration[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<{
    content: string;
    selectedIntegrations: string[];
    postType: 'now' | 'schedule' | 'draft';
    scheduleDate: Date | null;
    tags: string[];
    customTagInput: string;
  }>({
    content: '',
    selectedIntegrations: [],
    postType: 'now',
    scheduleDate: null,
    tags: [],
    customTagInput: ''
  });

  const [generating, setGenerating] = useState(false);

  // Load integrations when dialog opens
  useEffect(() => {
    if (open && integrations.length === 0) {
      loadIntegrations();
    }
  }, [open, integrations.length]);

  // Load suggested content when job changes
  useEffect(() => {
    if (job && open) {
      let suggestedContent = '';

      // Get suggested content from job scheduling metadata
      if (job.result && typeof job.result === 'object' && 'scheduling' in job.result) {
        const scheduling = (job.result as JobResult).scheduling;
        suggestedContent = scheduling?.suggested_content || '';
      }

      // Fallback to basic content
      if (!suggestedContent) {
        const operationType = job.operation || 'video creation';
        const result = job.result as JobResult;
        const hasVideo = result?.final_video_url || result?.video_url;
        const scriptGenerated = result?.script_generated;
        const topicUsed = result?.topic_used;

        if (hasVideo && scriptGenerated) {
          // Extract first sentence or key topic from script for more relevant content
          const scriptPreview = scriptGenerated.split('.')[0].substring(0, 100);
          const topic = topicUsed || 'amazing content';

          suggestedContent = `🎬 Just created an AI-generated video about ${topic}! ✨

"${scriptPreview}${scriptPreview.length >= 100 ? '...' : '.'}"

Created with automated script generation and video production.

#AI #VideoCreation #Automation #ContentCreation #DigitalStorytelling`;
        } else if (hasVideo) {
          suggestedContent = `🎬 New video content created with AI! Automated video production at its finest. #AI #VideoCreation #Automation #DigitalContent`;
        } else {
          suggestedContent = `✨ Just completed an amazing ${operationType} project using AI automation! #AI #Automation #Creation #Technology`;
        }
      }

      setFormData(prev => ({
        ...prev,
        content: suggestedContent,
        tags: ['AI', 'automation', 'creation']
      }));
    }
  }, [job, open]);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);

      const apiKey = localStorage.getItem('griot_api_key');
      if (!apiKey) {
        throw new Error('API key not found');
      }

      const response = await fetch('/api/v1/postiz/integrations', {
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setIntegrations(data);
    } catch (error: unknown) {
      console.error('Failed to load integrations:', error);
      let errorMessage = 'Failed to load integrations';

      if (error instanceof Error) {
        if (error.message.includes('API key not found')) {
          errorMessage = 'API key not found. Please check your browser storage.';
        } else if (error.message.includes('Invalid Postiz API key')) {
          errorMessage = 'Invalid Postiz API key. Please check your POSTIZ_API_KEY environment variable.';
        } else if (error.message.includes('Failed to connect')) {
          errorMessage = 'Cannot connect to Postiz API. Please check your POSTIZ_API_URL configuration.';
        } else {
          errorMessage = `Failed to load integrations: ${error.message}`;
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleIntegrationChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      selectedIntegrations: typeof value === 'string' ? value.split(',') : value
    }));
  };

  const handleAddTag = () => {
    const tag = formData.customTagInput.trim();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag],
        customTagInput: ''
      }));
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSchedule = async () => {
    // Check for job and job ID (handle both id and job_id fields)
    const jobId = job?.id || job?.job_id;
    if (!job || !jobId) {
      setError('No job found or job ID missing');
      return;
    }

    if (formData.selectedIntegrations.length === 0) {
      setError('Please select at least one social media platform');
      return;
    }

    if (formData.postType === 'schedule' && !formData.scheduleDate) {
      setError('Please select a schedule date for scheduled posts');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const scheduleData: ScheduleData = {
        jobId: jobId,
        content: formData.content,
        integrations: formData.selectedIntegrations,
        postType: formData.postType,
        scheduleDate: formData.scheduleDate || undefined,
        tags: formData.tags
      };

      await onSchedule(scheduleData);
      onClose();
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to schedule post';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateContent = async () => {
    if (!job) return;

    try {
      setGenerating(true);
      setError(null);

      const apiKey = localStorage.getItem('griot_api_key');
      if (!apiKey) {
        throw new Error('API key not found');
      }

      const jobId = job.id || job.job_id;
      const response = await fetch('/api/v1/postiz/generate-content', {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          job_id: jobId,
          user_instructions: formData.content || undefined,
          content_style: 'engaging',
          platform: 'general'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update content and tags with generated data
      setFormData(prev => ({
        ...prev,
        content: data.content,
        // Merge generated tags with existing tags, removing duplicates
        tags: Array.from(new Set([...prev.tags, ...(data.tags || [])]))
      }));

    } catch (error: unknown) {
      console.error('Failed to generate content:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate content';
      setError(errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  const handleClose = () => {
    setFormData({
      content: '',
      selectedIntegrations: [],
      postType: 'now',
      scheduleDate: null,
      tags: [],
      customTagInput: ''
    });
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Schedule to Social Media</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {job && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job: {job.operation}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ID: {job.id || job.job_id}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Status: {job.status}
              </Typography>
              {job.result && typeof job.result === 'object' && (() => {
                const result = job.result as JobResult;
                return (
                  <>
                    {(result.video_url || result.final_video_url) && (
                      <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                        📹 Contains video content - will be uploaded to social media
                      </Typography>
                    )}
                    {!(result.video_url || result.final_video_url) && result.image_url && (
                      <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                        🖼️ Contains image content - will be uploaded to social media
                      </Typography>
                    )}
                    {!(result.video_url || result.final_video_url) && !result.image_url && result.audio_url && (
                      <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                        🎵 Contains audio content - URL will be included in post
                      </Typography>
                    )}
                  </>
                );
              })()}
            </CardContent>
          </Card>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Post Content"
              value={formData.content}
              onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
              placeholder="Enter your instructions for AI content generation (e.g., 'Create an engaging post about AI video creation with emojis')..."
              disabled={generating}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end" sx={{ alignSelf: 'flex-start', mt: 2 }}>
                    <IconButton
                      onClick={handleGenerateContent}
                      disabled={generating || !job || !formData.content.trim()}
                      edge="end"
                      sx={{
                        bgcolor: generating ? 'action.disabledBackground' : 'primary.main',
                        color: 'white',
                        '&:hover': {
                          bgcolor: generating ? 'action.disabledBackground' : 'primary.dark',
                        },
                        '&:disabled': {
                          bgcolor: 'action.disabledBackground',
                          color: 'text.disabled',
                        },
                      }}
                      title="Generate AI content from your instructions"
                    >
                      {generating ? <CircularProgress size={20} color="inherit" /> : <AIIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Type your instructions and click the ✨ button to generate content, or write your post directly.
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Social Media Platforms</InputLabel>
              <Select
                multiple
                value={formData.selectedIntegrations}
                onChange={handleIntegrationChange}
                input={<OutlinedInput label="Social Media Platforms" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const integration = integrations.find(i => i.id === value);
                      return (
                        <Chip
                          key={value}
                          label={integration ? `${integration.name} (${integration.provider})` : value}
                          size="small"
                        />
                      );
                    })}
                  </Box>
                )}
              >
                {integrations.map((integration) => (
                  <MenuItem key={integration.id} value={integration.id}>
                    <Checkbox checked={formData.selectedIntegrations.indexOf(integration.id) > -1} />
                    <ListItemText primary={`${integration.name} (${integration.provider})`} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Post Type</InputLabel>
              <Select
                value={formData.postType}
                label="Post Type"
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  postType: e.target.value as 'now' | 'schedule' | 'draft'
                }))}
              >
                <MenuItem value="now">Publish Now</MenuItem>
                <MenuItem value="schedule">Schedule for Later</MenuItem>
                <MenuItem value="draft">Save as Draft</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {formData.postType === 'schedule' && (
            <Grid item xs={12}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="Schedule Date & Time"
                  value={formData.scheduleDate}
                  onChange={(newValue) => setFormData(prev => ({ ...prev, scheduleDate: newValue }))}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      required: true
                    }
                  }}
                  minDateTime={new Date()}
                />
              </LocalizationProvider>
            </Grid>
          )}

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Tags
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {formData.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={`#${tag}`}
                  onDelete={() => handleRemoveTag(tag)}
                  size="small"
                />
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                size="small"
                label="Add Tag"
                value={formData.customTagInput}
                onChange={(e) => setFormData(prev => ({ ...prev, customTagInput: e.target.value }))}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button onClick={handleAddTag} variant="outlined" size="small">
                Add
              </Button>
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSchedule}
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Scheduling...' :
            formData.postType === 'now' ? 'Publish Now' :
              formData.postType === 'schedule' ? 'Schedule Post' : 'Save Draft'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};