import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow
} from '@mui/material';
import {
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon,
  Transform as ConvertIcon,
  Info as MetadataIcon,
  YouTube as YouTubeIcon,
  ExpandMore as ExpandMoreIcon,
  AudioFile as AudioIcon,
  Image as ImageIcon,
  VideoLibrary as LibraryIcon,
  VolumeOff as SilenceIcon,
  Analytics as AnalysisIcon,
  ScreenshotMonitor as ScreenshotIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabPanelProps, JobResult, SupportedFormats, TabContext } from './types';

import MediaDownloadTab from './MediaDownloadTab';
import WebScreenshotsTab from './WebScreenshotsTab';
import FormatConversionTab from './FormatConversionTab';
import MetadataExtractionTab from './MetadataExtractionTab';
import YouTubeTranscriptsTab from './YouTubeTranscriptsTab';
import SilenceDetectionTab from './SilenceDetectionTab';
import AudioAnalysisTab from './AudioAnalysisTab';
import FileUploadTab from './FileUploadTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`media-tools-tabpanel-${index}`}
      aria-labelledby={`media-tools-tab-${index}`}
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

const MediaTools: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, JobResult | null>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({});
  const [supportedFormats, setSupportedFormats] = useState<{
    supported_formats?: SupportedFormats;
    quality_presets?: string[];
    total_formats?: number;
  } | null>(null);

  // Fetch supported formats on component mount
  React.useEffect(() => {
    const fetchFormats = async () => {
      try {
        const response = await directApi.get('/media/conversions/formats');
        setSupportedFormats(response.data);
      } catch (error) {
        console.error('Failed to fetch supported formats:', error);
      }
    };

    fetchFormats();
  }, []);

  // Generic job polling function
  const pollJobStatus = async (jobId: string, toolName: string) => {
    const maxAttempts = 60; // 5 minutes max
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

  const renderJobResult = (toolName: string, result: JobResult | null, icon: React.ReactNode) => {
    if (!result && !loading[toolName] && !errors[toolName]) return null;

    return (
      <Card elevation={0} sx={{ border: '1px solid #e2e8f0', mt: { xs: 2, sm: 3 } }}>
        <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
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

          {result && jobStatuses[toolName] === 'completed' && result.result && (
            <Box>
              {/* Check for silent backend failures */}
              {(result.result as Record<string, unknown>).success === false || (result.result as Record<string, unknown>).error ? (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {String((result.result as Record<string, unknown>).error || 'Processing failed with no details')}
                </Alert>
              ) : (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {toolName.charAt(0).toUpperCase() + toolName.slice(1)} completed successfully!
                </Alert>
              )}

              {/* Download Links */}
              {(result.result.file_url || result.result.thumbnail_url || result.result.subtitle_urls) && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    Download Files:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, flexDirection: { xs: 'column', sm: 'row' } }}>
                    {result.result.file_url && (
                      <Button
                        startIcon={<DownloadIcon />}
                        href={result.result.file_url as string}
                        target="_blank"
                        variant="contained"
                        size="small"
                        sx={{ width: { xs: '100%', sm: 'auto' } }}
                      >
                        Download Media
                      </Button>
                    )}
                    {result.result.thumbnail_url && (
                      <Button
                        startIcon={<ImageIcon />}
                        href={result.result.thumbnail_url as string}
                        target="_blank"
                        variant="outlined"
                        size="small"
                        color="secondary"
                        sx={{ width: { xs: '100%', sm: 'auto' } }}
                      >
                        Download Thumbnail
                      </Button>
                    )}
                    {result.result.subtitle_urls && Array.isArray(result.result.subtitle_urls) && (
                      result.result.subtitle_urls.map((subtitleUrl: string, index: number) => (
                        <Button
                          key={index}
                          startIcon={<AudioIcon />}
                          href={subtitleUrl}
                          target="_blank"
                          variant="outlined"
                          size="small"
                          color="info"
                          sx={{ width: { xs: '100%', sm: 'auto' } }}
                        >
                          Download Subtitle {index + 1}
                        </Button>
                      ))
                    )}
                    <Button
                      startIcon={<LibraryIcon />}
                      onClick={() => navigate('/dashboard/library')}
                      variant="outlined"
                      size="small"
                      color="primary"
                      sx={{ width: { xs: '100%', sm: 'auto' } }}
                    >
                      View in Library
                    </Button>
                  </Box>
                  {result.result.total_files && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Total files generated: {String(result.result.total_files)}
                    </Typography>
                  )}
                </Box>
              )}

              {/* Screenshot Preview */}
              {toolName === 'screenshot' && result.result.file_url && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    Preview:
                  </Typography>
                  <Paper
                    sx={{
                      p: 1,
                      display: 'inline-block',
                      maxWidth: '100%',
                      bgcolor: '#f8fafc'
                    }}
                  >
                    <img
                      src={result.result.file_url}
                      alt="Screenshot preview"
                      style={{
                        maxWidth: '100%',
                        height: 'auto',
                        borderRadius: '4px',
                        display: 'block'
                      }}
                    />
                  </Paper>
                </Box>
              )}

              {/* Metadata Display */}
              {(result.result.metadata || (toolName === 'metadata' && result.result)) && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">Media Metadata</Typography>
                  </AccordionSummary>
                  <AccordionDetails sx={{ px: { xs: 1, sm: 2 } }}>
                    <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
                      <Table size="small">
                        <TableBody>
                          {Object.entries(result.result.metadata || result.result).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell component="th" scope="row" sx={{ fontWeight: 600, width: { xs: '40%', sm: '30%' }, fontSize: { xs: '0.75rem', sm: '0.875rem' }, wordBreak: 'break-word' }}>
                                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </TableCell>
                              <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, wordBreak: 'break-all' }}>
                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Transcript Display */}
              {result.result.transcript && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                    Transcript:
                  </Typography>
                  <Paper sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: '#f8fafc', maxHeight: 300, overflow: 'auto' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: { xs: '0.8rem', sm: '0.875rem' }, wordBreak: 'break-word' }}>
                      {result.result.transcript}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {/* Silence Detection Results */}
              {((result.result as any).segments || result.result.type) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                    {result.result.type === 'speech_segments' ? 'Speech Segments' : 'Silence Intervals'}
                    ({String((result.result as any).total_segments || 0)} found)
                  </Typography>

                  {(result.result as any).method && (
                    <Chip
                      label={(result.result as any).method === 'advanced_vad' ? 'Advanced VAD' : 'FFmpeg Silencedetect'}
                      size="small"
                      color="primary"
                      sx={{ mb: 2 }}
                    />
                  )}

                  <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400, overflowX: 'auto' }}>
                    <Table size="small" stickyHeader sx={{ minWidth: { xs: 400, sm: 'auto' } }}>
                      <TableBody>
                        <TableRow>
                          <TableCell component="th" sx={{ fontWeight: 600, bgcolor: '#f8fafc', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>ID</TableCell>
                          <TableCell component="th" sx={{ fontWeight: 600, bgcolor: '#f8fafc', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>Start</TableCell>
                          <TableCell component="th" sx={{ fontWeight: 600, bgcolor: '#f8fafc', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>End</TableCell>
                          <TableCell component="th" sx={{ fontWeight: 600, bgcolor: '#f8fafc', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>Duration</TableCell>
                          {result.result.type === 'speech_segments' && (
                            <TableCell component="th" sx={{ fontWeight: 600, bgcolor: '#f8fafc', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>Confidence</TableCell>
                          )}
                        </TableRow>
                        {((result.result as any).segments || []).map((segment: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>{segment.id || index + 1}</TableCell>
                            <TableCell>{segment.start_formatted || segment.start}</TableCell>
                            <TableCell>{segment.end_formatted || segment.end}</TableCell>
                            <TableCell>{segment.duration}s</TableCell>
                            {(result.result as any).type === 'speech_segments' && segment.confidence && (
                              <TableCell>{(segment.confidence * 100).toFixed(1)}%</TableCell>
                            )}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {result.result.parameters && (
                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle2">Detection Parameters</Typography>
                      </AccordionSummary>
                      <AccordionDetails sx={{ px: { xs: 1, sm: 2 } }}>
                        <TableContainer sx={{ overflowX: 'auto' }}>
                          <Table size="small">
                            <TableBody>
                              {Object.entries(result.result.parameters).map(([key, value]) => (
                                <TableRow key={key}>
                                  <TableCell component="th" sx={{ fontWeight: 600, width: '40%', fontSize: { xs: '0.75rem', sm: '0.875rem' }, wordBreak: 'break-word' }}>
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </TableCell>
                                  <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{String(value)}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>
                  )}
                </Box>
              )}

              {/* Audio Analysis Results */}
              {(result.result.audio_quality || result.result.recommended_volume_threshold) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                    Audio Analysis Results
                  </Typography>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    {result.result.audio_quality && (
                      <Grid item xs={6} md={3}>
                        <Chip
                          label={`Quality: ${String(result.result.audio_quality).toUpperCase()}`}
                          color={
                            result.result.audio_quality === 'high' ? 'success' :
                              result.result.audio_quality === 'medium' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </Grid>
                    )}
                    {result.result.recommended_volume_threshold && (
                      <Grid item xs={6} md={3}>
                        <Chip
                          label={`Recommended Threshold: ${result.result.recommended_volume_threshold}%`}
                          color="primary"
                          size="small"
                        />
                      </Grid>
                    )}
                    {result.result.dynamic_range_db && (
                      <Grid item xs={6} md={3}>
                        <Chip
                          label={`Dynamic Range: ${result.result.dynamic_range_db}dB`}
                          color="info"
                          size="small"
                        />
                      </Grid>
                    )}
                    {result.result.duration && (
                      <Grid item xs={6} md={3}>
                        <Chip
                          label={`Duration: ${result.result.duration}s`}
                          variant="outlined"
                          size="small"
                        />
                      </Grid>
                    )}
                  </Grid>

                  <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
                    <Table size="small">
                      <TableBody>
                        {Object.entries(result.result)
                          .filter(([key]) => !['audio_quality', 'recommended_volume_threshold'].includes(key))
                          .map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell component="th" scope="row" sx={{ fontWeight: 600, width: '40%', fontSize: { xs: '0.75rem', sm: '0.875rem' }, wordBreak: 'break-word' }}>
                                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </TableCell>
                              <TableCell sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, wordBreak: 'break-all' }}>
                                {typeof value === 'number' ?
                                  (key.includes('_db') ? `${value}dB` :
                                    key.includes('_hz') ? `${value}Hz` :
                                      key.includes('_khz') ? `${value}kHz` :
                                        key.includes('rate') && !key.includes('_db') ? `${value}Hz` :
                                          value) :
                                  String(value)}
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {/* Supported Formats Display */}
              {result.result.supported_formats && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">Supported Formats</Typography>
                  </AccordionSummary>
                  <AccordionDetails sx={{ px: { xs: 1, sm: 2 } }}>
                    <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                      {Object.entries(result.result.supported_formats).map(([category, formats]: [string, SupportedFormats[string]]) => (
                        <Grid item xs={12} sm={6} md={4} key={category}>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {Object.keys(formats).map((format) => (
                              <Chip key={format} label={format} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
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
    supportedFormats
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
          Media Tools
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '1rem', sm: '1.1rem' },
            lineHeight: 1.5
          }}
        >
          Download enhanced media, capture webpage screenshots, convert formats, analyze audio, and extract transcripts.
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
            <Tab icon={<DownloadIcon />} label="Media Download" />
            <Tab icon={<UploadIcon />} label="File Upload" />
            <Tab icon={<ScreenshotIcon />} label="Web Screenshots" />
            <Tab icon={<ConvertIcon />} label="Format Conversion" />
            <Tab icon={<MetadataIcon />} label="Metadata Extraction" />
            <Tab icon={<YouTubeIcon />} label="YouTube Transcripts" />
            <Tab icon={<SilenceIcon />} label="Silence Detection" />
            <Tab icon={<AnalysisIcon />} label="Audio Analysis" />
          </Tabs>
        </Box>

        <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
          <TabPanel value={tabValue} index={0}>
            <MediaDownloadTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <FileUploadTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <WebScreenshotsTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <FormatConversionTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={4}>
            <MetadataExtractionTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={5}>
            <YouTubeTranscriptsTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={6}>
            <SilenceDetectionTab ctx={ctx} />
          </TabPanel>
          <TabPanel value={tabValue} index={7}>
            <AudioAnalysisTab ctx={ctx} />
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default MediaTools;
