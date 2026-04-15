import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Paper,
  LinearProgress,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  AutoAwesome as GenerateIcon,
  Edit as EditIcon,
  Preview as PreviewIcon,
  Download as DownloadIcon,
  PhotoCamera as FluxIcon,
  AutoFixHigh as EnhanceIcon,
  VideoLibrary as LibraryIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabPanelProps, JobResult, TabContext } from './types';

import GenerateImagesTab from './GenerateImagesTab';
import OverlayEditingTab from './OverlayEditingTab';
import AIImageEditingTab from './AIImageEditingTab';
import ImageEnhancementTab from './ImageEnhancementTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`images-tabpanel-${index}`}
      aria-labelledby={`images-tab-${index}`}
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

const Images: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<'pending' | 'processing' | 'completed' | 'failed' | null>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [previewDialog, setPreviewDialog] = useState(false);

  // Job status polling function
  const pollJobStatus = async (jobId: string) => {
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
          setJobProgress('Image processing completed successfully!');
          setResult({ job_id: jobId, result: jobResult, status: 'completed' });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Image processing failed');
          setError(jobError || 'Image processing failed');
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
        console.error('Error polling job status:', err);
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

  // Job status polling function for Pollinations AI
  const pollJobStatusPollinations = async (jobId: string) => {
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

        setJobStatus(status as 'pending' | 'processing' | 'completed' | 'failed');

        if (status === 'completed') {
          setJobProgress('Image generation completed successfully!');
          setResult({
            job_id: jobId,
            result: {
              image_url: jobResult?.image_url || jobResult?.content_url || jobResult?.url,
              content_url: jobResult?.image_url || jobResult?.content_url || jobResult?.url,
              content_type: jobResult?.content_type,
              file_size: jobResult?.file_size,
              generation_time: jobResult?.generation_time,
              model_used: jobResult?.model_used,
              prompt_used: jobResult?.prompt,
              dimensions: { width: jobResult?.width || 1024, height: jobResult?.height || 1024 },
              width: jobResult?.width,
              height: jobResult?.height
            },
            status: 'completed'
          });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Image generation failed');
          setError(jobError || 'Image generation failed');
          setLoading(false);
          return;
        } else if (status === 'processing') {
          setJobProgress(`Processing with Pollinations AI... (${attempts}/${maxAttempts})`);
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
        console.error('Error polling Pollinations AI job status:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setError('Failed to check Pollinations AI job status');
          setLoading(false);
        }
      }
    };

    poll();
  };

  // Render job result in sidebar
  const renderJobResult = (tabIndex: number, resultData: JobResult | null, icon: React.ReactNode) => {
    if (!resultData && !error && !jobStatus) return null;

    const tabTitles = [
      'Image Generation',
      'Overlay Editing',
      'AI Image Editing',
      'Image Enhancement'
    ];

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          {icon}
          {tabTitles[tabIndex]} Result
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
        {resultData && jobStatus === 'completed' && resultData.result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
              {tabTitles[tabIndex]} completed successfully!
            </Alert>

            {/* Image Generation/Edit Preview */}
            {!resultData.result.images && (resultData.result.image_url || resultData.result.edited_image_url) && (
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {resultData.result.edited_image_url ? 'Edited Image' : 'Generated Image'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column' }}>
                    <Button
                      startIcon={<PreviewIcon />}
                      onClick={() => setPreviewDialog(true)}
                      variant="outlined"
                      size="small"
                      fullWidth
                    >
                      Preview
                    </Button>
                    {(resultData.result.edited_image_url || resultData.result.image_url) && (
                      <Button
                        startIcon={<DownloadIcon />}
                        href={resultData.result.edited_image_url || resultData.result.image_url || '#'}
                        component="a"
                        target="_blank"
                        variant="contained"
                        size="small"
                        fullWidth
                      >
                        Download
                      </Button>
                    )}
                    <Button
                      startIcon={<LibraryIcon />}
                      onClick={() => navigate('/dashboard/library')}
                      variant="outlined"
                      size="small"
                      color="primary"
                      fullWidth
                    >
                      Library
                    </Button>
                  </Box>
                </Box>

                <Paper sx={{ p: 2, bgcolor: '#f8fafc', textAlign: 'center' }}>
                  <img
                    src={resultData.result.edited_image_url || resultData.result.image_url}
                    alt={resultData.result.edited_image_url ? "Edited result" : "Generated result"}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '300px',
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                    }}
                  />
                </Paper>

                {/* Show original image for editing results */}
                {resultData.result.original_image_url && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Original Image:</Typography>
                    <Paper sx={{ p: 2, bgcolor: '#f8fafc', textAlign: 'center' }}>
                      <img
                        src={resultData.result.original_image_url}
                        alt="Original image"
                        style={{
                          maxWidth: '100%',
                          maxHeight: '150px',
                          borderRadius: '8px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                        }}
                      />
                    </Paper>
                  </Box>
                )}
              </Box>
            )}

            {/* Stock Image Search Results */}
            {resultData.result.images && Array.isArray(resultData.result.images) && resultData.result.images.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                  Found {resultData.result.images.length} Images
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {resultData.result.images.slice(0, 3).map((image, index) => (
                    <Box key={image.id || index}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2">
                          {image.photographer ? `by ${image.photographer}` : 'Stock Image'}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            startIcon={<PreviewIcon />}
                            href={image.url}
                            target="_blank"
                            size="small"
                            variant="outlined"
                          >
                            View
                          </Button>
                          <Button
                            startIcon={<DownloadIcon />}
                            href={image.download_url}
                            target="_blank"
                            size="small"
                            variant="contained"
                          >
                            Download
                          </Button>
                        </Box>
                      </Box>
                      <Paper sx={{ p: 1, bgcolor: '#f8fafc', textAlign: 'center' }}>
                        <img
                          src={image.url}
                          alt={image.alt || 'Stock image'}
                          style={{
                            maxWidth: '100%',
                            maxHeight: '150px',
                            borderRadius: '4px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                          }}
                        />
                      </Paper>
                    </Box>
                  ))}
                  {resultData.result.images.length > 3 && (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                      And {resultData.result.images.length - 3} more images...
                    </Typography>
                  )}
                </Box>
              </Box>
            )}

            {/* Processing Details */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.75rem' }}>Details:</Typography>
              <Paper sx={{ p: 2, bgcolor: '#f8fafc', fontSize: '0.75rem' }}>
                {/* Image generation/editing details */}
                {!resultData.result.images && (
                  <>
                    {resultData.result.prompt_used && (
                      <Box sx={{ mb: 1 }}>
                        <strong>Prompt:</strong> {resultData.result.prompt_used.substring(0, 60)}...
                      </Box>
                    )}
                    {resultData.result.model_used && (
                      <Box sx={{ mb: 1 }}>
                        <strong>Model:</strong> {resultData.result.model_used}
                      </Box>
                    )}
                    {resultData.result.dimensions && (
                      <Box sx={{ mb: 1 }}>
                        <strong>Size:</strong> {resultData.result.dimensions.width} x {resultData.result.dimensions.height}
                      </Box>
                    )}
                    {resultData.result.processing_time && (
                      <Box>
                        <strong>Time:</strong> {resultData.result.processing_time.toFixed(1)}s
                      </Box>
                    )}
                  </>
                )}

                {/* Search details */}
                {resultData.result.images && (
                  <>
                    {resultData.result.query_used && (
                      <Box sx={{ mb: 1 }}>
                        <strong>Query:</strong> {resultData.result.query_used}
                      </Box>
                    )}
                    {resultData.result.provider_used && (
                      <Box sx={{ mb: 1 }}>
                        <strong>Provider:</strong> {resultData.result.provider_used.charAt(0).toUpperCase() + resultData.result.provider_used.slice(1)}
                      </Box>
                    )}
                    {resultData.result.total_results && (
                      <Box>
                        <strong>Total Results:</strong> {resultData.result.total_results}
                      </Box>
                    )}
                  </>
                )}
              </Paper>
            </Box>
          </Box>
        )}

        {/* Initial Job Created Message */}
        {resultData && !resultData.result && jobStatus !== 'completed' && (
          <Box>
            <Alert severity="info" sx={{ mb: 2, fontSize: '0.75rem' }}>
              {tabTitles[tabIndex]} job created successfully!
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              Job ID: <code style={{ padding: '1px 3px', backgroundColor: '#f1f3f4', borderRadius: '2px', fontSize: '0.7rem' }}>
                {resultData.job_id}
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
    previewDialog, setPreviewDialog,
    pollJobStatus,
    pollJobStatusPollinations,
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
          AI Image Tools
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '1rem', sm: '1.1rem' },
            lineHeight: 1.5
          }}
        >
          Generate stunning images from text prompts or edit existing images with precise overlay controls.
        </Typography>
      </Box>

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: { xs: 2, sm: 3 } }}>
        <Tabs
          value={activeTab}
          onChange={(_e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' },
              minWidth: { xs: 80, sm: 120 },
              py: { xs: 0.75, sm: 1.5 },
              px: { xs: 1, sm: 2 }
            }
          }}
        >
          <Tab
            icon={<GenerateIcon />}
            label="Generate Images"
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />
          <Tab
            icon={<EditIcon />}
            label="Overlay Editing"
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />
          <Tab
            icon={<FluxIcon />}
            label="AI Image Editing"
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />
          <Tab
            icon={<EnhanceIcon />}
            label="Image Enhancement"
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={activeTab} index={0}>
        <GenerateImagesTab ctx={ctx} />
      </TabPanel>
      <TabPanel value={activeTab} index={1}>
        <OverlayEditingTab ctx={ctx} />
      </TabPanel>
      <TabPanel value={activeTab} index={2}>
        <AIImageEditingTab ctx={ctx} />
      </TabPanel>
      <TabPanel value={activeTab} index={3}>
        <ImageEnhancementTab ctx={ctx} />
      </TabPanel>

      {/* Full Size Preview Dialog */}
      <Dialog
        open={previewDialog}
        onClose={() => setPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Image Preview</DialogTitle>
        <DialogContent>
          {(result?.result?.image_url || result?.result?.edited_image_url) && (
            <img
              src={result.result.edited_image_url || result.result.image_url}
              alt="Full size preview"
              style={{
                width: '100%',
                height: 'auto',
                borderRadius: '8px'
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
          {(result?.result?.image_url || result?.result?.edited_image_url) && (
            <Button
              href={result.result.edited_image_url || result.result.image_url || '#'}
              component="a"
              target="_blank"
              variant="contained"
              startIcon={<DownloadIcon />}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Images;
