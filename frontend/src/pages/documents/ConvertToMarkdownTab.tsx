import React, { useState } from 'react';
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
  LinearProgress,
  FormControlLabel,
  Switch,
  Chip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Link as LinkIcon,
  Description as DocumentIcon,
  PictureAsPdf as PdfIcon,
  Article as WordIcon,
  TableChart as ExcelIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface ConvertToMarkdownTabProps {
  ctx: TabContext;
}

const ConvertToMarkdownTab: React.FC<ConvertToMarkdownTabProps> = ({ ctx }) => {
  const {
    loading, setLoading,
    result, setResult,
    error, setError,
    jobStatus, setJobStatus,
    jobProgress,
    pollingJobId, setPollingJobId,
    pollJobStatus,
    copyToClipboard,
    downloadMarkdown,
    getFileIcon,
  } = ctx;

  // Local form state
  const [urlForm, setUrlForm] = useState({
    url: '',
    includeMetadata: true,
    preserveFormatting: true
  });

  const [fileForm, setFileForm] = useState({
    file: null as File | null,
    includeMetadata: true,
    preserveFormatting: true
  });

  const handleUrlSubmit = async () => {
    if (!urlForm.url.trim()) {
      setError('Document URL is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.convertUrlToMarkdown(urlForm.url, {
        includeMetadata: urlForm.includeMetadata,
        preserveFormatting: urlForm.preserveFormatting
      });

      if (response.success && response.data) {
        setResult({ job_id: response.data.job_id, status: 'pending' });
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        pollJobStatus(response.data.job_id);
      } else {
        setError(response.error || 'Failed to start document conversion');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async () => {
    if (!fileForm.file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.convertFileToMarkdown(fileForm.file, {
        includeMetadata: fileForm.includeMetadata,
        preserveFormatting: fileForm.preserveFormatting
      });

      if (response.success && response.data) {
        setResult({ job_id: response.data.job_id, status: 'pending' });
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        pollJobStatus(response.data.job_id);
      } else {
        setError(response.error || 'Failed to start document conversion');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFileForm(prev => ({ ...prev, file }));
    }
  };

  const renderDocumentJobResult = () => {
    if (!result && !error && !jobStatus) return null;

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          Document Conversion
          {jobStatus && jobStatus !== 'completed' && (
            <CircularProgress size={16} sx={{ ml: 1 }} />
          )}
        </Typography>

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

        {error && (
          <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>
            {error}
          </Alert>
        )}

        {result && jobStatus === 'completed' && result.result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
              Document converted successfully!
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Document Info:
              </Typography>
              <Paper sx={{ p: 1.5, bgcolor: '#f8fafc' }}>
                <Grid container spacing={1} sx={{ fontSize: '0.7rem' }}>
                  {result.result.original_filename && (
                    <Grid item xs={6}>
                      <strong>File:</strong> {result.result.original_filename.slice(0, 15)}...
                    </Grid>
                  )}
                  {result.result.word_count && (
                    <Grid item xs={6}>
                      <strong>Words:</strong> {result.result.word_count}
                    </Grid>
                  )}
                  {result.result.file_type && (
                    <Grid item xs={6}>
                      <strong>Type:</strong> {result.result.file_type}
                    </Grid>
                  )}
                  {result.result.processing_time && (
                    <Grid item xs={6}>
                      <strong>Time:</strong> {result.result.processing_time.toFixed(1)}s
                    </Grid>
                  )}
                </Grid>
              </Paper>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Preview:
              </Typography>
              <Paper sx={{
                p: 1.5,
                bgcolor: '#f0f9ff',
                maxHeight: 150,
                overflow: 'auto',
                fontSize: '0.75rem'
              }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {result.result.markdown_content?.slice(0, 200)}
                  {result.result.markdown_content?.length > 200 && '...'}
                </Typography>
              </Paper>
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => copyToClipboard(result.result?.markdown_content || '')}
                  sx={{ fontSize: '0.7rem', px: 1 }}
                >
                  Copy
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => downloadMarkdown(
                    result.result?.markdown_content || '',
                    `${result.result?.original_filename || 'document'}.md`
                  )}
                  sx={{ fontSize: '0.7rem', px: 1 }}
                >
                  Download
                </Button>
              </Box>
            </Box>
          </Box>
        )}

        {result && !result.result && jobStatus !== 'completed' && (
          <Box>
            <Alert severity="info" sx={{ mb: 2, fontSize: '0.75rem' }}>
              Document conversion job created successfully!
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

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Convert Document to Markdown
            </Typography>

            <Grid container spacing={3}>
              {/* URL Input */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Document URL (Optional)"
                  placeholder="https://example.com/document.pdf"
                  value={urlForm.url}
                  onChange={(e) => setUrlForm(prev => ({ ...prev, url: e.target.value }))}
                  helperText="Enter a URL to convert a document from the web"
                />
              </Grid>

              {/* Divider */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, my: 1 }}>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                    OR
                  </Typography>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                </Box>
              </Grid>

              {/* File Upload */}
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  component="label"
                  fullWidth
                  startIcon={<UploadIcon />}
                  sx={{ mb: 2, py: 2 }}
                >
                  {fileForm.file ? fileForm.file.name : 'Choose File to Upload'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.txt,.html,.htm"
                    onChange={handleFileChange}
                  />
                </Button>
                {fileForm.file && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    {getFileIcon(fileForm.file.name)}
                    <Typography variant="body2">
                      {fileForm.file.name} ({(fileForm.file.size / 1024 / 1024).toFixed(2)} MB)
                    </Typography>
                  </Box>
                )}
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  Supported formats: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, TXT, HTML
                </Typography>
              </Grid>

              {/* Settings */}
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={urlForm.includeMetadata}
                      onChange={(e) => {
                        setUrlForm(prev => ({ ...prev, includeMetadata: e.target.checked }));
                        setFileForm(prev => ({ ...prev, includeMetadata: e.target.checked }));
                      }}
                    />
                  }
                  label="Include Metadata"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={urlForm.preserveFormatting}
                      onChange={(e) => {
                        setUrlForm(prev => ({ ...prev, preserveFormatting: e.target.checked }));
                        setFileForm(prev => ({ ...prev, preserveFormatting: e.target.checked }));
                      }}
                    />
                  }
                  label="Preserve Formatting"
                />
              </Grid>

              {/* Convert Button */}
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> :
                    (fileForm.file ? <UploadIcon /> : <LinkIcon />)}
                  onClick={fileForm.file ? handleFileSubmit : handleUrlSubmit}
                  disabled={loading || (!urlForm.url.trim() && !fileForm.file)}
                  sx={{ px: 4 }}
                >
                  {loading ? 'Converting...' :
                    fileForm.file ? 'Upload & Convert' : 'Convert from URL'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            {renderDocumentJobResult() || (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Quick Examples
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Try these example documents:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setUrlForm(prev => ({ ...prev, url: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf' }))}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Sample PDF
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setUrlForm(prev => ({ ...prev, url: 'https://file-examples.com/wp-content/storage/2017/02/file-sample_100kB.docx' }))}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Sample DOCX
                  </Button>
                </Box>

                <Typography variant="h6" sx={{ mb: 2 }}>
                  Supported Formats
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<PdfIcon />} label="PDF" color="error" variant="outlined" size="small" />
                  <Chip icon={<WordIcon />} label="Word (DOCX/DOC)" color="primary" variant="outlined" size="small" />
                  <Chip icon={<ExcelIcon />} label="Excel (XLSX/XLS)" color="success" variant="outlined" size="small" />
                  <Chip icon={<DocumentIcon />} label="PowerPoint" color="secondary" variant="outlined" size="small" />
                  <Chip icon={<CodeIcon />} label="Text/HTML" color="info" variant="outlined" size="small" />
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default ConvertToMarkdownTab;
