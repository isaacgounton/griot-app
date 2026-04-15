import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Paper,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Tabs,
  Tab
} from '@mui/material';
import {
  Article as BlogIcon,
  TrendingUp as ViralIcon,
  YouTube as YouTubeIcon,
  Twitter as TwitterIcon,
  LinkedIn as LinkedInIcon,
  Instagram as InstagramIcon,
  Topic as TopicIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Image as ImageIcon,
  Subtitles as TranscriptIcon,
  Share as ShareIcon,
  Schedule as ScheduleIcon,
  VideoFile as VideoIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { PostizScheduleDialog } from '../../components/PostizScheduleDialog';
import { JobStatus } from '../../types/griot';
import { TabPanelProps, JobResult, TabContext, SelectedJobForScheduling } from './types';

import VideoToBlogTab from './VideoToBlogTab';
import ViralContentTab from './ViralContentTab';
import YouTubeShortsTab from './YouTubeShortsTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simone-tabpanel-${index}`}
      aria-labelledby={`simone-tab-${index}`}
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

const Simone: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, JobResult | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({});

  // Postiz integration
  const [postizDialogOpen, setPostizDialogOpen] = useState(false);
  const [selectedJobForScheduling, setSelectedJobForScheduling] = useState<SelectedJobForScheduling | null>(null);

  // Generic job polling function
  const pollJobStatus = async (jobId: string, toolName: string) => {
    const maxAttempts = 120; // 10 minutes max for video processing
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const statusResponse = await directApi.get(`/jobs/${jobId}/status`);

        // Handle the unified jobs endpoint response format
        const jobData = statusResponse.data.data || statusResponse.data;
        const status = jobData.status;
        const jobResult = jobData.result;
        const jobError = jobData.error;

        setJobStatuses(prev => ({ ...prev, [toolName]: status }));

        if (status === 'completed') {
          setResults(prev => ({ ...prev, [toolName]: { job_id: jobId, result: jobResult, status: 'completed' } }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
          return;
        } else if (status === 'failed') {
          setErrors(prev => ({ ...prev, [toolName]: jobError || 'Job failed' }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setErrors(prev => ({ ...prev, [toolName]: 'Job polling timeout' }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
        }
      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setErrors(prev => ({ ...prev, [toolName]: 'Failed to check job status' }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
        }
      }
    };

    poll();
  };

  // Postiz scheduling handlers
  const generateSuggestedContent = (toolName: string, result: JobResult): string => {
    if (toolName === 'viral' && result.result?.viral_content_package?.content.posts) {
      // Use the generated X (Twitter) post if available
      const xPost = result.result.viral_content_package.content.posts.x;
      if (xPost) {
        return xPost;
      }
    }

    if (result.result?.social_media_post_content) {
      return result.result.social_media_post_content;
    }

    // Fallback content per tab
    if (toolName === 'shorts') {
      const title = result.result?.original_title || 'a video';
      return `\uD83C\uDFAC Just created a YouTube Short from "${title}" using AI-powered highlight detection! #YouTubeShorts #AI #ContentCreation #VideoEditing`;
    } else if (toolName === 'viral') {
      return `\uD83E\uDD16 Just generated amazing viral content with Simone AI! Multi-platform social media posts, X threads, and blog content all from a single video. #AI #ContentCreation #ViralMarketing #Automation`;
    } else {
      return `\uD83D\uDCDD Just converted a video into a comprehensive blog post using Simone AI! Complete with transcription, screenshots, and social media content. #AI #ContentCreation #BlogPost #Automation`;
    }
  };

  const handleScheduleClick = (toolName: string, result: JobResult) => {
    const operationNames: Record<string, string> = {
      blog: 'Video to Blog',
      viral: 'Viral Content Generation',
      shorts: 'YouTube Shorts'
    };

    // For shorts, map `url` to `video_url` so PostizScheduleDialog detects video content
    const resultData = { ...result.result };
    if (toolName === 'shorts' && resultData?.url && !resultData?.video_url) {
      (resultData as Record<string, unknown>).video_url = resultData.url;
    }

    // Create a job object compatible with PostizScheduleDialog
    const jobForScheduling: SelectedJobForScheduling = {
      id: result.job_id,
      job_id: result.job_id,
      operation: operationNames[toolName] || toolName,
      status: JobStatus.COMPLETED,
      result: {
        scheduling: {
          available: true,
          content_type: toolName === 'shorts' ? 'video' : 'text',
          suggested_content: generateSuggestedContent(toolName, result)
        },
        ...resultData
      }
    };

    setSelectedJobForScheduling(jobForScheduling);
    setPostizDialogOpen(true);
  };

  const handlePostizSchedule = async (scheduleData: {
    jobId: string;
    content: string;
    integrations: string[];
    postType: string;
    scheduleDate?: Date;
    tags: string[];
  }) => {
    try {
      await directApi.post('/postiz/schedule-job', {
        job_id: scheduleData.jobId,
        content: scheduleData.content,
        integrations: scheduleData.integrations,
        post_type: scheduleData.postType,
        schedule_date: scheduleData.scheduleDate,
        tags: scheduleData.tags
      });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      throw new Error(axiosErr.response?.data?.detail || 'Failed to schedule post');
    }
  };

  const renderJobResult = (toolName: string, result: JobResult | null, icon: React.ReactNode) => {
    if (!result && !loading[toolName] && !errors[toolName]) return null;

    return (
      <Card elevation={0} sx={{ border: '1px solid #e2e8f0', mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            {icon}
            {toolName === 'blog' ? 'Blog Processing' : toolName === 'viral' ? 'Viral Content' : 'YouTube Shorts'} Result
            {loading[toolName] && <CircularProgress size={20} sx={{ ml: 1 }} />}
          </Typography>

          {loading[toolName] && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress sx={{ mb: 1, height: 6, borderRadius: 3 }} />
              <Typography variant="body2" color="text.secondary">
                Status: {jobStatuses[toolName] || 'Processing...'}
              </Typography>
            </Box>
          )}

          {errors[toolName] && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {errors[toolName]}
            </Alert>
          )}

          {result && jobStatuses[toolName] === 'completed' && result.result && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                {'\uD83C\uDF89'} Content generated successfully!
              </Alert>

              {/* Schedule to Postiz Button */}
              <Box sx={{ mb: 2 }}>
                <Button
                  startIcon={<ScheduleIcon />}
                  onClick={() => handleScheduleClick(toolName, result)}
                  variant="contained"
                  color="secondary"
                  size="medium"
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                >
                  Schedule to Social Media
                </Button>
              </Box>

              {/* Blog Post Content */}
              {result.result.blog_post_content && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <BlogIcon /> Blog Post Content
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: 400, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {result.result.blog_post_content.substring(0, 1000)}
                        {result.result.blog_post_content.length > 1000 && '...'}
                      </Typography>
                    </Paper>
                    {result.result.blog_post_url && (
                      <Button
                        startIcon={<DownloadIcon />}
                        href={result.result.blog_post_url.startsWith('http') ? result.result.blog_post_url : `${window.location.origin}${result.result.blog_post_url}`}
                        target="_blank"
                        variant="outlined"
                        size="small"
                        sx={{ mt: 1 }}
                      >
                        Download Full Blog Post
                      </Button>
                    )}
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Social Media Posts */}
              {(result.result.social_media_post_content || result.result.viral_content_package?.content.posts) && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ShareIcon /> Social Media Posts
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {result.result.social_media_post_content && (
                      <Paper sx={{ p: 2, bgcolor: '#f8fafc', mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                          Generated Post:
                        </Typography>
                        <Typography variant="body2">{result.result.social_media_post_content}</Typography>
                      </Paper>
                    )}

                    {result.result.viral_content_package?.content.posts && (
                      <Grid container spacing={2}>
                        {Object.entries(result.result.viral_content_package.content.posts).map(([platform, content]) => (
                          <Grid item xs={12} md={6} key={platform}>
                            <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  {platform === 'x' && <TwitterIcon fontSize="small" />}
                                  {platform === 'linkedin' && <LinkedInIcon fontSize="small" />}
                                  {platform === 'instagram' && <InstagramIcon fontSize="small" />}
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                                    {platform === 'x' ? 'X (Twitter)' : platform}
                                  </Typography>
                                </Box>
                                <Button
                                  size="small"
                                  startIcon={<ScheduleIcon />}
                                  onClick={() => {
                                    const platformResult = { ...result, result: { ...result.result, social_media_post_content: content } };
                                    handleScheduleClick(toolName, platformResult);
                                  }}
                                  variant="outlined"
                                >
                                  Schedule
                                </Button>
                              </Box>
                              <Typography variant="body2">{content}</Typography>
                            </Paper>
                          </Grid>
                        ))}
                      </Grid>
                    )}
                  </AccordionDetails>
                </Accordion>
              )}

              {/* X Thread */}
              {result.result.viral_content_package?.content.x_thread?.thread && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TwitterIcon /> X Thread ({result.result.viral_content_package.content.x_thread.thread.length} posts)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                      {result.result.viral_content_package.content.x_thread.thread.map((post, index) => (
                        <Paper key={index} sx={{ p: 2, mb: 1, bgcolor: index % 2 === 0 ? '#f8fafc' : '#ffffff' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="caption" sx={{ fontWeight: 600 }}>
                              Post {post.post_number || index + 1}
                            </Typography>
                            {post.character_count && (
                              <Typography variant="caption" color="text.secondary">
                                {post.character_count} chars
                              </Typography>
                            )}
                          </Box>
                          <Typography variant="body2">{post.content}</Typography>
                        </Paper>
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Topics */}
              {result.result.viral_content_package?.content.topics && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TopicIcon /> Identified Topics ({result.result.viral_content_package.content.topics.topics?.length || 0})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {(result.result.viral_content_package.content.topics.topics || []).map((topic, index) => (
                        <Grid item xs={12} md={6} key={index}>
                          <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {topic.topic}
                              </Typography>
                              {topic.confidence && (
                                <Chip
                                  label={`${(topic.confidence * 100).toFixed(0)}%`}
                                  size="small"
                                  color="primary"
                                />
                              )}
                            </Box>
                            {topic.key_points && (
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {topic.key_points.map((point, pointIndex) => (
                                  <Chip key={pointIndex} label={point} size="small" variant="outlined" />
                                ))}
                              </Box>
                            )}
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Screenshots */}
              {result.result.screenshots && result.result.screenshots.length > 0 && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ImageIcon /> Screenshots ({result.result.screenshots.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {result.result.screenshots.map((screenshot, index) => {
                        // Handle both S3 URLs and local paths
                        const imageUrl = screenshot.startsWith('http') ? screenshot : `${window.location.origin}${screenshot}`;
                        return (
                          <Grid item xs={12} md={4} key={index}>
                            <Card variant="outlined">
                              <img
                                src={imageUrl}
                                alt={`Screenshot ${index + 1}`}
                                style={{
                                  width: '100%',
                                  height: 150,
                                  objectFit: 'cover'
                                }}
                                onError={(e) => {
                                  console.error('Failed to load image:', imageUrl);
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                              <CardContent sx={{ p: 1 }}>
                                <Button
                                  fullWidth
                                  size="small"
                                  startIcon={<DownloadIcon />}
                                  href={imageUrl}
                                  target="_blank"
                                >
                                  Download
                                </Button>
                              </CardContent>
                            </Card>
                          </Grid>
                        );
                      })}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Transcription */}
              {result.result.transcription_content && (
                <Accordion sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TranscriptIcon /> Transcription
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: 300, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {result.result.transcription_content.substring(0, 2000)}
                        {result.result.transcription_content.length > 2000 && '...'}
                      </Typography>
                    </Paper>
                    {result.result.transcription_url && (
                      <Button
                        startIcon={<DownloadIcon />}
                        href={result.result.transcription_url.startsWith('http') ? result.result.transcription_url : `${window.location.origin}${result.result.transcription_url}`}
                        target="_blank"
                        variant="outlined"
                        size="small"
                        sx={{ mt: 1 }}
                      >
                        Download Full Transcription
                      </Button>
                    )}
                  </AccordionDetails>
                </Accordion>
              )}

              {/* YouTube Shorts Video Result */}
              {result.result.url && toolName === 'shorts' && (
                <Accordion defaultExpanded sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <VideoIcon /> Generated Short
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                      <video
                        controls
                        style={{
                          maxWidth: '100%',
                          maxHeight: 500,
                          borderRadius: 8,
                          backgroundColor: '#000'
                        }}
                        src={result.result.url}
                      />
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                        <Button
                          startIcon={<DownloadIcon />}
                          href={result.result.url}
                          target="_blank"
                          variant="contained"
                          size="medium"
                        >
                          Download Short
                        </Button>
                      </Box>

                      {/* Video Details */}
                      <Paper sx={{ p: 2, bgcolor: '#f8fafc', width: '100%' }}>
                        <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                          {result.result.original_title && (
                            <Grid item xs={12}>
                              <strong>Original:</strong> {result.result.original_title}
                            </Grid>
                          )}
                          {result.result.duration != null && (
                            <Grid item xs={6} md={3}>
                              <strong>Duration:</strong> {Math.round(result.result.duration)}s
                            </Grid>
                          )}
                          {result.result.original_duration != null && (
                            <Grid item xs={6} md={3}>
                              <strong>Original:</strong> {Math.round(result.result.original_duration)}s
                            </Grid>
                          )}
                          {result.result.highlight_start != null && result.result.highlight_end != null && (
                            <Grid item xs={6} md={3}>
                              <strong>Segment:</strong> {Math.round(result.result.highlight_start)}s - {Math.round(result.result.highlight_end)}s
                            </Grid>
                          )}
                          {result.result.quality && (
                            <Grid item xs={6} md={3}>
                              <strong>Quality:</strong> {result.result.quality}
                            </Grid>
                          )}
                        </Grid>
                      </Paper>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Processing Summary */}
              {result.result.processing_summary && (
                <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>{'\uD83D\uDCCA'} Processing Summary:</Typography>
                  <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                    {result.result.processing_summary.total_topics && (
                      <Grid item xs={6} md={3}>
                        <strong>Topics:</strong> {result.result.processing_summary.total_topics}
                      </Grid>
                    )}
                    {result.result.processing_summary.thread_posts && (
                      <Grid item xs={6} md={3}>
                        <strong>Thread Posts:</strong> {result.result.processing_summary.thread_posts}
                      </Grid>
                    )}
                    {result.result.processing_summary.screenshots_count && (
                      <Grid item xs={6} md={3}>
                        <strong>Screenshots:</strong> {result.result.processing_summary.screenshots_count}
                      </Grid>
                    )}
                    {result.result.processing_summary.platforms_generated && (
                      <Grid item xs={6} md={3}>
                        <strong>Platforms:</strong> {result.result.processing_summary.platforms_generated.join(', ')}
                      </Grid>
                    )}
                  </Grid>
                </Paper>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  const ctx: TabContext = {
    loading, setLoading,
    errors, setErrors,
    results, setResults,
    jobStatuses,
    pollJobStatus,
    renderJobResult,
    handleScheduleClick
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
          Simone AI {'\uD83E\uDD16'}
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '1rem', sm: '1.1rem' }, lineHeight: 1.5 }}
        >
          Transform videos into blog posts, social media content, viral threads, and YouTube Shorts using AI.
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
            <Tab icon={<BlogIcon />} label="Video to Blog" iconPosition="start" sx={{ textTransform: 'none' }} />
            <Tab icon={<ViralIcon />} label="Viral Content" iconPosition="start" sx={{ textTransform: 'none' }} />
            <Tab icon={<YouTubeIcon />} label="YouTube Shorts" iconPosition="start" sx={{ textTransform: 'none' }} />
          </Tabs>
        </Box>

        <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
          <TabPanel value={tabValue} index={0}>
            <VideoToBlogTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <ViralContentTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <YouTubeShortsTab ctx={ctx} />
          </TabPanel>
        </Box>
      </Paper>

      {/* Postiz Schedule Dialog */}
      <PostizScheduleDialog
        open={postizDialogOpen}
        onClose={() => setPostizDialogOpen(false)}
        job={selectedJobForScheduling}
        onSchedule={handlePostizSchedule}
      />
    </Box>
  );
};

export default Simone;
