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
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  VolumeOff as SilenceIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const SilenceDetectionTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [silenceForm, setSilenceForm] = useState({
    media_url: '',
    use_advanced_vad: true,
    volume_threshold: 40.0,
    min_speech_duration: 0.5,
    speech_padding_ms: 50,
    silence_padding_ms: 450,
    noise: '-30dB',
    duration: 0.5,
    mono: false,
    start: '',
    end: ''
  });

  const handleSilenceDetection = async () => {
    if (!silenceForm.media_url.trim()) {
      setErrors(prev => ({ ...prev, silence: 'Media URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, silence: true }));
    setErrors(prev => ({ ...prev, silence: null }));
    setResults(prev => ({ ...prev, silence: null }));

    try {
      const response = await directApi.post('/media/silence/', silenceForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'silence');
      } else {
        setErrors(prev => ({ ...prev, silence: 'Failed to create silence detection job' }));
        setLoading(prev => ({ ...prev, silence: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, silence: errorMessage }));
      setLoading(prev => ({ ...prev, silence: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <SilenceIcon color="primary" />
              Detect Speech & Silence
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://example.com/audio.mp3"
                  value={silenceForm.media_url}
                  onChange={(e) => setSilenceForm({ ...silenceForm, media_url: e.target.value })}
                  helperText="URL of the audio/video file to analyze"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Detection Method</InputLabel>
                  <Select
                    value={silenceForm.use_advanced_vad ? 'advanced' : 'basic'}
                    label="Detection Method"
                    onChange={(e) => setSilenceForm({
                      ...silenceForm,
                      use_advanced_vad: e.target.value === 'advanced'
                    })}
                  >
                    <MenuItem value="advanced">Advanced VAD (Speech Segments)</MenuItem>
                    <MenuItem value="basic">Basic FFmpeg (Silence Intervals)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {silenceForm.use_advanced_vad ? (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Volume Threshold (%)"
                      value={silenceForm.volume_threshold}
                      onChange={(e) => setSilenceForm({
                        ...silenceForm,
                        volume_threshold: parseFloat(e.target.value)
                      })}
                      helperText="Threshold for speech detection (0-100)"
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Min Speech Duration (s)"
                      value={silenceForm.min_speech_duration}
                      onChange={(e) => setSilenceForm({
                        ...silenceForm,
                        min_speech_duration: parseFloat(e.target.value)
                      })}
                      helperText="Minimum duration for valid speech segment"
                      inputProps={{ min: 0.1, step: 0.1 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Speech Padding (ms)"
                      value={silenceForm.speech_padding_ms}
                      onChange={(e) => setSilenceForm({
                        ...silenceForm,
                        speech_padding_ms: parseInt(e.target.value)
                      })}
                      helperText="Padding around speech segments"
                      inputProps={{ min: 0, step: 10 }}
                    />
                  </Grid>
                </>
              ) : (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Noise Threshold"
                      value={silenceForm.noise}
                      onChange={(e) => setSilenceForm({ ...silenceForm, noise: e.target.value })}
                      helperText="FFmpeg noise threshold (e.g., -30dB)"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Min Duration (s)"
                      value={silenceForm.duration}
                      onChange={(e) => setSilenceForm({
                        ...silenceForm,
                        duration: parseFloat(e.target.value)
                      })}
                      helperText="Minimum silence duration"
                      inputProps={{ min: 0.1, step: 0.1 }}
                    />
                  </Grid>
                </>
              )}

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Start Time (Optional)"
                  placeholder="00:01:30"
                  value={silenceForm.start}
                  onChange={(e) => setSilenceForm({ ...silenceForm, start: e.target.value })}
                  helperText="HH:MM:SS format"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="End Time (Optional)"
                  placeholder="00:05:00"
                  value={silenceForm.end}
                  onChange={(e) => setSilenceForm({ ...silenceForm, end: e.target.value })}
                  helperText="HH:MM:SS format"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.silence ? <CircularProgress size={20} /> : <SilenceIcon />}
              onClick={handleSilenceDetection}
              disabled={loading.silence || !silenceForm.media_url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.silence ? 'Analyzing...' : 'Detect Speech/Silence'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('silence', results.silence, <SilenceIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Detection Methods
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Choose the best method for your needs:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Advanced VAD</Typography>
                    <Typography variant="caption">&#8226; ML-based speech detection</Typography><br />
                    <Typography variant="caption">&#8226; More accurate boundaries</Typography><br />
                    <Typography variant="caption">&#8226; Returns speech segments</Typography>
                  </Box>
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Basic FFmpeg</Typography>
                    <Typography variant="caption">&#8226; Fast silence detection</Typography><br />
                    <Typography variant="caption">&#8226; Traditional threshold-based</Typography><br />
                    <Typography variant="caption">&#8226; Returns silence intervals</Typography>
                  </Box>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default SilenceDetectionTab;
