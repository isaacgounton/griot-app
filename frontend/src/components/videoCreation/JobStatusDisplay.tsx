import React from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Button,
  Alert,
  Paper,
  Card,
  CardContent,
  CardActions,
  Chip,
  Grid,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  CloudDownload as DownloadIcon,
  Refresh as ResetIcon,
  VideoLibrary as VideoIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';

import {
  ContentCreationJobResult,
  ContentCreationJobStatus,
  VideoCreationResult,
  TopicResearchResult
} from '../../types/contentCreation';
import VideoResultPreview from './VideoResultPreview';

interface JobStatusDisplayProps {
  loading: boolean;
  jobStatus: ContentCreationJobStatus | null;
  jobProgress: string;
  result: ContentCreationJobResult | null;
  isResumedJob?: boolean;
  onReset: () => void;
  onSchedule?: () => void;
}

const JobStatusDisplay: React.FC<JobStatusDisplayProps> = ({
  loading,
  jobStatus,
  jobProgress,
  result,
  isResumedJob = false,
  onReset,
  onSchedule,
}) => {

  

  const getStatusIcon = (status: ContentCreationJobStatus | null) => {
    switch (status) {
      case 'completed': return <SuccessIcon color="success" />;
      case 'failed': return <ErrorIcon color="error" />;
      case 'processing': return null; // Remove duplicate spinner
      case 'pending': return null; // Remove duplicate spinner  
      default: return null; // Remove duplicate spinner
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  // Show processing status
  if (loading || (jobStatus && jobStatus !== 'completed')) {
    return (
      <Paper elevation={0} sx={{ 
        border: '1px solid #e2e8f0', 
        borderRadius: 2, 
        p: { xs: 2, sm: 3 }, 
        mb: 3 
      }}>
        <Box sx={{ textAlign: 'center' }}>
          <Box sx={{ mb: 2 }}>
            {jobStatus === 'processing' ? (
              <CircularProgress size={60} color="primary" />
            ) : (
              <CircularProgress size={60} color="secondary" />
            )}
          </Box>
          
          <Typography 
            variant="h6" 
            sx={{ 
              mb: 1, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              gap: 1,
              fontSize: { xs: '1.1rem', sm: '1.25rem' },
              flexWrap: 'wrap'
            }}
          >
            {getStatusIcon(jobStatus)}
            {jobStatus ? jobStatus.charAt(0).toUpperCase() + jobStatus.slice(1) : 'Processing'}
          </Typography>
          
          {isResumedJob && (
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
              <Chip 
                label="🔄 Resumed from previous session" 
                color="info" 
                variant="outlined" 
                size="small"
                sx={{ 
                  fontSize: { xs: '0.7rem', sm: '0.75rem' },
                  height: { xs: '24px', sm: '28px' }
                }}
              />
            </Box>
          )}
          
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 2,
              fontSize: { xs: '0.9rem', sm: '1rem' },
              lineHeight: 1.4
            }}
          >
            {jobProgress || 'Processing your request...'}
          </Typography>
          
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{
              fontSize: { xs: '0.8rem', sm: '0.875rem' },
              lineHeight: 1.4,
              px: { xs: 1, sm: 0 }
            }}
          >
            {isResumedJob 
              ? "✨ Good news! You can now safely leave this page and return later to check your video status."
              : "This may take 15-20 minutes for complex videos. You can safely leave this page and return later - your job will continue processing."
            }
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Show completed result
  if (result && result.status === 'completed' && result.result) {
    const isVideoResult = 'video_url' in result.result;
    const videoResult = result.result as VideoCreationResult;
    const researchResult = result.result as TopicResearchResult;

    // Debug: Log the result structure to understand the video URL fields
    // console.log('Job result structure:', result.result);
    
    // Get the video URL - should be standardized to final_video_url
    const getVideoUrl = (): string | null => {
      const resultData = result.result as VideoCreationResult | TopicResearchResult | undefined;
      if (!resultData) return null;
      
      // Primary: standardized field name
      const url = (resultData.final_video_url as string) || 
                  // Fallbacks for legacy/inconsistent services
                  (resultData.video_url as string) || 
                  (resultData.url as string) ||
                  null;
      
      return url;
    };
    
    const actualVideoUrl = getVideoUrl();

    return (
      <Card elevation={0} sx={{ 
        border: '1px solid #e2e8f0', 
        borderRadius: 2, 
        mb: 3 
      }}>
        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
          <Box sx={{ textAlign: 'center', mb: { xs: 3, sm: 4 } }}>
            <Box sx={{
              mb: 2,
              p: { xs: 2, sm: 3 },
              borderRadius: '50%',
              bgcolor: 'success.light',
              width: { xs: 60, sm: 80 },
              height: { xs: 60, sm: 80 },
              mx: 'auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(34, 197, 94, 0.3)'
            }}>
              <SuccessIcon sx={{ 
                fontSize: { xs: 30, sm: 40 }, 
                color: 'success.main' 
              }} />
            </Box>
            <Typography 
              variant="h4" 
              sx={{ 
                fontWeight: 700, 
                color: 'success.main', 
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '2rem' }
              }}
            >
              🎉 Video Created Successfully!
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2, fontSize: '1.1rem' }}>
              Your video has been generated and is ready to watch
            </Typography>
            <Chip
              label="✨ Processing Complete"
              color="success"
              variant="filled"
              sx={{
                fontSize: '0.9rem',
                fontWeight: 600,
                px: 3,
                py: 1,
                borderRadius: 3,
                boxShadow: '0 2px 8px rgba(34, 197, 94, 0.3)'
              }}
            />
          </Box>

          {/* Video Preview */}
          <Box sx={{ mb: 3 }}>
            {actualVideoUrl && (
              <Box sx={{ mb: 3 }}>
                <VideoResultPreview url={actualVideoUrl} />
              </Box>
            )}
            
            {/* Debug info for troubleshooting */}
            {!actualVideoUrl && (
              <Box sx={{ mb: 2, p: 2, backgroundColor: '#fef3c7', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  ⚠️ Video URL not found. Available fields: {Object.keys(result.result || {}).join(', ')}
                </Typography>
              </Box>
            )}

            {/* Video Details - styled like VideoTools.tsx */}
            {(() => {
              const resultData = result.result as VideoCreationResult | TopicResearchResult;
              return (Boolean(resultData.video_duration) || Boolean(resultData.duration) || Boolean(resultData.resolution) || Boolean(resultData.processing_time) || Boolean(resultData.file_size_mb) || Boolean(resultData.word_count) || Boolean(resultData.segments_count)) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>📊 Video Details:</Typography>
                  <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
                    <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                      {Boolean(resultData.video_duration || resultData.duration) && (
                        <Grid item xs={12} md={3}>
                          <strong>Duration:</strong> {formatDuration(Number(resultData.video_duration || resultData.duration))}
                        </Grid>
                      )}
                      {Boolean(resultData.resolution) && (
                        <Grid item xs={12} md={3}>
                          <strong>Resolution:</strong> {String(resultData.resolution)}
                        </Grid>
                      )}
                      {Boolean(resultData.processing_time) && (
                        <Grid item xs={12} md={3}>
                          <strong>Processing:</strong> {formatDuration(Number(resultData.processing_time))}
                        </Grid>
                      )}
                      {Boolean(resultData.file_size_mb) && (
                        <Grid item xs={12} md={3}>
                          <strong>Size:</strong> {String(resultData.file_size_mb)} MB
                        </Grid>
                      )}
                      {Boolean(resultData.word_count) && (
                        <Grid item xs={12} md={3}>
                          <strong>Words:</strong> {String(resultData.word_count)}
                        </Grid>
                      )}
                      {Boolean(resultData.segments_count) && (
                        <Grid item xs={12} md={3}>
                          <strong>Segments:</strong> {String(resultData.segments_count)}
                        </Grid>
                      )}
                    </Grid>
                  </Paper>
                </Box>
              );
            })()}

            {/* SRT Download */}
            {(() => {
              const resultData = result.result as VideoCreationResult | TopicResearchResult;
              return Boolean(resultData.srt_url) && (
                <Box sx={{ mt: 2, textAlign: 'center' }}>
                  <Button
                    startIcon={<DownloadIcon />}
                    href={String(resultData.srt_url || '#')}
                    target="_blank"
                    variant="outlined"
                    size="small"
                  >
                    Download SRT Subtitles
                  </Button>
                </Box>
              );
            })()}

            {/* Legacy metadata support */}
            {videoResult.metadata && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center', mb: 2 }}>
                <Chip 
                  label={`${videoResult.metadata.resolution}`} 
                  size="small" 
                  variant="outlined"
                  icon={<VideoIcon />}
                />
                <Chip 
                  label={`${videoResult.metadata.aspect_ratio}`} 
                  size="small" 
                  variant="outlined"
                />
                <Chip 
                  label={`${videoResult.metadata.total_scenes} scenes`} 
                  size="small" 
                  variant="outlined"
                />
                <Chip 
                  label={videoResult.metadata.voice_used} 
                  size="small" 
                  variant="outlined"
                />
                {videoResult.duration && (
                  <Chip 
                    label={formatDuration(videoResult.duration)} 
                    size="small" 
                    variant="outlined"
                  />
                )}
                {videoResult.file_size && (
                  <Chip 
                    label={formatFileSize(videoResult.file_size)} 
                    size="small" 
                    variant="outlined"
                  />
                )}
              </Box>
            )}

            {/* Research Script Info */}
            {!isVideoResult && researchResult.script && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {researchResult.script.title}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                  <Chip 
                    label={`${researchResult.script.scenes.length} scenes`} 
                    size="small" 
                    variant="outlined"
                  />
                  <Chip 
                    label={formatDuration(researchResult.script.total_duration)} 
                    size="small" 
                    variant="outlined"
                  />
                  {researchResult.script.research_sources && (
                    <Chip 
                      label={`${researchResult.script.research_sources.length} sources`} 
                      size="small" 
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>
            )}
          </Box>
        </CardContent>

        <CardActions sx={{ justifyContent: 'center', pb: 4, pt: 3, gap: 2 }}>
          {onSchedule && (
            <Button
              variant="contained"
              size="large"
              startIcon={<ScheduleIcon />}
              onClick={onSchedule}
              sx={{
                borderRadius: 3,
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 600,
                backgroundColor: '#10b981',
                '&:hover': {
                  backgroundColor: '#059669',
                  boxShadow: '0 6px 16px rgba(16, 185, 129, 0.4)',
                  transform: 'translateY(-1px)'
                },
                boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                transition: 'all 0.2s ease-in-out'
              }}
            >
              Schedule Post
            </Button>
          )}
          <Button
            variant="contained"
            size="large"
            startIcon={<ResetIcon />}
            onClick={onReset}
            sx={{
              borderRadius: 3,
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
              backgroundColor: '#3b82f6',
              '&:hover': {
                backgroundColor: '#2563eb',
                boxShadow: '0 6px 16px rgba(59, 130, 246, 0.4)',
                transform: 'translateY(-1px)'
              },
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
              transition: 'all 0.2s ease-in-out'
            }}
          >
            Create New Video
          </Button>
        </CardActions>
      </Card>
    );
  }

  // Show failed result
  if (result && result.status === 'failed') {
    return (
      <Alert 
        severity="error" 
        sx={{ mb: 3 }}
        action={
          <Button color="inherit" size="small" onClick={onReset}>
            Try Again
          </Button>
        }
      >
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Video Creation Failed
        </Typography>
        <Typography variant="body2">
          {result.error || 'An unknown error occurred during video processing.'}
        </Typography>
      </Alert>
    );
  }

  return null;
};

export default JobStatusDisplay;