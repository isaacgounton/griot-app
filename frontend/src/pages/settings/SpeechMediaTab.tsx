import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Chip,
  useTheme,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Snackbar,
  alpha,
  Divider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Mic as MicIcon,
  RecordVoiceOver as VoiceIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  GraphicEq as TtsIcon,
  Dns as ServiceIcon,
  Collections as StockIcon,
  AutoAwesome as AiGenIcon,
  Videocam as VideoIcon,
  Memory as ModelIcon,
} from '@mui/icons-material';
import ConfigSettingField from './ConfigSettingField';
import { useConfigSettings } from './useConfigSettings';
import { apiClient } from '../../utils/api';

interface SpeachesModel {
  id: string;
  object?: string;
  created?: number;
  owned_by?: string;
}

// Each section maps to a Card with icon-branded header
const SECTIONS = [
  {
    title: 'TTS Defaults',
    description: 'Default text-to-speech provider and voice',
    icon: <TtsIcon />,
    color: 'primary' as const,
    keys: ['TTS_PROVIDER', 'TTS_VOICE'],
  },
  {
    title: 'Speaches Service',
    description: 'Self-hosted TTS/STT engine connection',
    icon: <ServiceIcon />,
    color: 'info' as const,
    keys: ['SPEACHES_BASE_URL', 'SPEACHES_API_KEY'],
  },
  {
    title: 'Stock Media',
    description: 'Pexels and Pixabay API access for stock footage',
    icon: <StockIcon />,
    color: 'secondary' as const,
    keys: ['PEXELS_API_KEY', 'PIXABAY_API_KEY'],
  },
  {
    title: 'Together AI — Image Generation',
    description: 'Image generation model, defaults, and rate limiting',
    icon: <AiGenIcon />,
    color: 'warning' as const,
    keys: [
      'TOGETHER_DEFAULT_MODEL', 'TOGETHER_DEFAULT_WIDTH', 'TOGETHER_DEFAULT_HEIGHT',
      'TOGETHER_DEFAULT_STEPS', 'TOGETHER_MODELS', 'TOGETHER_MAX_RPS',
      'TOGETHER_MAX_CONCURRENT', 'TOGETHER_RETRY_ATTEMPTS', 'TOGETHER_BASE_DELAY',
    ],
  },
  {
    title: 'ComfyUI',
    description: 'Custom workflow-based image and video generation',
    icon: <VideoIcon />,
    color: 'info' as const,
    keys: ['COMFYUI_URL', 'COMFYUI_API_KEY', 'COMFYUI_USERNAME', 'COMFYUI_PASSWORD'],
  },
  {
    title: 'WaveSpeed AI',
    description: 'AI video generation service',
    icon: <SpeedIcon />,
    color: 'primary' as const,
    keys: ['WAVESPEEDAI_API_KEY'],
  },
  {
    title: 'Modal — Image & Video',
    description: 'Serverless GPU inference for media generation',
    icon: <AiGenIcon />,
    color: 'secondary' as const,
    keys: ['MODAL_IMAGE_API_KEY', 'MODAL_IMAGE_API_URL', 'MODAL_VIDEO_API_KEY', 'MODAL_VIDEO_API_URL'],
  },
];

