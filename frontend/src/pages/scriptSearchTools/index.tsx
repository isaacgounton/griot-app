import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Paper,
  LinearProgress,
  Tabs,
  Tab,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  Divider
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  Search as SearchIcon,
  Newspaper as NewsIcon,
  Download as DownloadIcon,
  PlayArrow as PlayIcon,
  ContentCopy as CopyIcon,
  ImageSearch as ImageSearchIcon,
  Article as ArticleIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabPanelProps, JobResult, TabContext } from './types';

import ScriptGeneratorTab from './ScriptGeneratorTab';
import VideoSearchTab from './VideoSearchTab';
import NewsResearchTab from './NewsResearchTab';
import WebSearchTab from './WebSearchTab';
import StockImagesTab from './StockImagesTab';
import ArticleToScriptTab from './ArticleToScriptTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-tools-tabpanel-${index}`}
      aria-labelledby={`ai-tools-tab-${index}`}
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

const ScriptSearchTools: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, JobResult | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({});

  // Generic job polling function
  const pollJobStatus = async (jobId: string, toolName: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        // Use the standard jobs status endpoint: /api/v1/jobs/{jobId}/status
        const statusResponse = await directApi.get(`/jobs/${jobId}/status`);

        const status = statusResponse.data.data?.status || statusResponse.data.status;
        const jobResult = statusResponse.data.data?.result || statusResponse.data.result;
        const jobError = statusResponse.data.data?.error || statusResponse.data.error;

        setJobStatuses(prev => ({ ...prev, [toolName]: `${status} (${attempts}/${maxAttempts})` }));

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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const renderJobResult = (toolName: string, result: JobResult | null, icon: React.ReactNode) => {
    if (!result && !loading[toolName] && !errors[toolName]) return null;

    return (
      <Card elevation={0} sx={{ border: '1px solid #e2e8f0', mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            {icon}
            {toolName.charAt(0).toUpperCase() + toolName.slice(1)} Result
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

          {result && result.result && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                {toolName.charAt(0).toUpperCase() + toolName.slice(1)} completed successfully!
              </Alert>

              {/* Script Content */}
              {(result.result.script || result.result.script_content) && (
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Generated Script
                    </Typography>
                    <Button
                      startIcon={<CopyIcon />}
                      onClick={() => copyToClipboard(result.result?.script || result.result?.script_content || '')}
                      variant="outlined"
                      size="small"
                    >
                      Copy Script
                    </Button>
                  </Box>

                  <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: 400, overflow: 'auto' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.result.script || result.result.script_content}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {/* Search Queries - AI Generated */}
              {result.result?.queries && Array.isArray(result.result.queries) && result.result.queries.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    AI-Generated Search Queries ({result.result.queries.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {result.result.queries.map((queryObj, index) => (
                      <Card key={index} elevation={1} sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                              "{queryObj.query}"
                            </Typography>
                            {queryObj.visual_concept && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {queryObj.visual_concept}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              Duration: {queryObj.duration}s ({queryObj.start_time}s - {queryObj.end_time}s)
                            </Typography>
                          </Box>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => copyToClipboard(queryObj.query)}
                            sx={{ ml: 2 }}
                          >
                            Copy
                          </Button>
                        </Box>
                      </Card>
                    ))}
                  </Box>
                  {result.result?.total_duration && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                      Total Duration: {result.result.total_duration}s - {result.result?.total_segments || 0} segments
                    </Typography>
                  )}
                </Box>
              )}

              {/* Legacy Search Queries (fallback) */}
              {result.result?.search_queries && Array.isArray(result.result.search_queries) && result.result.search_queries.length > 0 && !result.result?.queries && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    AI-Generated Search Queries
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {result.result.search_queries.map((query, index) => (
                      <Chip
                        key={index}
                        label={query}
                        variant="outlined"
                        onClick={() => copyToClipboard(query)}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Video Results */}
              {result.result?.videos && Array.isArray(result.result.videos) && result.result.videos.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Found Videos ({result.result.videos.length})
                  </Typography>

                  {/* Video Search Details */}
                  <Box sx={{ mb: 2, p: 2, bgcolor: '#f8f9fa', borderRadius: 1 }}>
                    <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                      {result.result?.query_used && typeof result.result.query_used === 'string' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Search Query:</strong> {result.result.query_used}
                        </Grid>
                      )}
                      {result.result?.provider_used && typeof result.result.provider_used === 'string' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Provider:</strong> {result.result.provider_used.charAt(0).toUpperCase() + result.result.provider_used.slice(1)}
                        </Grid>
                      )}
                      {result.result?.total_results && typeof result.result.total_results === 'number' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Total Available:</strong> {result.result.total_results.toLocaleString()} videos
                        </Grid>
                      )}
                      {result.result?.page && result.result?.per_page && typeof result.result.page === 'number' && typeof result.result.per_page === 'number' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Page:</strong> {result.result.page} ({result.result.per_page} per page)
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                  <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                    {result.result.videos.slice(0, 12).map((video, index) => (
                      <Grid item xs={12} sm={6} md={4} key={video.id || `video-${index}`}>
                        <Card elevation={1}>
                          <Box sx={{ position: 'relative' }}>
                            {video.image ? (
                              <img
                                src={video.image}
                                alt={`Video ${index + 1}`}
                                style={{
                                  width: '100%',
                                  height: '120px',
                                  objectFit: 'cover'
                                }}
                                onError={(e) => {
                                  // Replace with a colored background if image fails
                                  e.currentTarget.style.display = 'none';
                                  const parent = e.currentTarget.parentElement;
                                  if (parent && !parent.querySelector('.placeholder-bg')) {
                                    const placeholder = document.createElement('div');
                                    placeholder.className = 'placeholder-bg';
                                    placeholder.style.cssText = 'width: 100%; height: 120px; background: #f5f5f5; display: flex; align-items: center; justify-content: center; color: #999;';
                                    placeholder.textContent = 'Video Preview';
                                    parent.appendChild(placeholder);
                                  }
                                }}
                              />
                            ) : (
                              <Box
                                sx={{
                                  width: '100%',
                                  height: '120px',
                                  bgcolor: '#f5f5f5',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: '#999'
                                }}
                              >
                                Video Preview
                              </Box>
                            )}
                            <Chip
                              label={`${video.duration || 0}s`}
                              size="small"
                              sx={{
                                position: 'absolute',
                                bottom: 8,
                                right: 8,
                                bgcolor: 'rgba(0,0,0,0.7)',
                                color: 'white'
                              }}
                            />
                          </Box>
                          <CardContent sx={{ p: 1.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {video.width || '?'}x{video.height || '?'} - by {video.user?.name || 'Unknown'}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                              <Button
                                startIcon={<PlayIcon />}
                                href={video.url || '#'}
                                target="_blank"
                                size="small"
                                variant="outlined"
                                sx={{ flex: 1 }}
                                disabled={!video.url}
                              >
                                View
                              </Button>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {/* News Research Results */}
              {((result.result?.articles && Array.isArray(result.result.articles) && result.result.articles.length > 0) || result.result?.summary) && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    News Research Results
                  </Typography>

                  {/* Research Summary */}
                  {result.result?.summary && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        Research Summary
                      </Typography>
                      <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: 500, overflow: 'auto' }}>
                        <Typography
                          variant="body2"
                          component="div"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.6,
                            fontSize: '0.875rem',
                            '& strong': { fontWeight: 700 },
                            // Handle markdown-style formatting
                            '& h1, & h2, & h3, & h4': {
                              fontWeight: 600,
                              marginTop: 2,
                              marginBottom: 1,
                              fontSize: '1rem'
                            }
                          }}
                          dangerouslySetInnerHTML={{
                            __html: (result.result?.summary || '')
                              // Convert **text** to bold
                              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              // Convert ### Header to h3
                              .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                              // Convert ## Header to h2
                              .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                              // Convert # Header to h1
                              .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                              // Convert - bullet points to HTML lists
                              .replace(/^- (.*$)/gim, '&bull; $1')
                              // Convert line breaks
                              .replace(/\n\n/g, '<br><br>')
                              .replace(/\n/g, '<br>')
                          }}
                        />
                      </Paper>
                      {result.result?.research_date && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Research Date: {new Date(result.result.research_date).toLocaleString()}
                        </Typography>
                      )}
                    </Box>
                  )}

                  {/* News Articles */}
                  {result.result?.articles && Array.isArray(result.result.articles) && result.result.articles.length > 0 && (
                    <>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                        News Articles ({result.result.articles.length})
                      </Typography>
                      <List>
                        {result.result.articles.map((article, index) => (
                          <React.Fragment key={index}>
                            <ListItem alignItems="flex-start">
                              <ListItemAvatar>
                                <Avatar sx={{ bgcolor: 'primary.main' }}>
                                  <NewsIcon />
                                </Avatar>
                              </ListItemAvatar>
                              <Box sx={{ flex: 1 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600, pr: 2 }}>
                                    {article.title}
                                  </Typography>
                                  {(article.link || article.url) && (
                                    <Button
                                      component="a"
                                      href={article.link || article.url || '#'}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      size="small"
                                      variant="outlined"
                                      sx={{ ml: 1, minWidth: 'auto', flexShrink: 0 }}
                                    >
                                      Read
                                    </Button>
                                  )}
                                </Box>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                  {article.snippet || article.description || article.content?.substring(0, 200) + '...'}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {article.source} - {article.date ?
                                    new Date(article.date).toLocaleDateString() :
                                    (article.publishedAt ? new Date(article.publishedAt).toLocaleDateString() : 'Invalid Date')
                                  }
                                </Typography>
                              </Box>
                            </ListItem>
                            {index < (result.result?.articles?.length || 0) - 1 && <Divider />}
                          </React.Fragment>
                        ))}
                      </List>
                    </>
                  )}

                  {/* Research Sources */}
                  {(result.result?.sources_used && Array.isArray(result.result.sources_used) && result.result.sources_used.length > 0) && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        Research Sources ({result.result.total_sources || result.result.sources_used.length})
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {result.result.sources_used.map((source, index) => (
                          <Chip
                            key={index}
                            label={source}
                            variant="outlined"
                            size="small"
                            onClick={() => copyToClipboard(source)}
                            sx={{ cursor: 'pointer' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  {/* Fallback for legacy sources format */}
                  {(!result.result?.sources_used && result.result?.sources && Array.isArray(result.result.sources) && result.result.sources.length > 0) && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        Sources
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {result.result.sources.map((source, index) => (
                          <Chip
                            key={index}
                            label={source}
                            variant="outlined"
                            size="small"
                            onClick={() => copyToClipboard(source)}
                            sx={{ cursor: 'pointer' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}

              {/* AI Chat Response */}
              {result.result.content && (
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      AI Response
                    </Typography>
                    <Button
                      startIcon={<CopyIcon />}
                      onClick={() => copyToClipboard(result.result?.content || '')}
                      variant="outlined"
                      size="small"
                    >
                      Copy Response
                    </Button>
                  </Box>

                  <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: 400, overflow: 'auto' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.result.content}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {/* Video Download */}
              {(result.result.final_video_url || result.result.video_url) && (
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Generated Video
                    </Typography>
                    <Button
                      startIcon={<DownloadIcon />}
                      component="a"
                      href={result.result?.final_video_url || result.result?.video_url || '#'}
                      target="_blank"
                      variant="contained"
                      size="small"
                    >
                      Download
                    </Button>
                  </Box>

                  <Paper sx={{ p: 2, bgcolor: '#f8fafc', textAlign: 'center' }}>
                    <video
                      src={result.result.final_video_url || result.result.video_url}
                      controls
                      style={{
                        width: '100%',
                        maxHeight: '400px',
                        borderRadius: '8px'
                      }}
                    />
                  </Paper>
                </Box>
              )}

              {/* Web Search Results */}
              {result.result?.results && Array.isArray(result.result.results) && result.result.results.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ mb: 3, p: 2, bgcolor: '#f8fafc', borderRadius: 1 }}>
                    <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                      {typeof result.result?.query === 'string' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Search Query:</strong> {result.result.query}
                        </Grid>
                      )}
                      {typeof result.result?.engine === 'string' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Engine:</strong> {result.result.engine.charAt(0).toUpperCase() + result.result.engine.slice(1)}
                        </Grid>
                      )}
                      {typeof result.result?.total_results === 'number' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Results Found:</strong> {result.result.total_results}
                        </Grid>
                      )}
                      {typeof result.result?.search_time === 'number' && (
                        <Grid item xs={12} sm={6}>
                          <strong>Search Time:</strong> {result.result.search_time.toFixed(2)}s
                        </Grid>
                      )}
                    </Grid>
                  </Box>

                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Search Results ({(result.result.results as Array<unknown>).length})
                  </Typography>
                  <List>
                    {(result.result.results as Array<Record<string, unknown>>).map((item, index: number) => (
                      <React.Fragment key={index}>
                        <ListItem alignItems="flex-start" sx={{ py: 2 }}>
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: 'info.main' }}>
                              <SearchIcon />
                            </Avatar>
                          </ListItemAvatar>
                          <Box sx={{ flex: 1 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, pr: 2 }}>
                                {typeof item.title === 'string' ? item.title : ''}
                              </Typography>
                              {typeof item.url === 'string' && (
                                <Button
                                  component="a"
                                  href={item.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  size="small"
                                  variant="outlined"
                                  sx={{ ml: 1, minWidth: 'auto', flexShrink: 0 }}
                                >
                                  Visit
                                </Button>
                              )}
                            </Box>
                            {typeof item.content === 'string' && item.content && (
                              <Typography variant="body2" sx={{ mb: 1, lineHeight: 1.6 }}>
                                {item.content}
                              </Typography>
                            )}
                            {typeof item.description === 'string' && item.description && !item.content && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {item.description}
                              </Typography>
                            )}
                            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mt: 1 }}>
                              {typeof item.source === 'string' && (
                                <Typography variant="caption" color="text.secondary">
                                  <strong>Source:</strong> {item.source}
                                </Typography>
                              )}
                              {typeof item.published_at === 'string' && (
                                <Typography variant="caption" color="text.secondary">
                                  {new Date(item.published_at).toLocaleDateString()}
                                </Typography>
                              )}
                              {typeof item.url === 'string' && (
                                <Typography variant="caption" sx={{ color: '#1976d2', cursor: 'pointer' }} onClick={() => copyToClipboard(item.url as string)}>
                                  Copy URL
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </ListItem>
                        {index < ((result.result?.results as Array<unknown> | undefined)?.length || 0) - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Box>
              )}

              {/* Stock Image Search Results */}
              {result.result?.images && Array.isArray(result.result.images) && result.result.images.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Found {result.result.images.length} Images
                  </Typography>
                  <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                    {(result.result.images as Array<Record<string, unknown>>).slice(0, 12).map((image, index: number) => (
                      <Grid item xs={12} sm={6} md={4} key={(image.id as string) || `img-${index}`}>
                        <Card elevation={1}>
                          <Box sx={{ position: 'relative' }}>
                            <img
                              src={image.url as string}
                              alt={(image.alt as string) || 'Stock image'}
                              style={{
                                width: '100%',
                                height: '150px',
                                objectFit: 'cover'
                              }}
                            />
                          </Box>
                          <CardContent sx={{ p: 1.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {image.photographer ? `by ${image.photographer}` : 'Stock Image'}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                              <Button
                                href={image.url as string}
                                target="_blank"
                                size="small"
                                variant="outlined"
                                sx={{ flex: 1 }}
                              >
                                View
                              </Button>
                              {!!image.download_url && (
                                <Button
                                  startIcon={<DownloadIcon />}
                                  href={image.download_url as string}
                                  target="_blank"
                                  size="small"
                                  variant="contained"
                                  sx={{ flex: 1 }}
                                >
                                  Download
                                </Button>
                              )}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                  {result.result.images.length > 12 && (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 2 }}>
                      And {result.result.images.length - 12} more images...
                    </Typography>
                  )}
                </Box>
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
    renderJobResult
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
          Script & Search Tools
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '1rem', sm: '1.1rem' },
            lineHeight: 1.5
          }}
        >
          Advanced AI-powered tools for script generation, video search, scene creation, and content research.
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
            <Tab icon={<AIIcon />} label="Script Generator" />
            <Tab icon={<ArticleIcon />} label="Article to Script" />
            <Tab icon={<SearchIcon />} label="Video Search" />
            <Tab icon={<NewsIcon />} label="News Research" />
            <Tab icon={<SearchIcon />} label="Web Search" />
            <Tab icon={<ImageSearchIcon />} label="Stock Images" />
          </Tabs>
        </Box>

        <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
          <TabPanel value={tabValue} index={0}>
            <ScriptGeneratorTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <ArticleToScriptTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <VideoSearchTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <NewsResearchTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={4}>
            <WebSearchTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={5}>
            <StockImagesTab ctx={ctx} />
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default ScriptSearchTools;
