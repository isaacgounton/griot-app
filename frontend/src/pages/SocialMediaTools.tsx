import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  LinearProgress,
  OutlinedInput,
  InputAdornment
} from '@mui/material';
import {
  Share as ShareIcon,
  Schedule as ScheduleIcon,
  Drafts as DraftIcon,
  CloudUpload as _UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  AccessTime as TimeIcon,
  Image as ImageIcon,
  VideoFile as _VideoIcon,
  AudioFile as _AudioIcon,
  Link as _LinkIcon,
  Delete as DeleteIcon,
  Edit as _EditIcon,
  Visibility as VisibilityIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Twitter as XIcon,
  LinkedIn as LinkedInIcon,
  Facebook as FacebookIcon,
  Instagram as InstagramIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
  CalendarToday as CalendarIcon,
  Tag as TagIcon,
  AddPhotoAlternate as AddPhotoIcon,
  Publish as _PublishIcon,
  Close as CloseIcon,
  UploadFile as FileUploadIcon
} from '@mui/icons-material';
import { directApi } from '../utils/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`social-media-tabpanel-${index}`}
      aria-labelledby={`social-media-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: { xs: 1.5, sm: 2, md: 3 } }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface PostizIntegration {
  id: string;
  name: string;
  provider: string;
}

interface PostHistory {
  id: string;
  content: string;
  integrations: string[];
  post_type: string;
  status: string;
  created_at: string;
  post_id?: string;
  media_urls?: string[];
  tags?: string[];
}

const SocialMediaTools: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Postiz state
  const [integrations, setIntegrations] = useState<PostizIntegration[]>([]);
  const [loadingIntegrations, setLoadingIntegrations] = useState(false);
  
  // Post creation state
  const [postContent, setPostContent] = useState('');
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);
  const [postType, setPostType] = useState('now');
  const [scheduleDate, setScheduleDate] = useState('');
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [newMediaUrl, setNewMediaUrl] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  // File upload state
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Post history
  const [postHistory, setPostHistory] = useState<PostHistory[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load integrations on mount
  useEffect(() => {
    loadIntegrations();
    loadPostHistory();
  }, []);

  const loadIntegrations = async () => {
    setLoadingIntegrations(true);
    try {
      const response = await directApi.get('/api/v1/postiz/integrations');
      setIntegrations(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load Postiz integrations');
    } finally {
      setLoadingIntegrations(false);
    }
  };

  const loadPostHistory = async () => {
    setLoadingHistory(true);
    try {
      const response = await directApi.get('/api/v1/postiz/history');
      setPostHistory(response.data || []);
    } catch (err: any) {
      console.error('Failed to load post history:', err);
      setPostHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handlePostSubmit = async () => {
    if (!postContent.trim()) {
      setError('Please enter post content');
      return;
    }

    if (selectedIntegrations.length === 0) {
      setError('Please select at least one social media integration');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const payload: any = {
        content: postContent,
        integrations: selectedIntegrations,
        post_type: postType,
        tags: tags.length > 0 ? tags : undefined
      };

      if (mediaUrls.length > 0) {
        payload.media_urls = mediaUrls;
      }

      if (postType === 'schedule' && scheduleDate) {
        payload.schedule_date = scheduleDate;
      }

      const endpoint = postType === 'draft' 
        ? '/api/v1/postiz/create-draft'
        : postType === 'now'
        ? '/api/v1/postiz/schedule-now'
        : '/api/v1/postiz/schedule';

      await directApi.post(endpoint, payload);

      setSuccess(`Post ${postType === 'draft' ? 'created as draft' : postType === 'now' ? 'published' : 'scheduled'} successfully!`);
      
      // Reset form
      setPostContent('');
      setSelectedIntegrations([]);
      setMediaUrls([]);
      setTags([]);
      setNewMediaUrl('');
      setNewTag('');
      
      // Reload post history
      loadPostHistory();
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  const addMediaUrl = () => {
    if (newMediaUrl.trim() && !mediaUrls.includes(newMediaUrl.trim())) {
      setMediaUrls([...mediaUrls, newMediaUrl.trim()]);
      setNewMediaUrl('');
    }
  };

  const removeMediaUrl = (url: string) => {
    setMediaUrls(mediaUrls.filter(u => u !== url));
  };

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('public', 'true');

    setUploadingFile(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await directApi.post('/api/v1/postiz/upload-attachment', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        },
      });

      if (response.data.success && response.data.url) {
        console.log('Upload successful, adding URL to mediaUrls:', response.data.url);
        console.log('Current mediaUrls:', mediaUrls);
        setMediaUrls([...mediaUrls, response.data.url]);
        setSuccess(`File "${file.name}" uploaded successfully!`);
        console.log('Updated mediaUrls:', [...mediaUrls, response.data.url]);
      } else {
        console.error('Upload response invalid:', response.data);
        setError(response.data.message || 'Upload failed');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'File upload failed';
      setError(`Upload failed: ${errorMessage}`);
    } finally {
      setUploadingFile(false);
      setUploadProgress(0);
      // Reset file input
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const getPlatformIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'x':
      case 'twitter':
        return <XIcon />;
      case 'linkedin':
        return <LinkedInIcon />;
      case 'facebook':
        return <FacebookIcon />;
      case 'instagram':
        return <InstagramIcon />;
      default:
        return <ShareIcon />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'published':
        return <CheckIcon color="success" />;
      case 'scheduled':
        return <TimeIcon color="warning" />;
      case 'draft':
        return <DraftIcon color="info" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <ShareIcon />;
    }
  };

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      pb: { xs: 4, sm: 8 }
    }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 3 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            color: '#1a202c',
            fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' }
          }}
        >
          Social Media Tools 📱
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '1rem', sm: '1.1rem' }, lineHeight: 1.5 }}
        >
          Manage and schedule your social media content across multiple platforms with Postiz integration.
        </Typography>
      </Box>

      {/* Main Content */}
      <Paper elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: { xs: 2, sm: 3 } }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{
              px: { xs: 1, sm: 2, md: 3 },
              '& .MuiTab-root': {
                fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' },
                minWidth: { xs: 80, sm: 120 },
                py: { xs: 0.75, sm: 1.5 },
                px: { xs: 1, sm: 2 }
              }
            }}
          >
            <Tab icon={<ShareIcon />} label="Post Manager" />
            <Tab icon={<ScheduleIcon />} label="Post History" />
            <Tab icon={<VisibilityIcon />} label="Analytics" />
          </Tabs>
        </Box>

        <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
          {/* Alert Messages */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
              {success}
            </Alert>
          )}

          {/* Post Manager Tab */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              {/* Left Column - Post Creation */}
              <Grid item xs={12} md={8}>
                <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ShareIcon color="primary" />
                      Create New Post
                    </Typography>

                    {/* Post Content */}
                    <TextField
                      fullWidth
                      multiline
                      rows={4}
                      label="Post Content"
                      value={postContent}
                      onChange={(e) => setPostContent(e.target.value)}
                      placeholder="What would you like to share?"
                      helperText="Write your post content here. Emojis and hashtags are supported."
                      sx={{ mb: 3 }}
                    />

                    {/* Post Type Selection */}
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                          <InputLabel>Post Type</InputLabel>
                          <Select
                            value={postType}
                            label="Post Type"
                            onChange={(e) => setPostType(e.target.value)}
                          >
                            <MenuItem value="now">Post Now</MenuItem>
                            <MenuItem value="schedule">Schedule for Later</MenuItem>
                            <MenuItem value="draft">Save as Draft</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      {postType === 'schedule' && (
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            type="datetime-local"
                            label="Schedule Date"
                            value={scheduleDate}
                            onChange={(e) => setScheduleDate(e.target.value)}
                            InputLabelProps={{ shrink: true }}
                          />
                        </Grid>
                      )}
                    </Grid>

                    {/* Media Attachments */}
                    <Accordion elevation={0} sx={{ border: '1px solid #e2e8f0', mb: 3 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <AddPhotoIcon color="action" />
                          <Typography variant="subtitle1">
                            Media Attachments ({mediaUrls.length})
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                          {/* URL Input */}
                          <Grid item xs={12} md={8}>
                            <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                              Add from URL:
                            </Typography>
                            <OutlinedInput
                              fullWidth
                              placeholder="https://example.com/image.jpg"
                              value={newMediaUrl}
                              onChange={(e) => setNewMediaUrl(e.target.value)}
                              endAdornment={
                                <InputAdornment position="end">
                                  <Button
                                    onClick={addMediaUrl}
                                    disabled={!newMediaUrl.trim()}
                                    startIcon={<AddIcon />}
                                  >
                                    Add URL
                                  </Button>
                                </InputAdornment>
                              }
                            />
                          </Grid>

                          {/* File Upload */}
                          <Grid item xs={12} md={4}>
                            <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                              Upload from Computer:
                            </Typography>
                            <input
                              accept="image/*,audio/*,video/*"
                              style={{ display: 'none' }}
                              id="media-file-upload"
                              type="file"
                              onChange={handleFileUpload}
                              disabled={uploadingFile}
                            />
                            <label htmlFor="media-file-upload">
                              <Button
                                variant="outlined"
                                component="span"
                                fullWidth
                                disabled={uploadingFile}
                                startIcon={<FileUploadIcon />}
                                sx={{ height: '56px' }}
                              >
                                {uploadingFile ? `Uploading ${uploadProgress}%` : 'Choose File'}
                              </Button>
                            </label>
                          </Grid>
                        </Grid>

                        {/* Upload Progress */}
                        {uploadingFile && (
                          <Box sx={{ mb: 2 }}>
                            <LinearProgress
                              variant="determinate"
                              value={uploadProgress}
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              Uploading file... {uploadProgress}%
                            </Typography>
                          </Box>
                        )}

                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                          Supported: Images (JPG, PNG, GIF), Videos (MP4, MOV), Audio (MP3, WAV)
                        </Typography>

                        {/* Media List */}
                        {mediaUrls.length > 0 && (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {mediaUrls.map((url, index) => (
                              <Chip
                                key={index}
                                label={url.split('/').pop() || url}
                                onDelete={() => removeMediaUrl(url)}
                                deleteIcon={<DeleteIcon />}
                                color="primary"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        )}

                        {mediaUrls.length === 0 && (
                          <Alert severity="info" sx={{ mt: 2 }}>
                            No media attachments yet. Add files by uploading from your computer or providing URLs.
                          </Alert>
                        )}
                      </AccordionDetails>
                    </Accordion>

                    {/* Tags */}
                    <Accordion elevation={0} sx={{ border: '1px solid #e2e8f0', mb: 3 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <TagIcon color="action" />
                          <Typography variant="subtitle1">
                            Tags & Hashtags ({tags.length})
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                          <Grid item xs={12}>
                            <OutlinedInput
                              fullWidth
                              placeholder="Add tag (AI, marketing, social)"
                              value={newTag}
                              onChange={(e) => setNewTag(e.target.value)}
                              startAdornment={<InputAdornment position="start">#</InputAdornment>}
                              endAdornment={
                                <InputAdornment position="end">
                                  <Button 
                                    onClick={addTag} 
                                    disabled={!newTag.trim()}
                                    startIcon={<AddIcon />}
                                  >
                                    Add
                                  </Button>
                                </InputAdornment>
                              }
                            />
                          </Grid>
                        </Grid>
                        {tags.length > 0 && (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {tags.map((tag, index) => (
                              <Chip
                                key={index}
                                label={`#${tag}`}
                                onDelete={() => removeTag(tag)}
                                deleteIcon={<CloseIcon />}
                                color="secondary"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        )}
                      </AccordionDetails>
                    </Accordion>

                    {/* Submit Button */}
                    <Button
                      variant="contained"
                      size="large"
                      onClick={handlePostSubmit}
                      disabled={loading || !postContent.trim() || selectedIntegrations.length === 0}
                      startIcon={loading ? <CircularProgress size={20} /> : (postType === 'draft' ? <DraftIcon /> : postType === 'now' ? <SendIcon /> : <CalendarIcon />)}
                      fullWidth
                      sx={{ py: 1.5 }}
                    >
                      {loading ? 'Processing...' : postType === 'draft' ? 'Create Draft' : postType === 'now' ? 'Publish Now' : 'Schedule Post'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              {/* Right Column - Integrations */}
              <Grid item xs={12} md={4}>
                <Card elevation={0} sx={{ border: '1px solid #e2e8f0', mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ScheduleIcon color="primary" />
                        Connected Accounts
                      </Typography>
                      <IconButton onClick={loadIntegrations} disabled={loadingIntegrations}>
                        {loadingIntegrations ? <CircularProgress size={20} /> : <RefreshIcon />}
                      </IconButton>
                    </Box>
                    
                    {loadingIntegrations ? (
                      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                        <LinearProgress sx={{ width: '100%' }} />
                      </Box>
                    ) : integrations.length === 0 ? (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        No social media integrations found. Please connect your accounts in Postiz dashboard.
                      </Alert>
                    ) : (
                      <List dense>
                        {integrations.map((integration) => (
                          <ListItem key={integration.id} sx={{ px: 0 }}>
                            <ListItemIcon>
                              {getPlatformIcon(integration.provider)}
                            </ListItemIcon>
                            <ListItemText
                              primary={integration.name}
                              secondary={integration.provider.charAt(0).toUpperCase() + integration.provider.slice(1)}
                            />
                            <FormControlLabel
                              control={
                                <Switch
                                  checked={selectedIntegrations.includes(integration.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedIntegrations([...selectedIntegrations, integration.id]);
                                    } else {
                                      setSelectedIntegrations(selectedIntegrations.filter(id => id !== integration.id));
                                    }
                                  }}
                                />
                              }
                              label=""
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </CardContent>
                </Card>

                {/* Quick Stats */}
                <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <VisibilityIcon color="primary" />
                      Quick Stats
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                            {integrations.length}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Connected
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary" sx={{ fontWeight: 'bold' }}>
                            {selectedIntegrations.length}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Selected
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Post History Tab */}
          <TabPanel value={tabValue} index={1}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ScheduleIcon color="primary" />
                  Post History
                </Typography>
                
                {loadingHistory ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <LinearProgress sx={{ width: '50%' }} />
                  </Box>
                ) : postHistory.length === 0 ? (
                  <Alert severity="info">
                    No posts found. Create your first post to see it here.
                  </Alert>
                ) : (
                  <List>
                    {postHistory.map((post) => (
                      <Card key={post.id} elevation={0} sx={{ border: '1px solid #e2e8f0', mb: 2 }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {getStatusIcon(post.status)}
                              <Typography variant="h6">
                              {post.post_type.charAt(0).toUpperCase() + post.post_type.slice(1)} Post
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(post.created_at).toLocaleString()}
                            </Typography>
                          </Box>
                          
                          <Typography variant="body2" sx={{ mb: 2 }}>
                            {post.content}
                          </Typography>
                          
                          {post.media_urls && post.media_urls.length > 0 && (
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="caption" color="text.secondary">
                                <ImageIcon sx={{ fontSize: 16, verticalAlign: 'middle', mr: 0.5 }} />
                                Media: {post.media_urls.length} file(s)
                              </Typography>
                            </Box>
                          )}
                          
                          {post.tags && post.tags.length > 0 && (
                            <Box sx={{ mb: 2 }}>
                              {post.tags.map((tag, index) => (
                                <Chip
                                  key={index}
                                  label={`#${tag}`}
                                  size="small"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                          
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {post.integrations.map((integrationId) => {
                              const integration = integrations.find(i => i.id === integrationId);
                              return integration ? (
                                <Chip
                                  key={integrationId}
                                  icon={getPlatformIcon(integration.provider)}
                                  label={integration.name}
                                  size="small"
                                  variant="outlined"
                                />
                              ) : null;
                            })}
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </TabPanel>

          {/* Analytics Tab */}
          <TabPanel value={tabValue} index={2}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <VisibilityIcon color="primary" />
                  Social Media Analytics
                </Typography>
                <Alert severity="info">
                  Analytics features are coming soon! This will show engagement metrics, best posting times, and performance insights across all your connected platforms.
                </Alert>
              </CardContent>
            </Card>
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default SocialMediaTools;