const SpeechMediaTab: React.FC = () => {
  const theme = useTheme();
  const {
    editValues, loading, saving, error, success,
    setValue, saveCategory, getSettingsForCategory,
  } = useConfigSettings();

  // Speaches model management
  const [healthStatus, setHealthStatus] = useState<boolean | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [models, setModels] = useState<SpeachesModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
  const [modelToDownload, setModelToDownload] = useState('');
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false, message: '', severity: 'info',
  });

  const showNotification = (message: string, severity: 'success' | 'error' | 'info' = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const checkHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      const resp = await apiClient.get('/speaches/health');
      setHealthStatus(resp.data?.healthy === true || resp.data?.status === 'ok' || resp.status === 200);
    } catch {
      setHealthStatus(false);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  const fetchModels = useCallback(async () => {
    setModelsLoading(true);
    try {
      const resp = await apiClient.get('/speaches/models');
      const data = resp.data;
      setModels(Array.isArray(data) ? data : data?.data || data?.models || []);
    } catch {
      // silent
    } finally {
      setModelsLoading(false);
    }
  }, []);

  const handleDownloadModel = async () => {
    if (!modelToDownload.trim()) return;
    setDownloadLoading(true);
    try {
      await apiClient.post(`/speaches/models/${encodeURIComponent(modelToDownload)}`);
      showNotification(`Model "${modelToDownload}" download started`, 'success');
      setDownloadDialogOpen(false);
      setModelToDownload('');
      setTimeout(fetchModels, 3000);
    } catch {
      showNotification('Failed to download model', 'error');
    } finally {
      setDownloadLoading(false);
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    setDeleteLoading(modelId);
    try {
      await apiClient.delete(`/speaches/models/${encodeURIComponent(modelId)}`);
      showNotification(`Model "${modelId}" deleted`, 'success');
      fetchModels();
    } catch {
      showNotification('Failed to delete model', 'error');
    } finally {
      setDeleteLoading(null);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchModels();
  }, [checkHealth, fetchModels]);

  const settings = getSettingsForCategory('speech_media');

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  return (
    <Box>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="body2" color="text.secondary">
          TTS/STT, stock media, and image/video generation services.
        </Typography>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveCategory('speech_media')} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Config sections in Cards */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 3 }}>
        {SECTIONS.map((section) => {
          const visibleKeys = section.keys.filter((k) => k in settings);
          if (visibleKeys.length === 0) return null;
          const themeColor = theme.palette[section.color].main;

          return (
            <Card elevation={1} key={section.title}>
              <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(themeColor, 0.1), color: themeColor }}>
                    {section.icon}
                  </Box>
                  <Box>
                    <Typography variant="h6" fontWeight="medium">{section.title}</Typography>
                    <Typography variant="body2" color="text.secondary">{section.description}</Typography>
                  </Box>
                </Box>
                <Grid container spacing={1.5}>
                  {visibleKeys.map((key) => (
                    <Grid item xs={12} sm={6} md={visibleKeys.length <= 2 ? 6 : 4} key={key}>
                      <ConfigSettingField
                        settingKey={key}
                        setting={settings[key]}
                        value={editValues[key] ?? settings[key].value}
                        onChange={setValue}
                      />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          );
        })}
      </Box>

      {/* Speaches Model Management */}
      <Card elevation={1}>
        <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(theme.palette.warning.main, 0.1), color: theme.palette.warning.main }}>
              <ModelIcon />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Typography variant="h6" fontWeight="medium">Speaches Models</Typography>
                <Chip
                  icon={healthLoading ? <CircularProgress size={14} /> : healthStatus ? <HealthyIcon /> : <ErrorIcon />}
                  label={healthLoading ? 'Checking...' : healthStatus ? 'Online' : 'Offline'}
                  color={healthStatus ? 'success' : healthStatus === false ? 'error' : 'default'}
                  variant="outlined" size="small" sx={{ fontWeight: 600 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">Manage loaded TTS and STT models</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Refresh health"><IconButton onClick={checkHealth} size="small"><RefreshIcon fontSize="small" /></IconButton></Tooltip>
              <Button variant="contained" size="small" startIcon={<DownloadIcon />} onClick={() => setDownloadDialogOpen(true)}>
                Download
              </Button>
              <Button variant="outlined" size="small" startIcon={<RefreshIcon />} onClick={fetchModels} disabled={modelsLoading}>
                Refresh
              </Button>
            </Box>
          </Box>

          {healthStatus === false && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Speaches service is offline. TTS/STT features require this Docker sidecar.
            </Alert>
          )}

          {/* Models table */}
          <Paper variant="outlined" sx={{ borderRadius: 1.5, mb: 2 }}>
            {modelsLoading ? (
              <Box sx={{ py: 3 }}><LinearProgress /></Box>
            ) : models.length === 0 ? (
              <Alert severity="info" sx={{ m: 2 }}>
                No models loaded. Try downloading "kokoro" for TTS or "Systran/faster-whisper-base" for STT.
              </Alert>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Model ID</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Owner</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {models.map((model) => {
                      const isTTS = model.id?.includes('kokoro') || model.id?.includes('piper');
                      const isSTT = model.id?.includes('whisper') || model.id?.includes('Systran');
                      return (
                        <TableRow key={model.id} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight={500} sx={{ fontFamily: 'monospace' }}>{model.id}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={isTTS ? 'TTS' : isSTT ? 'STT' : 'Other'} size="small" color={isTTS ? 'primary' : isSTT ? 'secondary' : 'default'} variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">{model.owned_by || 'unknown'}</Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Tooltip title="Delete model">
                              <IconButton size="small" color="error" onClick={() => handleDeleteModel(model.id)} disabled={deleteLoading === model.id}>
                                {deleteLoading === model.id ? <CircularProgress size={16} /> : <DeleteIcon />}
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>

          {/* Recommended models */}
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>Recommended Models</Typography>
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            {[
              { icon: <MicIcon fontSize="small" color="primary" />, name: 'Kokoro TTS', id: 'kokoro' },
              { icon: <VoiceIcon fontSize="small" color="secondary" />, name: 'Whisper Base', id: 'Systran/faster-whisper-base' },
              { icon: <SpeedIcon fontSize="small" color="info" />, name: 'Whisper Large V3', id: 'Systran/faster-whisper-large-v3' },
            ].map((m) => (
              <Chip
                key={m.id}
                icon={m.icon}
                label={`${m.name} — ${m.id}`}
                variant="outlined"
                size="small"
                sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Download dialog */}
      <Dialog open={downloadDialogOpen} onClose={() => setDownloadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Download Model</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter a model ID. Examples: "kokoro" for TTS, "Systran/faster-whisper-base" for STT.
          </Typography>
          <TextField fullWidth label="Model ID" placeholder="e.g., Systran/faster-whisper-base" value={modelToDownload} onChange={(e) => setModelToDownload(e.target.value)} autoFocus />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDownloadDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleDownloadModel} disabled={!modelToDownload.trim() || downloadLoading} startIcon={downloadLoading ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}>
            {downloadLoading ? 'Downloading...' : 'Download'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar(p => ({ ...p, open: false }))} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert onClose={() => setSnackbar(p => ({ ...p, open: false }))} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SpeechMediaTab;
