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
  Grid
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Subtitles as CaptionsIcon,
  TextFields as TextOverlayIcon,
  Download as DownloadIcon,
  Transform as TransformIcon,
  AudioFile as AddAudioIcon,
  CallMerge as MergeIcon,
  PhotoLibrary as ThumbnailsIcon,
  ViewModule as FramesIcon,
  Layers as VideoOverlayIcon,
  Movie as AIVideoIcon,
  SmartDisplay as VideoAnalysisIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { VoiceInfo } from '../../types/contentCreation';
import { TabPanelProps, JobResult, TabContext } from './types';

import ImageToVideoTab from './ImageToVideoTab';
import AIVideoGeneratorTab from './AIVideoGeneratorTab';
import AIClipsTab from './AIClipsTab';
import CaptionsTab from './CaptionsTab';
import TextOverlayTab from './TextOverlayTab';
import AddAudioTab from './AddAudioTab';
import MergeVideosTab from './MergeVideosTab';
import ThumbnailsTab from './ThumbnailsTab';
import ExtractFramesTab from './ExtractFramesTab';
import VideoOverlayTab from './VideoOverlayTab';
import VideoAnalysisTab from './VideoAnalysisTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`video-tools-tabpanel-${index}`}
      aria-labelledby={`video-tools-tab-${index}`}
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

