import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  GraphicEq as VadIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const VoiceDetectionTab: React.FC<Props> = ({ ctx }) => {
  const { error, setError } = ctx;

  const [vadFile, setVadFile] = useState<File | null>(null);
  const [vadResults, setVadResults] = useState<Array<{ start: number; end: number }>>([]);
  const [vadLoading, setVadLoading] = useState(false);
  const [vadAudioUrl, setVadAudioUrl] = useState<string | null>(null);

  const handleVadSubmit = async () => {
    if (!vadFile) return;
    setVadLoading(true);
    setVadResults([]);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', vadFile);
      const resp = await directApi.post('/speaches/vad', formData);
      const data = resp.data;
      setVadResults(Array.isArray(data) ? data : data?.timestamps || data?.segments || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'VAD analysis failed';
      setError(errorMessage);
    } finally {
      setVadLoading(false);
    }
  };

  const formatVadTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(2);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <VadIcon color="primary" />
              Voice Activity Detection
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload an audio file to detect speech segments with precise timestamps.
            </Typography>

            <Box
              sx={{
                border: '2px dashed',
                borderColor: 'divider',
                borderRadius: 2,
                p: { xs: 2, sm: 4 },
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                mb: 3,
                '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
              }}
              onClick={() => document.getElementById('vad-file-input')?.click()}
            >
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body1" fontWeight={500}>
                {vadFile ? vadFile.name : 'Click to upload audio file'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supports WAV, MP3, FLAC, OGG, M4A
              </Typography>
              <input
                id="vad-file-input"
                type="file"
                accept="audio/*"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setVadFile(file);
                    setVadResults([]);
                    if (vadAudioUrl) URL.revokeObjectURL(vadAudioUrl);
                    setVadAudioUrl(URL.createObjectURL(file));
                  }
                }}
              />
            </Box>

            {vadFile && vadAudioUrl && (
              <Box sx={{ mb: 3 }}>
                <audio controls src={vadAudioUrl} style={{ width: '100%' }} />
              </Box>
            )}

            <Button
              variant="contained"
              size="large"
              startIcon={vadLoading ? <CircularProgress size={20} color="inherit" /> : <VadIcon />}
              onClick={handleVadSubmit}
              disabled={!vadFile || vadLoading}
              sx={{ maxWidth: { sm: '300px' } }}
            >
              {vadLoading ? 'Analyzing...' : 'Detect Speech'}
            </Button>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
            )}

            {vadResults.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  Detected Speech Segments ({vadResults.length})
                </Typography>

                {/* Timeline visualization */}
                <Box sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      position: 'relative',
                      height: 40,
                      bgcolor: 'action.hover',
                      borderRadius: 1,
                      overflow: 'hidden',
                      border: '1px solid',
                      borderColor: 'divider'
                    }}
                  >
                    {(() => {
                      const maxEnd = Math.max(...vadResults.map(s => s.end), 1);
                      return vadResults.map((segment, idx) => (
                        <Box
                          key={idx}
                          title={`${formatVadTime(segment.start)} - ${formatVadTime(segment.end)}`}
                          sx={{
                            position: 'absolute',
                            left: `${(segment.start / maxEnd) * 100}%`,
                            width: `${Math.max(((segment.end - segment.start) / maxEnd) * 100, 0.5)}%`,
                            height: '100%',
                            bgcolor: 'primary.main',
                            opacity: 0.6,
                            borderRadius: 0.5,
                            minWidth: 2,
                            '&:hover': { opacity: 1 }
                          }}
                        />
                      ));
                    })()}
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">0s</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatVadTime(Math.max(...vadResults.map(s => s.end), 0))}
                    </Typography>
                  </Box>
                </Box>

                {/* Segments table */}
                <Paper variant="outlined" sx={{ borderRadius: 2 }}>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          <th style={{ padding: '8px 16px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: '0.875rem' }}>#</th>
                          <th style={{ padding: '8px 16px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: '0.875rem' }}>Start</th>
                          <th style={{ padding: '8px 16px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: '0.875rem' }}>End</th>
                          <th style={{ padding: '8px 16px', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: '0.875rem' }}>Duration</th>
                        </tr>
                      </thead>
                      <tbody>
                        {vadResults.map((segment, idx) => (
                          <tr key={idx}>
                            <td style={{ padding: '6px 16px', borderBottom: '1px solid #f1f5f9', fontSize: '0.875rem' }}>{idx + 1}</td>
                            <td style={{ padding: '6px 16px', borderBottom: '1px solid #f1f5f9', fontSize: '0.875rem' }}>{formatVadTime(segment.start)}</td>
                            <td style={{ padding: '6px 16px', borderBottom: '1px solid #f1f5f9', fontSize: '0.875rem' }}>{formatVadTime(segment.end)}</td>
                            <td style={{ padding: '6px 16px', borderBottom: '1px solid #f1f5f9', fontSize: '0.875rem' }}>{formatVadTime(segment.end - segment.start)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Box>
                </Paper>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              About VAD
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Voice Activity Detection identifies when someone is speaking in an audio file.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="subtitle2" color="primary">Use Cases</Typography>
                <Typography variant="body2" color="text.secondary">
                  Trim silence from recordings, detect speaker turns, pre-process audio before transcription.
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="primary">Output</Typography>
                <Typography variant="body2" color="text.secondary">
                  Precise start/end timestamps for each detected speech segment with visual timeline.
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default VoiceDetectionTab;
