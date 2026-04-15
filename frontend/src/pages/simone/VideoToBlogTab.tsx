import React, { useState } from 'react';
import {
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
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Article as BlogIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

const VideoToBlogTab: React.FC<{ ctx: TabContext }> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  // Blog form state
  const [blogForm, setBlogForm] = useState({
    url: '',
    platform: '',
    cookies_content: '',
    cookies_url: ''
  });

  const handleBlogSubmit = async () => {
    if (!blogForm.url.trim()) {
      setErrors(prev => ({ ...prev, blog: 'Video URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, blog: true }));
    setErrors(prev => ({ ...prev, blog: null }));
    setResults(prev => ({ ...prev, blog: null }));

    try {
      const payload = {
        url: blogForm.url,
        ...(blogForm.platform && { platform: blogForm.platform }),
        ...(blogForm.cookies_content && { cookies_content: blogForm.cookies_content }),
        ...(blogForm.cookies_url && { cookies_url: blogForm.cookies_url })
      };

      const response = await directApi.post('/simone/video-to-blog', payload);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'blog');
      } else {
        setErrors(prev => ({ ...prev, blog: 'Failed to create blog processing job' }));
        setLoading(prev => ({ ...prev, blog: false }));
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const errorMessage = axiosErr.response?.data?.detail || axiosErr.message || 'An error occurred';
      setErrors(prev => ({ ...prev, blog: errorMessage }));
      setLoading(prev => ({ ...prev, blog: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} md={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <BlogIcon color="primary" />
              Convert Video to Blog Post
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Video URL"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={blogForm.url}
                  onChange={(e) => setBlogForm({ ...blogForm, url: e.target.value })}
                  helperText="YouTube, TikTok, Instagram, Twitter, or direct video URL"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Social Media Platform (Optional)</InputLabel>
                  <Select
                    value={blogForm.platform}
                    label="Social Media Platform (Optional)"
                    onChange={(e) => setBlogForm({ ...blogForm, platform: e.target.value })}
                  >
                    <MenuItem value="">None</MenuItem>
                    <MenuItem value="x">X (Twitter)</MenuItem>
                    <MenuItem value="linkedin">LinkedIn</MenuItem>
                    <MenuItem value="instagram">Instagram</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Cookies URL (Optional)"
                  placeholder="https://example.com"
                  value={blogForm.cookies_url}
                  onChange={(e) => setBlogForm({ ...blogForm, cookies_url: e.target.value })}
                  helperText="For private/authenticated content"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Cookies Content (Optional)"
                  placeholder="session_token=abc123; user_id=456789"
                  value={blogForm.cookies_content}
                  onChange={(e) => setBlogForm({ ...blogForm, cookies_content: e.target.value })}
                  helperText="Authentication cookies for private content"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.blog ? <CircularProgress size={20} /> : <BlogIcon />}
              onClick={handleBlogSubmit}
              disabled={loading.blog || !blogForm.url.trim()}
              sx={{ mt: 3, px: 4, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.blog ? 'Processing...' : 'Generate Blog Post'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        {renderJobResult('blog', results.blog, <BlogIcon />) || (
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                What You'll Get
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="AI-Generated Blog Post"
                    secondary="Full article with SEO optimization"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Video Transcription"
                    secondary="Complete text transcript"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Key Screenshots"
                    secondary="AI-selected video frames"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Social Media Post"
                    secondary="Platform-optimized content"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        )}
      </Grid>
    </Grid>
  );
};

export default VideoToBlogTab;
