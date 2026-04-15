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
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  // AttachFile as AttachFileIcon,
  CheckCircle as CheckIcon,
  Description as FileIcon,
  Image as ImageIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { directApi } from '../utils/api';

interface JobResult {
  job_id: string;
  status?: string;
  result?: {
    file_url?: string;
    [key: string]: string | number | boolean | undefined;
  };
  error?: string | null;
}

const Upload: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [jobProgress, setJobProgress] = useState<string>('');

  // Form state
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    file_name: ''
  });

  const [dragActive, setDragActive] = useState(false);

  // Job status polling function
  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const statusResponse = await directApi.getJobStatus(jobId);

        const job = statusResponse.data!;
        const status = job.status;
        const jobResult = job.result;
        const jobError = job.error;

        setJobStatus(status);

        if (status === 'completed') {
          setJobProgress('File uploaded successfully!');
          setResult({ job_id: jobId, result: jobResult, status: 'completed' });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Upload failed');
          setError(jobError || 'Upload failed');
          setLoading(false);
          return;
        } else if (status === 'processing') {
          setJobProgress(`Uploading file... (${attempts}/${maxAttempts})`);
        } else {
          setJobProgress(`Queued... (${attempts}/${maxAttempts})`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds for uploads
        } else {
          setError('Job polling timeout. Please check status manually.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setError('Failed to check job status');
          setLoading(false);
        }
      }
    };

    poll();
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      setError('File is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setJobStatus('');
    setJobProgress('');

    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      if (uploadForm.file_name.trim()) {
        formData.append('file_name', uploadForm.file_name);
      }
      formData.append('public', 'true');

      const response = await directApi.post('/s3/upload', formData);

      if (response.data && response.data.job_id) {
        setResult(response.data);
        setJobStatus('pending');
        setJobProgress('Upload job created, starting file upload...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to create upload job');
        setLoading(false);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setLoading(false);
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setUploadForm({
        file,
        file_name: file.name
      });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadForm({
        file,
        file_name: file.name
      });
    }
  };

  const clearFile = () => {
    setUploadForm({
      file: null,
      file_name: ''
    });
  };

  const renderJobResult = () => {
    if (!result && !loading && !error && !jobStatus) return null;

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          📁 Upload Result
          {loading && <CircularProgress size={20} sx={{ ml: 1 }} />}
        </Typography>

        {/* Job Status */}
        {jobStatus && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Job ID: {result?.job_id}
            </Typography>
            <LinearProgress
              variant={jobStatus === 'completed' ? 'determinate' : 'indeterminate'}
              value={jobStatus === 'completed' ? 100 : undefined}
              sx={{ mb: 1, height: 6, borderRadius: 3 }}
            />
            <Typography variant="body2" sx={{
              color: jobStatus === 'completed' ? 'success.main' :
                jobStatus === 'failed' ? 'error.main' : 'info.main'
            }}>
              {jobProgress}
            </Typography>
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Success Results */}
        {result && jobStatus === 'completed' && result.result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2 }}>
              🎉 File uploaded successfully!
            </Alert>

            {result.result.file_url && (
              <Box sx={{ mb: 2 }}>
                <Button
                  startIcon={<DownloadIcon />}
                  href={result.result.file_url}
                  target="_blank"
                  variant="contained"
                  size="small"
                  fullWidth
                >
                  View Uploaded File
                </Button>
              </Box>
            )}

            {/* File URL Display */}
            <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                File URL:
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  wordBreak: 'break-all',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }}
              >
                {result.result.file_url}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* Initial Job Created Message */}
        {result && !result.result && jobStatus !== 'completed' && (
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              Upload job created successfully!
            </Alert>
            <Typography variant="body2" color="text.secondary">
              Job ID: <code style={{ padding: '2px 4px', backgroundColor: '#f1f3f4', borderRadius: '3px' }}>
                {result.job_id}
              </code>
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  const getFileIcon = (file: File) => {
    const type = file.type.toLowerCase();
    if (type.startsWith('image/')) return <ImageIcon />;
    if (type.startsWith('video/')) return <VideoIcon />;
    if (type.startsWith('audio/')) return <AudioIcon />;
    return <FileIcon />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      pb: 8
    }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 4 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            color: '#1a202c',
            fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
          }}
        >
          File Upload 📁
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '0.95rem', sm: '1.1rem' } }}
        >
          Upload files to your S3 storage with drag-and-drop support.
        </Typography>
      </Box>

      {/* Main Upload Form */}
      <Paper elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3 }}>
        <Box sx={{ p: { xs: 2, sm: 3 } }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <UploadIcon color="primary" />
                    Upload File to S3
                  </Typography>

                  {/* Drag and Drop Area */}
                  <Box
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    sx={{
                      border: `2px dashed ${dragActive ? '#1976d2' : '#e0e0e0'}`,
                      borderRadius: 2,
                      p: { xs: 2, sm: 4 },
                      textAlign: 'center',
                      backgroundColor: dragActive ? '#f3f7ff' : '#fafafa',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      mb: 3,
                      '&:hover': {
                        borderColor: '#1976d2',
                        backgroundColor: '#f3f7ff'
                      }
                    }}
                    onClick={() => document.getElementById('file-input')?.click()}
                  >
                    <UploadIcon
                      sx={{
                        fontSize: 48,
                        color: dragActive ? '#1976d2' : '#9e9e9e',
                        mb: 2
                      }}
                    />
                    <Typography variant="h6" sx={{ mb: 1, color: dragActive ? '#1976d2' : 'text.primary' }}>
                      {dragActive ? 'Drop your file here' : 'Drag and drop your file here'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      or click to browse files
                    </Typography>
                    <input
                      id="file-input"
                      type="file"
                      hidden
                      onChange={handleFileSelect}
                    />
                  </Box>

                  {/* Selected File Display */}
                  {uploadForm.file && (
                    <Card variant="outlined" sx={{ mb: 3, bgcolor: '#f8fafc' }}>
                      <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            {getFileIcon(uploadForm.file)}
                            <Box>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {uploadForm.file.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {formatFileSize(uploadForm.file.size)} • {uploadForm.file.type || 'Unknown type'}
                              </Typography>
                            </Box>
                          </Box>
                          <Button
                            size="small"
                            startIcon={<DeleteIcon />}
                            onClick={clearFile}
                            color="error"
                          >
                            Remove
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Custom File Name */}
                  <TextField
                    fullWidth
                    label="Custom File Name (Optional)"
                    placeholder="custom-name.jpg"
                    value={uploadForm.file_name}
                    onChange={(e) => setUploadForm({ ...uploadForm, file_name: e.target.value })}
                    helperText="Leave empty to use original file name"
                    sx={{ mb: 3 }}
                  />

                  <Button
                    variant="contained"
                    size="large"
                    startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
                    onClick={handleUpload}
                    disabled={loading || !uploadForm.file}
                    sx={{ px: 4 }}
                  >
                    {loading ? 'Uploading...' : 'Upload File'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
                <CardContent>
                  {renderJobResult() || (
                    <>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Upload Features
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary="Drag & Drop"
                            secondary="Easy file selection"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary="S3 Storage"
                            secondary="Secure cloud storage"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary="Custom Naming"
                            secondary="Rename files on upload"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary="All File Types"
                            secondary="Images, videos, documents"
                          />
                        </ListItem>
                      </List>

                      <Divider sx={{ my: 2 }} />

                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Supported Types:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        <Chip icon={<ImageIcon />} label="Images" size="small" variant="outlined" />
                        <Chip icon={<VideoIcon />} label="Videos" size="small" variant="outlined" />
                        <Chip icon={<AudioIcon />} label="Audio" size="small" variant="outlined" />
                        <Chip icon={<FileIcon />} label="Documents" size="small" variant="outlined" />
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Box>
  );
};

export default Upload;