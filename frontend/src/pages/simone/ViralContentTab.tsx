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
  FormGroup,
  Slider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  TrendingUp as ViralIcon,
  YouTube as YouTubeIcon,
  Twitter as TwitterIcon,
  LinkedIn as LinkedInIcon,
  Instagram as InstagramIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

const ViralContentTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  // Viral content form state
  const [viralForm, setViralForm] = useState({
    url: '',
    include_topics: true,
    include_x_thread: true,
    platforms: ['x', 'linkedin', 'instagram'],
    thread_config: {
      max_posts: 8,
      character_limit: 280,
      thread_style: 'viral'
    },
    cookies_content: '',
    cookies_url: ''
  });

  const handlePlatformToggle = (platform: string) => {
    setViralForm(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }));
  };

  const handleViralSubmit = async () => {
    if (!viralForm.url.trim()) {
      setErrors(prev => ({ ...prev, viral: 'Video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, viral: true }));
    setErrors(prev => ({ ...prev, viral: null }));
    setResults(prev => ({ ...prev, viral: null }));

    try {
      const payload = {
        url: viralForm.url,
        include_topics: viralForm.include_topics,
        include_x_thread: viralForm.include_x_thread,
        platforms: viralForm.platforms,
        thread_config: viralForm.thread_config,
        ...(viralForm.cookies_content && { cookies_content: viralForm.cookies_content }),
        ...(viralForm.cookies_url && { cookies_url: viralForm.cookies_url })
      };

      const response = await directApi.post('/simone/viral-content', payload);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'viral');
      } else {
        setErrors(prev => ({ ...prev, viral: 'Failed to create viral content job' }));
        setLoading(prev => ({ ...prev, viral: false }));
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const errorMessage = axiosErr.response?.data?.detail || axiosErr.message || 'An error occurred';
      setErrors(prev => ({ ...prev, viral: errorMessage }));
      setLoading(prev => ({ ...prev, viral: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} md={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <ViralIcon color="primary" />
              Viral Content Generator
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={viralForm.url}
                  onChange={(e) => setViralForm({ ...viralForm, url: e.target.value })}
                  helperText="YouTube, TikTok, Instagram, Twitter, or direct video URL"
                />
              </Grid>

              {/* Platform Selection */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Target Platforms:
                </Typography>
                <FormGroup row sx={{ flexDirection: { xs: 'column', sm: 'row' } }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viralForm.platforms.includes('x')}
                        onChange={() => handlePlatformToggle('x')}
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TwitterIcon fontSize="small" />
                        X (Twitter)
                      </Box>
                    }
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viralForm.platforms.includes('linkedin')}
                        onChange={() => handlePlatformToggle('linkedin')}
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinkedInIcon fontSize="small" />
                        LinkedIn
                      </Box>
                    }
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viralForm.platforms.includes('instagram')}
                        onChange={() => handlePlatformToggle('instagram')}
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <InstagramIcon fontSize="small" />
                        Instagram
                      </Box>
                    }
                  />
                </FormGroup>
              </Grid>

              {/* Content Options */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Content Options:
                </Typography>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viralForm.include_topics}
                        onChange={(e) => setViralForm({ ...viralForm, include_topics: e.target.checked })}
                      />
                    }
                    label="Include Topic Identification"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viralForm.include_x_thread}
                        onChange={(e) => setViralForm({ ...viralForm, include_x_thread: e.target.checked })}
                      />
                    }
                    label="Generate X Thread"
                  />
                </FormGroup>
              </Grid>

              {/* Thread Configuration */}
              {viralForm.include_x_thread && (
                <Grid item xs={12}>
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="h6">Thread Configuration</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={4}>
                          <Typography gutterBottom>Max Posts: {viralForm.thread_config.max_posts}</Typography>
                          <Slider
                            value={viralForm.thread_config.max_posts}
                            onChange={(_e, value) => setViralForm({
                              ...viralForm,
                              thread_config: {
                                ...viralForm.thread_config,
                                max_posts: Array.isArray(value) ? value[0] : value
                              }
                            })}
                            min={5}
                            max={20}
                            step={1}
                            marks={[
                              { value: 5, label: '5' },
                              { value: 10, label: '10' },
                              { value: 15, label: '15' },
                              { value: 20, label: '20' }
                            ]}
                          />
                        </Grid>

                        <Grid item xs={12} sm={6} md={4}>
                          <Typography gutterBottom>Character Limit: {viralForm.thread_config.character_limit}</Typography>
                          <Slider
                            value={viralForm.thread_config.character_limit}
                            onChange={(_e, value) => setViralForm({
                              ...viralForm,
                              thread_config: {
                                ...viralForm.thread_config,
                                character_limit: Array.isArray(value) ? value[0] : value
                              }
                            })}
                            min={200}
                            max={400}
                            step={20}
                            marks={[
                              { value: 200, label: '200' },
                              { value: 280, label: '280' },
                              { value: 400, label: '400' }
                            ]}
                          />
                        </Grid>

                        <Grid item xs={12} sm={6} md={4}>
                          <FormControl fullWidth>
                            <InputLabel>Thread Style</InputLabel>
                            <Select
                              value={viralForm.thread_config.thread_style}
                              label="Thread Style"
                              onChange={(e) => setViralForm({
                                ...viralForm,
                                thread_config: {
                                  ...viralForm.thread_config,
                                  thread_style: e.target.value
                                }
                              })}
                            >
                              <MenuItem value="viral">Viral</MenuItem>
                              <MenuItem value="professional">Professional</MenuItem>
                              <MenuItem value="casual">Casual</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                </Grid>
              )}

              {/* Authentication (Optional) */}
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Authentication (Optional)</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Cookies URL"
                          placeholder="https://example.com"
                          value={viralForm.cookies_url}
                          onChange={(e) => setViralForm({ ...viralForm, cookies_url: e.target.value })}
                          helperText="For private/authenticated content"
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={2}
                          label="Cookies Content"
                          placeholder="session_token=abc123; user_id=456789"
                          value={viralForm.cookies_content}
                          onChange={(e) => setViralForm({ ...viralForm, cookies_content: e.target.value })}
                          helperText="Authentication cookies for private content"
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
              startIcon={loading.viral ? <CircularProgress size={20} /> : <ViralIcon />}
              onClick={handleViralSubmit}
              disabled={loading.viral || !viralForm.url.trim() || viralForm.platforms.length === 0}
              sx={{ mt: 3, px: 4, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.viral ? 'Processing...' : 'Generate Viral Content'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        {renderJobResult('viral', results.viral, <ViralIcon />) || (
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Enhanced Features
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Multi-Platform Content"
                    secondary="X, LinkedIn, Instagram posts"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Viral X Threads"
                    secondary="Engagement-optimized threads"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Topic Analysis"
                    secondary="AI-identified themes & subjects"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Complete Package"
                    secondary="Blog + Screenshots + Transcripts"
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Supported Platforms:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                <Chip icon={<YouTubeIcon />} label="YouTube" size="small" variant="outlined" />
                <Chip icon={<TwitterIcon />} label="Twitter" size="small" variant="outlined" />
                <Chip icon={<InstagramIcon />} label="Instagram" size="small" variant="outlined" />
                <Chip label="TikTok" size="small" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        )}
      </Grid>
    </Grid>
  );
};

export default ViralContentTab;
