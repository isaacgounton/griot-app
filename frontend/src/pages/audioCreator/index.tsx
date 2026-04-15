import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Tab,
  Tabs,
  LinearProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  VolumeUp as AudioIcon,
  MusicNote as MusicIcon,
  Subtitles as TranscribeIcon,
  VideoLibrary as LibraryIcon,
  GraphicEq as VadIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import {
  TabPanelProps,
  TabContext,
  VoicesData,
  ModelsData,
  ProvidersData,
  ApiResult,
  TranscriptionJobResult
} from './types';

import AudioGenerationTab from './AudioGenerationTab';
import MusicGenerationTab from './MusicGenerationTab';
import TranscriptionTab from './TranscriptionTab';
import MusicTracksTab from './MusicTracksTab';
import VoiceDetectionTab from './VoiceDetectionTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`audio-tabpanel-${index}`}
      aria-labelledby={`audio-tab-${index}`}
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

const AudioCreatorPage: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<'pending' | 'processing' | 'completed' | 'failed' | null>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [voices, setVoices] = useState<VoicesData>({});
  const [models, setModels] = useState<ModelsData>({});
  const [providers, setProviders] = useState<ProvidersData>({});
  const [loadingVoices, setLoadingVoices] = useState(false);

  // Fetch TTS data on component mount
  useEffect(() => {
    const fetchTTSData = async () => {
      setLoadingVoices(true);
      try {
        const [voicesRes, modelsRes, providersRes] = await Promise.all([
          directApi.get('/audio/voices/all'),
          directApi.get('/audio/models'),
          directApi.get('/audio/providers')
        ]);

        if (voicesRes.data) {
          setVoices(voicesRes.data.voices || {});
        }

        if (modelsRes.data) {
          setModels(modelsRes.data || {});
        }

        if (providersRes.data) {
          setProviders(providersRes.data || {});
        }
      } catch (error) {
        console.error('Failed to fetch TTS data:', error);
        setVoices({
          'kokoro': [
            { "id": "af_heart", "name": "af_heart", "gender": "female", "language": "en-US", "description": "American Female - Heart (Grade A)", "grade": "A", "engine": "kokoro" },
            { "id": "af_alloy", "name": "af_alloy", "gender": "female", "language": "en-US", "description": "American Female - Alloy (Grade C)", "grade": "C", "engine": "kokoro" },
            { "id": "af_bella", "name": "af_bella", "gender": "female", "language": "en-US", "description": "American Female - Bella (Grade A-)", "grade": "A-", "engine": "kokoro" },
            { "id": "am_michael", "name": "am_michael", "gender": "male", "language": "en-US", "description": "American Male - Michael (Grade C+)", "grade": "C+", "engine": "kokoro" },
            { "id": "bf_emma", "name": "bf_emma", "gender": "female", "language": "en-GB", "description": "British Female - Emma (Grade B-)", "grade": "B-", "engine": "kokoro" },
            { "id": "bm_george", "name": "bm_george", "gender": "male", "language": "en-GB", "description": "British Male - George (Grade C)", "grade": "C", "engine": "kokoro" },
          ],
          'piper': [
            { "id": "en_US-lessac-medium", "name": "en_US-lessac-medium", "language": "en_US", "gender": "unknown", "quality": "medium", "available": true, "downloaded": false },
            { "id": "en_US-lessac-low", "name": "en_US-lessac-low", "language": "en_US", "gender": "unknown", "quality": "low", "available": true, "downloaded": false },
            { "id": "en_US-lessac-high", "name": "en_US-lessac-high", "language": "en_US", "gender": "unknown", "quality": "high", "available": true, "downloaded": false },
          ],
          'edge': []
        });
        setModels({
          "models": {
            "edge": [{ "id": "en-US-AriaRUS", "name": "Aria (en-US)" }],
            "kokoro": [{ "id": "kokoro-v1.0", "name": "Kokoro ONNX v1.0" }],
            "piper": [{ "id": "en_US-lessac-medium", "name": "Lessac (en-US)" }]
          }
        });
        setProviders({
          "providers": ["kokoro", "piper", "edge"],
          "formats": {
            "kokoro": ["wav"],
            "piper": ["wav", "mp3"],
            "edge": ["mp3", "wav", "opus", "aac", "flac", "pcm"]
          },
          "models": {
            "edge": [{ "id": "en-US-AriaRUS", "name": "Aria (en-US)" }],
            "kokoro": [{ "id": "kokoro-v1.0", "name": "Kokoro ONNX v1.0" }],
            "piper": [{ "id": "en_US-lessac-medium", "name": "Lessac (en-US)" }]
          },
          "default_provider": "kokoro"
        });
      } finally {
        setLoadingVoices(false);
      }
    };

    fetchTTSData();
  }, []);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setResult(null);
    setError(null);
    setJobStatus(null);
    setJobProgress('');
    setPollingJobId(null);
  };

  // Job status polling function
  const pollJobStatus = (jobId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;

        const statusResponse = await directApi.getJobStatus(jobId);

        if (!statusResponse.success || !statusResponse.data) {
          throw new Error(statusResponse.error || 'Failed to get job status');
        }

        const job = statusResponse.data;
        const status = job.status;
        const jobResult = job.result;
        const jobError = job.error;

        setJobStatus(status);

        if (status === 'completed') {
          setJobProgress('Job completed successfully!');
          setResult({ job_id: jobId, jobResult, status: 'completed' });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Job failed');
          setError(jobError || 'Job processing failed');
          setLoading(false);
          return;
        } else if (status === 'processing') {
          setJobProgress(`Processing... (${attempts}/${maxAttempts})`);
        } else {
          setJobProgress(`Queued... (${attempts}/${maxAttempts})`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setError('Job polling timeout. Please check status manually.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setError('Failed to check job status');
          setLoading(false);
        }
      }
    };

    poll();
  };

  // Audio player component
  const AudioPlayer: React.FC<{ audioUrl: string; title: string }> = ({ audioUrl, title }) => (
    <Box sx={{ mt: 3, mb: 3, p: { xs: 2, sm: 3 }, border: '1px solid #e2e8f0', borderRadius: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {title}
      </Typography>
      <audio controls style={{ width: '100%', marginBottom: '8px' }}>
        <source src={audioUrl} type="audio/mpeg" />
        <source src={audioUrl} type="audio/wav" />
        Your browser does not support the audio element.
      </audio>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={() => window.open(audioUrl, '_blank')}
        >
          Download
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => navigator.clipboard.writeText(audioUrl)}
        >
          Copy URL
        </Button>
        <Button
          startIcon={<LibraryIcon />}
          onClick={() => navigate('/dashboard/library')}
          variant="outlined"
          size="small"
          color="primary"
        >
          View in Library
        </Button>
      </Box>
    </Box>
  );

  // Render job result in sidebar
  const renderJobResult = (tabIndex: number): React.ReactNode => {
    if (!result && !error && !jobStatus) return null;

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          {tabIndex === 0 && 'Speech Result'}
          {tabIndex === 1 && 'Music Result'}
          {tabIndex === 2 && 'Transcription Result'}
          {jobStatus && jobStatus !== 'completed' && (
            <CircularProgress size={16} sx={{ ml: 1 }} />
          )}
        </Typography>

        {/* Job Status */}
        {jobStatus && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Job ID: {pollingJobId}
            </Typography>
            <LinearProgress
              variant={jobStatus === 'completed' ? 'determinate' : 'indeterminate'}
              value={jobStatus === 'completed' ? 100 : undefined}
              sx={{ mb: 1, height: 4, borderRadius: 2 }}
            />
            <Typography variant="body2" sx={{
              color: jobStatus === 'completed' ? 'success.main' :
                jobStatus === 'failed' ? 'error.main' : 'info.main',
              fontSize: '0.75rem'
            }}>
              {jobProgress}
            </Typography>
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>
            {error}
          </Alert>
        )}

        {/* Success Results */}
        {result && jobStatus === 'completed' && result.jobResult && (
          <Box>
            <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
              {tabIndex === 0 && 'Speech generated successfully!'}
              {tabIndex === 1 && 'Music generated successfully!'}
              {tabIndex === 2 && 'Transcription completed successfully!'}
            </Alert>

            {/* Audio Player for Speech and Music */}
            {(tabIndex === 0 || tabIndex === 1) && 'audio_url' in result.jobResult && result.jobResult.audio_url && (
              <AudioPlayer
                audioUrl={('audio_url' in result.jobResult) ? result.jobResult.audio_url : ''}
                title={tabIndex === 0 ? 'Generated Speech' : 'Generated Music'}
              />
            )}

            {/* Transcription Results */}
            {tabIndex === 2 && (() => {
              const tr = result.jobResult as TranscriptionJobResult;
              return (
                <Box>
                  {tr.text && (
                    <Paper sx={{ p: 2, mb: 2, bgcolor: '#f8fafc', maxHeight: 300, overflow: 'auto' }}>
                      <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.75rem' }}>Transcription:</Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{tr.text}</Typography>
                    </Paper>
                  )}
                  {tr.srt_url && (
                    <Button
                      variant="outlined"
                      size="small"
                      href={tr.srt_url}
                      download
                      sx={{ mb: 1, mr: 1 }}
                    >
                      Download SRT
                    </Button>
                  )}
                  {tr.words && tr.words.length > 0 && (
                    <Accordion sx={{ mt: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="body2">{tr.words.length} word timestamps</Typography>
                      </AccordionSummary>
                      <AccordionDetails sx={{ maxHeight: 250, overflow: 'auto' }}>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {tr.words.map((w, i) => (
                            <Chip
                              key={i}
                              label={`${w.word} [${w.start.toFixed(2)}s]`}
                              size="small"
                              variant="outlined"
                              sx={{
                                fontSize: '0.7rem',
                                borderColor: w.probability > 0.9 ? '#4caf50' : w.probability > 0.7 ? '#ff9800' : '#f44336',
                                opacity: 0.7 + w.probability * 0.3,
                              }}
                              title={`${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s (${(w.probability * 100).toFixed(0)}% confidence)`}
                            />
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  )}
                  {tr.segments && tr.segments.length > 0 && (
                    <Accordion sx={{ mt: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="body2">{tr.segments.length} segments</Typography>
                      </AccordionSummary>
                      <AccordionDetails sx={{ maxHeight: 200, overflow: 'auto' }}>
                        {tr.segments.map((seg, i) => (
                          <Box key={i} sx={{ mb: 0.5, fontSize: '0.75rem' }}>
                            <Typography component="span" variant="caption" color="text.secondary">
                              [{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s]
                            </Typography>{' '}
                            <Typography component="span" variant="body2">{seg.text}</Typography>
                          </Box>
                        ))}
                      </AccordionDetails>
                    </Accordion>
                  )}
                </Box>
              );
            })()}

            {/* Additional Result Info */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.75rem' }}>Job Details:</Typography>
              <Paper sx={{ p: 1.5, bgcolor: '#f8fafc' }}>
                <Grid container spacing={{ xs: 1, sm: 1 }} sx={{ fontSize: '0.75rem' }}>
                  {'tts_engine' in result.jobResult && result.jobResult.tts_engine && (
                    <Grid item xs={6}>
                      <strong>Engine:</strong> {('tts_engine' in result.jobResult) ? result.jobResult.tts_engine : ''}
                    </Grid>
                  )}
                  {'voice' in result.jobResult && result.jobResult.voice && (
                    <Grid item xs={6}>
                      <strong>Voice:</strong> {('voice' in result.jobResult) ? result.jobResult.voice : ''}
                    </Grid>
                  )}
                  {'response_format' in result.jobResult && result.jobResult.response_format && (
                    <Grid item xs={6}>
                      <strong>Format:</strong> {('response_format' in result.jobResult) ? result.jobResult.response_format : ''}
                    </Grid>
                  )}
                  {'duration' in result.jobResult && result.jobResult.duration != null && (
                    <Grid item xs={6}>
                      <strong>Duration:</strong> {Number(result.jobResult.duration).toFixed(1)}s
                    </Grid>
                  )}
                  {'estimated_duration' in result.jobResult && result.jobResult.estimated_duration != null && !('duration' in result.jobResult) && (
                    <Grid item xs={6}>
                      <strong>Duration:</strong> {result.jobResult.estimated_duration}s
                    </Grid>
                  )}
                  {'language' in result.jobResult && result.jobResult.language && (
                    <Grid item xs={6}>
                      <strong>Language:</strong> {result.jobResult.language}
                      {'language_probability' in result.jobResult && result.jobResult.language_probability != null &&
                        ` (${(Number(result.jobResult.language_probability) * 100).toFixed(0)}%)`
                      }
                    </Grid>
                  )}
                  {'word_count' in result.jobResult && result.jobResult.word_count != null && (
                    <Grid item xs={6}>
                      <strong>Words:</strong> {result.jobResult.word_count}
                    </Grid>
                  )}
                  {'words' in result.jobResult && Array.isArray(result.jobResult.words) && result.jobResult.words.length > 0 && (
                    <Grid item xs={6}>
                      <strong>Words:</strong> {result.jobResult.words.length}
                    </Grid>
                  )}
                  {'model_used' in result.jobResult && result.jobResult.model_used && (
                    <Grid item xs={6}>
                      <strong>Model:</strong> {('model_used' in result.jobResult) ? result.jobResult.model_used : ''}
                    </Grid>
                  )}
                </Grid>
              </Paper>
            </Box>
          </Box>
        )}

        {/* Initial Job Created Message */}
        {result && !result.jobResult && jobStatus !== 'completed' && (
          <Box>
            <Alert severity="info" sx={{ mb: 2, fontSize: '0.75rem' }}>
              {tabIndex === 0 && 'Speech generation job created successfully!'}
              {tabIndex === 1 && 'Music generation job created successfully!'}
              {tabIndex === 2 && 'Transcription job created successfully!'}
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              Job ID: <code style={{ padding: '1px 3px', backgroundColor: '#f1f3f4', borderRadius: '2px', fontSize: '0.7rem' }}>
                {result.job_id}
              </code>
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  const ctx: TabContext = {
    loading, setLoading,
    error, setError,
    result, setResult,
    jobStatus, setJobStatus,
    jobProgress, setJobProgress,
    pollingJobId, setPollingJobId,
    pollJobStatus,
    renderJobResult,
    AudioPlayer,
    voices, models, providers, loadingVoices
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
          Audio Tools
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '1rem', sm: '1.1rem' },
            lineHeight: 1.5
          }}
        >
          Generate speech, create music, and transcribe audio content with AI-powered tools.
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: { xs: 2, sm: 3 } }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            borderBottom: '1px solid #e2e8f0',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 600,
              fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' },
              minHeight: { xs: 48, sm: 64 },
              minWidth: { xs: 80, sm: 120 },
              py: { xs: 0.75, sm: 1.5 },
              px: { xs: 1, sm: 2 }
            }
          }}
        >
          <Tab
            icon={<AudioIcon />}
            label="Audio Generation"
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab
            icon={<MusicIcon />}
            label="Music Generation"
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab
            icon={<TranscribeIcon />}
            label="Transcription"
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab
            icon={<LibraryIcon />}
            label="Music Tracks"
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab
            icon={<VadIcon />}
            label="Voice Detection"
            iconPosition="start"
            sx={{ gap: 1 }}
          />
        </Tabs>

        <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
          <TabPanel value={tabValue} index={0}>
            <AudioGenerationTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <MusicGenerationTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <TranscriptionTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <MusicTracksTab />
          </TabPanel>
          <TabPanel value={tabValue} index={4}>
            <VoiceDetectionTab ctx={ctx} />
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default AudioCreatorPage;