const VideoTools: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, JobResult | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({});
  const [voices, setVoices] = useState<VoiceInfo[]>([]);

  // Fetch TTS voices on mount
  React.useEffect(() => {
    const fetchTTSData = async () => {
      try {
        const voicesRes = await directApi.get('/audio/voices/all');

        if (voicesRes.data && voicesRes.data.voices) {
          const flatVoices: VoiceInfo[] = [];

          Object.entries(voicesRes.data.voices).forEach(([provider, voiceList]) => {
            if (!voiceList || (Array.isArray(voiceList) && voiceList.length === 0)) {
              return;
            }

            (voiceList as Array<{
              name?: string;
              id?: string;
              label?: string;
              gender?: string;
              language?: string;
              description?: string;
              grade?: string;
              engine?: string;
            }>).forEach((voice) => {
              flatVoices.push({
                name: voice.name || voice.id || voice.label || 'Unknown Voice',
                gender: voice.gender || 'unknown',
                language: voice.language || 'en',
                description: voice.description || '',
                grade: voice.grade || '',
                provider: provider as 'kokoro' | 'edge' | 'piper'
              });
            });
          });

          if (flatVoices.length > 0) {
            setVoices(flatVoices);
          } else {
            setVoices([
              { name: 'af_heart', gender: 'female', language: 'en', description: 'Kokoro Female Voice', grade: '', provider: 'kokoro' },
              { name: 'af_bella', gender: 'female', language: 'en', description: 'Kokoro Female Voice', grade: '', provider: 'kokoro' }
            ]);
          }
        } else {
          setVoices([
            { name: 'af_heart', gender: 'female', language: 'en', description: 'Kokoro Female Voice', grade: '', provider: 'kokoro' }
          ]);
        }
      } catch {
        setVoices([
          { name: 'af_heart', gender: 'female', language: 'en', description: 'Kokoro Female Voice', grade: '', provider: 'kokoro' },
          { name: 'af_bella', gender: 'female', language: 'en', description: 'Kokoro Female Voice', grade: '', provider: 'kokoro' }
        ]);
      }
    };

    fetchTTSData();
  }, []);

  // Generic job polling
  const pollJobStatus = (jobId: string, toolName: string) => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const statusResponse = await directApi.get(`/jobs/${jobId}/status`);
        const jobData = statusResponse.data.data || statusResponse.data;
        const status = jobData.status;
        const jobResult = jobData.result;
        const jobError = jobData.error;

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
          setTimeout(poll, 5000);
        } else {
          setErrors(prev => ({ ...prev, [toolName]: 'Job polling timeout' }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
        }
      } catch (err: unknown) {
        const error = err as { response?: { status?: number; data?: { detail?: string } }; message?: string };
        if (error.response?.status === 401) {
          setErrors(prev => ({ ...prev, [toolName]: 'Authentication expired. Please login again.' }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
          window.location.href = '/auth/login';
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          const detail = error.response?.data?.detail;
          const detailStr = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.message);
          setErrors(prev => ({ ...prev, [toolName]: `Failed to check job status: ${detailStr}` }));
          setLoading(prev => ({ ...prev, [toolName]: false }));
        }
      }
    };

    poll();
  };

  const renderJobResult = (toolName: string, result: JobResult | null, icon: React.ReactNode) => {
    if (!result && !loading[toolName] && !errors[toolName]) return null;

    return (
      <Card elevation={0} sx={{ border: '1px solid #e2e8f0', mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' }, flexWrap: 'wrap' }}>
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
              {typeof errors[toolName] === 'string'
                ? errors[toolName]
                : Array.isArray(errors[toolName])
                  ? (errors[toolName] as unknown[]).map((d: unknown) => (d && typeof d === 'object' && 'msg' in d) ? (d as {msg: string}).msg : JSON.stringify(d)).join('; ')
                  : JSON.stringify(errors[toolName])}
            </Alert>
          )}

          {result && jobStatuses[toolName]?.includes('completed') && result.result && (
            <Box>
              {/* Check for silent backend failures */}
              {result.result.success === false || result.result.error ? (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {String(result.result.error || 'Processing failed with no details')}
                </Alert>
              ) : (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {toolName.charAt(0).toUpperCase() + toolName.slice(1)} completed successfully!
                </Alert>
              )}

              {/* Single Video Result */}
              {(() => {
                const videoUrl = result.result.final_video_url || result.result.video_url || result.result.output_url || result.result.url;
                return videoUrl ? (
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                        Generated Video
                      </Typography>
                      <Button
                        startIcon={<DownloadIcon />}
                        href={videoUrl}
                        target="_blank"
                        variant="contained"
                        size="small"
                        sx={{ width: { xs: '100%', sm: 'auto' } }}
                      >
                        Download
                      </Button>
                    </Box>
                    <Paper sx={{ p: 2, bgcolor: '#f8fafc', textAlign: 'center' }}>
                      <video
                        src={videoUrl}
                        controls
                        style={{ width: '100%', maxHeight: '400px', borderRadius: '8px' }}
                      />
                    </Paper>
                  </Box>
                ) : null;
              })()}

              {/* Multiple Clips Result */}
              {result.result.clip_urls && result.result.clip_urls.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Generated Clips ({result.result.clip_urls.length})
                  </Typography>
                  <Grid container spacing={2}>
                    {result.result.clip_urls.map((clipUrl, index) => (
                      <Grid item xs={12} sm={6} key={index}>
                        <Paper sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: '#f8fafc' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1, flexWrap: 'wrap', gap: 0.5 }}>
                            <Typography variant="subtitle2">
                              Clip {index + 1}
                            </Typography>
                            <Button
                              startIcon={<DownloadIcon />}
                              href={clipUrl}
                              target="_blank"
                              size="small"
                              variant="outlined"
                              sx={{ width: { xs: '100%', sm: 'auto' } }}
                            >
                              Download
                            </Button>
                          </Box>
                          <video
                            src={clipUrl}
                            controls
                            style={{ width: '100%', maxHeight: '200px', borderRadius: '4px' }}
                          />
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {/* Processing Details */}
              {(result.result.duration || result.result.resolution || result.result.processing_time || result.result.file_size) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Video Details:</Typography>
                  <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
                    <Grid container spacing={2} sx={{ fontSize: '0.875rem' }}>
                      {result.result.duration && (
                        <Grid item xs={12} sm={6} md={3}>
                          <strong>Duration:</strong> {result.result.duration}s
                        </Grid>
                      )}
                      {result.result.resolution && (
                        <Grid item xs={12} sm={6} md={3}>
                          <strong>Resolution:</strong> {result.result.resolution}
                        </Grid>
                      )}
                      {result.result.processing_time && (
                        <Grid item xs={12} sm={6} md={3}>
                          <strong>Processing:</strong> {result.result.processing_time}s
                        </Grid>
                      )}
                      {result.result.file_size && (
                        <Grid item xs={12} sm={6} md={3}>
                          <strong>Size:</strong> {(result.result.file_size / 1024 / 1024).toFixed(1)} MB
                        </Grid>
                      )}
                    </Grid>
                  </Paper>
                </Box>
              )}

              {/* SRT Download */}
              {result.result.srt_url && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    startIcon={<DownloadIcon />}
                    href={result.result.srt_url}
                    target="_blank"
                    variant="outlined"
                    size="small"
                  >
                    Download SRT Subtitles
                  </Button>
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
    renderJobResult,
    voices
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
          sx={{ fontWeight: 700, mb: 1, color: '#1a202c', fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' } }}
        >
          Video Tools
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '1rem', sm: '1.1rem' }, lineHeight: 1.5 }}
        >
          Create, edit, and enhance videos with AI-powered tools and professional effects.
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
            <Tab icon={<TransformIcon />} label="Image to Video" iconPosition="start" />
            <Tab icon={<AIVideoIcon />} label="AI Video" iconPosition="start" />
            <Tab icon={<AIIcon />} label="AI Clips" iconPosition="start" />
            <Tab icon={<CaptionsIcon />} label="Captions" iconPosition="start" />
            <Tab icon={<TextOverlayIcon />} label="Text Overlay" iconPosition="start" />
            <Tab icon={<AddAudioIcon />} label="Add Audio" iconPosition="start" />
            <Tab icon={<MergeIcon />} label="Merge" iconPosition="start" />
            <Tab icon={<ThumbnailsIcon />} label="Thumbnails" iconPosition="start" />
            <Tab icon={<FramesIcon />} label="Frames" iconPosition="start" />
            <Tab icon={<VideoOverlayIcon />} label="Overlay" iconPosition="start" />
            <Tab icon={<VideoAnalysisIcon />} label="Analysis" iconPosition="start" />
          </Tabs>
        </Box>

        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          <TabPanel value={tabValue} index={0}>
            <ImageToVideoTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <AIVideoGeneratorTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <AIClipsTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <CaptionsTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={4}>
            <TextOverlayTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={5}>
            <AddAudioTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={6}>
            <MergeVideosTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={7}>
            <ThumbnailsTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={8}>
            <ExtractFramesTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={9}>
            <VideoOverlayTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={10}>
            <VideoAnalysisTab ctx={ctx} />
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default VideoTools;
