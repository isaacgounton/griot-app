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
  YouTube as YouTubeIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const YouTubeTranscriptsTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [transcriptForm, setTranscriptForm] = useState({
    video_url: '',
    translate_to: ''
  });

  const handleTranscript = async () => {
    if (!transcriptForm.video_url.trim()) {
      setErrors(prev => ({ ...prev, transcript: 'URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, transcript: true }));
    setErrors(prev => ({ ...prev, transcript: null }));
    setResults(prev => ({ ...prev, transcript: null }));

    try {
      const response = await directApi.post('/media/youtube-transcripts', transcriptForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'transcript');
      } else {
        setErrors(prev => ({ ...prev, transcript: 'Failed to create transcript job' }));
        setLoading(prev => ({ ...prev, transcript: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, transcript: errorMessage }));
      setLoading(prev => ({ ...prev, transcript: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <YouTubeIcon color="primary" />
              Extract YouTube Transcripts
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="YouTube URL"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={transcriptForm.video_url}
                  onChange={(e) => setTranscriptForm({ ...transcriptForm, video_url: e.target.value })}
                  helperText="YouTube video URL to extract transcript from"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Translate To (Optional)"
                  placeholder="en, es, fr, de, etc."
                  value={transcriptForm.translate_to}
                  onChange={(e) => setTranscriptForm({ ...transcriptForm, translate_to: e.target.value })}
                  helperText="Language code for translation"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.transcript ? <CircularProgress size={20} /> : <YouTubeIcon />}
              onClick={handleTranscript}
              disabled={loading.transcript || !transcriptForm.video_url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.transcript ? 'Extracting...' : 'Extract Transcript'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('transcript', results.transcript, <YouTubeIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Transcript Features
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Extract existing captions and subtitles from YouTube videos.
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="caption">&#8226; Multiple language support</Typography>
                  <Typography variant="caption">&#8226; Auto-generated captions</Typography>
                  <Typography variant="caption">&#8226; Translation capabilities</Typography>
                  <Typography variant="caption">&#8226; Clean text output</Typography>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default YouTubeTranscriptsTab;
