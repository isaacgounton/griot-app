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
  AutoAwesome as AIIcon,
  Search as SearchIcon,
  VideoLibrary as VideoIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const VideoSearchTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [videoSearchForm, setVideoSearchForm] = useState({
    topic: '',
    language: 'en',
    orientation: 'portrait',
    per_page: 15,
    page: 1
  });

  const [manualSearchForm, setManualSearchForm] = useState({
    query: '',
    provider: 'pexels',
    orientation: 'landscape',
    per_page: 15,
    page: 1
  });

  const handleVideoSearch = async () => {
    if (!videoSearchForm.topic.trim()) {
      setErrors(prev => ({ ...prev, videosearch: 'Topic is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, videosearch: true }));
    setErrors(prev => ({ ...prev, videosearch: null }));
    setResults(prev => ({ ...prev, videosearch: null }));

    try {
      // Smart Search Queries: Generate AI-powered search queries from topic
      const response = await directApi.post('/ai/video-search-queries', {
        script: videoSearchForm.topic,
        segment_duration: 3.0,
        provider: 'auto',
        language: videoSearchForm.language
      });
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'videosearch');
      } else {
        setErrors(prev => ({ ...prev, videosearch: 'Failed to create video search job' }));
        setLoading(prev => ({ ...prev, videosearch: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, videosearch: errorMessage }));
      setLoading(prev => ({ ...prev, videosearch: false }));
    }
  };

  const handleManualVideoSearch = async () => {
    if (!manualSearchForm.query.trim()) {
      setErrors(prev => ({ ...prev, manualsearch: 'Search query is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, manualsearch: true }));
    setErrors(prev => ({ ...prev, manualsearch: null }));
    setResults(prev => ({ ...prev, manualsearch: null }));

    try {
      // Manual Video Browse: Direct search without AI
      const response = await directApi.post('/ai/video-search/stock-videos', {
        query: manualSearchForm.query,
        orientation: manualSearchForm.orientation,
        per_page: manualSearchForm.per_page
      });
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'manualsearch');
      } else {
        setErrors(prev => ({ ...prev, manualsearch: 'Failed to create manual video search job' }));
        setLoading(prev => ({ ...prev, manualsearch: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, manualsearch: errorMessage }));
      setLoading(prev => ({ ...prev, manualsearch: false }));
    }
  };

  return (
    <>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          AI-Powered Video Search
        </Typography>

        <Grid container spacing={{ xs: 2, sm: 3 }}>
          <Grid item xs={12} md={6}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Smart Search Queries
                </Typography>

                <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Topic"
                      placeholder="AI and machine learning"
                      value={videoSearchForm.topic}
                      onChange={(e) => setVideoSearchForm({ ...videoSearchForm, topic: e.target.value })}
                      helperText="AI will generate optimized search queries"
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Orientation</InputLabel>
                      <Select
                        value={videoSearchForm.orientation}
                        label="Orientation"
                        onChange={(e) => setVideoSearchForm({ ...videoSearchForm, orientation: e.target.value })}
                      >
                        <MenuItem value="portrait">Portrait (9:16)</MenuItem>
                        <MenuItem value="landscape">Landscape (16:9)</MenuItem>
                        <MenuItem value="square">Square (1:1)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Language</InputLabel>
                      <Select
                        value={videoSearchForm.language}
                        label="Language"
                        onChange={(e) => setVideoSearchForm({ ...videoSearchForm, language: e.target.value })}
                      >
                        <MenuItem value="en">English</MenuItem>
                        <MenuItem value="es">Spanish</MenuItem>
                        <MenuItem value="fr">French</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading.videosearch ? <CircularProgress size={20} /> : <AIIcon />}
                  onClick={handleVideoSearch}
                  disabled={loading.videosearch || !videoSearchForm.topic.trim()}
                  sx={{ mt: 2, px: 3 }}
                >
                  {loading.videosearch ? 'Searching...' : 'Generate Search Queries'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Manual Video Browse
                </Typography>

                <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Search Query"
                      placeholder="technology, innovation, startup"
                      value={manualSearchForm.query}
                      onChange={(e) => setManualSearchForm({ ...manualSearchForm, query: e.target.value })}
                      helperText={`Direct search in ${manualSearchForm.provider.charAt(0).toUpperCase() + manualSearchForm.provider.slice(1)} database`}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Provider</InputLabel>
                      <Select
                        value={manualSearchForm.provider}
                        label="Provider"
                        onChange={(e) => setManualSearchForm({ ...manualSearchForm, provider: e.target.value })}
                      >
                        <MenuItem value="pexels">Pexels</MenuItem>
                        <MenuItem value="pixabay">Pixabay</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Orientation</InputLabel>
                      <Select
                        value={manualSearchForm.orientation}
                        label="Orientation"
                        onChange={(e) => setManualSearchForm({ ...manualSearchForm, orientation: e.target.value })}
                      >
                        <MenuItem value="landscape">Landscape</MenuItem>
                        <MenuItem value="portrait">Portrait</MenuItem>
                        <MenuItem value="square">Square</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Results Per Page"
                      value={manualSearchForm.per_page}
                      onChange={(e) => setManualSearchForm({ ...manualSearchForm, per_page: parseInt(e.target.value) })}
                      inputProps={{ min: 5, max: 80 }}
                    />
                  </Grid>
                </Grid>

                <Button
                  variant="outlined"
                  size="large"
                  startIcon={loading.manualsearch ? <CircularProgress size={20} /> : <SearchIcon />}
                  onClick={handleManualVideoSearch}
                  disabled={loading.manualsearch || !manualSearchForm.query.trim()}
                  sx={{ mt: 2, px: 3 }}
                >
                  {loading.manualsearch ? 'Searching...' : 'Browse Videos'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {renderJobResult('videosearch', results.videosearch, <SearchIcon />)}
      {renderJobResult('manualsearch', results.manualsearch, <VideoIcon />)}
    </>
  );
};

export default VideoSearchTab;
