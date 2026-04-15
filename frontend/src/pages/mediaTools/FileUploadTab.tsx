import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Chip,
  Alert,
  LinearProgress,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Image as ImageIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  Delete as DeleteIcon,
  Storage as StorageIcon,
  DriveFileRenameOutline as RenameIcon,
  DragIndicator as DragIcon,
  Security as SecurityIcon,
  ContentCopy as CopyIcon,
  OpenInNew as OpenIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const FileUploadTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, errors, setErrors, results, setResults, jobStatuses, pollJobStatus } = ctx;

  const toolName = 'upload';

  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    file_name: ''
  });

  const [dragActive, setDragActive] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      setErrors(prev => ({ ...prev, [toolName]: 'File is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, [toolName]: true }));
    setErrors(prev => ({ ...prev, [toolName]: null }));
    setResults(prev => ({ ...prev, [toolName]: null }));

    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      if (uploadForm.file_name.trim()) {
        formData.append('file_name', uploadForm.file_name);
      }
      formData.append('public', 'true');

      const response = await directApi.post('/s3/upload', formData);

      if (response.data && response.data.job_id) {
        setResults(prev => ({ ...prev, [toolName]: { job_id: response.data.job_id, status: 'pending' } }));
        pollJobStatus(response.data.job_id, toolName);
      } else {
        setErrors(prev => ({ ...prev, [toolName]: 'Failed to create upload job' }));
        setLoading(prev => ({ ...prev, [toolName]: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, [toolName]: errorMessage }));
      setLoading(prev => ({ ...prev, [toolName]: false }));
    }
  };

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
      setUploadForm({ file, file_name: file.name });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadForm({ file, file_name: file.name });
    }
  };

  const clearFile = () => {
    setUploadForm({ file: null, file_name: '' });
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
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <UploadIcon color="primary" />
              File Upload
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
              onClick={() => document.getElementById('upload-tab-file-input')?.click()}
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
                id="upload-tab-file-input"
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
                          {formatFileSize(uploadForm.file.size)} &bull; {uploadForm.file.type || 'Unknown type'}
                        </Typography>
                      </Box>
                    </Box>
                    <Button size="small" startIcon={<DeleteIcon />} onClick={clearFile} color="error">
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
              startIcon={loading[toolName] ? <CircularProgress size={20} /> : <UploadIcon />}
              onClick={handleUpload}
              disabled={loading[toolName] || !uploadForm.file}
              sx={{ px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading[toolName] ? 'Uploading...' : 'Upload File'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {/* Upload result with copyable URL */}
            {(loading[toolName] || errors[toolName] || results[toolName]) ? (
              <Box>
                <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  <UploadIcon />
                  Upload Result
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

                {results[toolName] && jobStatuses[toolName] === 'completed' && results[toolName]?.result && (
                  <Box>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      File uploaded successfully!
                    </Alert>

                    {results[toolName]?.result?.file_url && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                          File URL:
                        </Typography>
                        <Paper sx={{ p: 1.5, bgcolor: '#f8fafc', display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              wordBreak: 'break-all',
                              fontFamily: 'monospace',
                              fontSize: '0.8rem',
                              flex: 1
                            }}
                          >
                            {results[toolName]?.result?.file_url}
                          </Typography>
                          <Tooltip title={copied ? 'Copied!' : 'Copy URL'}>
                            <IconButton
                              size="small"
                              onClick={() => handleCopyUrl(String(results[toolName]?.result?.file_url))}
                              color={copied ? 'success' : 'default'}
                            >
                              <CopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Open in new tab">
                            <IconButton
                              size="small"
                              href={String(results[toolName]?.result?.file_url)}
                              target="_blank"
                              component="a"
                            >
                              <OpenIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Paper>
                      </Box>
                    )}
                  </Box>
                )}
              </Box>
            ) : (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Features
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<DragIcon />} label="Drag & Drop" variant="outlined" />
                  <Chip icon={<StorageIcon />} label="S3 Cloud Storage" variant="outlined" />
                  <Chip icon={<RenameIcon />} label="Custom File Naming" variant="outlined" />
                  <Chip icon={<ImageIcon />} label="Images" variant="outlined" />
                  <Chip icon={<VideoIcon />} label="Videos" variant="outlined" />
                  <Chip icon={<AudioIcon />} label="Audio Files" variant="outlined" />
                  <Chip icon={<FileIcon />} label="Documents" variant="outlined" />
                  <Chip icon={<SecurityIcon />} label="Secure Upload" variant="outlined" />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Upload any file type directly to S3 storage with public URL generation.
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default FileUploadTab;
