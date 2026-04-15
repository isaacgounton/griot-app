import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress
} from '@mui/material';
import {
  Analytics as AnalysisIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const AudioAnalysisTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [analysisForm, setAnalysisForm] = useState({
    media_url: ''
  });

  const handleAudioAnalysis = async () => {
    if (!analysisForm.media_url.trim()) {
      setErrors(prev => ({ ...prev, analysis: 'Media URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, analysis: true }));
    setErrors(prev => ({ ...prev, analysis: null }));
    setResults(prev => ({ ...prev, analysis: null }));

    try {
      const response = await directApi.post('/media/silence/analyze', analysisForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'analysis');
      } else {
        setErrors(prev => ({ ...prev, analysis: 'Failed to create audio analysis job' }));
        setLoading(prev => ({ ...prev, analysis: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, analysis: errorMessage }));
      setLoading(prev => ({ ...prev, analysis: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <AnalysisIcon color="primary" />
              Analyze Audio Characteristics
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://example.com/audio.mp3"
                  value={analysisForm.media_url}
                  onChange={(e) => setAnalysisForm({ ...analysisForm, media_url: e.target.value })}
                  helperText="URL of the audio file to analyze for optimal parameters"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.analysis ? <CircularProgress size={20} /> : <AnalysisIcon />}
              onClick={handleAudioAnalysis}
              disabled={loading.analysis || !analysisForm.media_url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.analysis ? 'Analyzing...' : 'Analyze Audio'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('analysis', results.analysis, <AnalysisIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Analysis Features
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Get insights to optimize your audio processing:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="caption">&#8226; Recommended volume threshold</Typography>
                  <Typography variant="caption">&#8226; Dynamic range analysis</Typography>
                  <Typography variant="caption">&#8226; Audio quality assessment</Typography>
                  <Typography variant="caption">&#8226; Noise floor detection</Typography>
                  <Typography variant="caption">&#8226; Speech level analysis</Typography>
                  <Typography variant="caption">&#8226; Spectral characteristics</Typography>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default AudioAnalysisTab;
