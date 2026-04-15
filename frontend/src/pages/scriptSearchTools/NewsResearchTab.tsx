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
  MenuItem,
  Chip
} from '@mui/material';
import {
  Newspaper as NewsIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const NewsResearchTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [newsResearchForm, setNewsResearchForm] = useState({
    searchTerm: '',
    targetLanguage: 'en',
    maxResults: 5
  });

  const handleNewsResearch = async () => {
    if (!newsResearchForm.searchTerm.trim()) {
      setErrors(prev => ({ ...prev, news: 'Search term is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, news: true }));
    setErrors(prev => ({ ...prev, news: null }));
    setResults(prev => ({ ...prev, news: null }));

    try {
      const response = await directApi.post('/ai/news-research', newsResearchForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'news');
      } else {
        setErrors(prev => ({ ...prev, news: 'Failed to create news research job' }));
        setLoading(prev => ({ ...prev, news: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, news: errorMessage }));
      setLoading(prev => ({ ...prev, news: false }));
    }
  };

  return (
    <>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <NewsIcon color="primary" />
                News Research
              </Typography>

              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Search Term"
                    placeholder="artificial intelligence, climate change, technology trends..."
                    value={newsResearchForm.searchTerm}
                    onChange={(e) => setNewsResearchForm({ ...newsResearchForm, searchTerm: e.target.value })}
                    helperText="Enter topics to research current news and trends"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={newsResearchForm.targetLanguage}
                      label="Language"
                      onChange={(e) => setNewsResearchForm({ ...newsResearchForm, targetLanguage: e.target.value })}
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="es">Spanish</MenuItem>
                      <MenuItem value="fr">French</MenuItem>
                      <MenuItem value="de">German</MenuItem>
                      <MenuItem value="it">Italian</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Results"
                    value={newsResearchForm.maxResults}
                    onChange={(e) => setNewsResearchForm({ ...newsResearchForm, maxResults: parseInt(e.target.value) })}
                    inputProps={{ min: 1, max: 20 }}
                  />
                </Grid>
              </Grid>

              <Button
                variant="contained"
                size="large"
                startIcon={loading.news ? <CircularProgress size={20} /> : <NewsIcon />}
                onClick={handleNewsResearch}
                disabled={loading.news || !newsResearchForm.searchTerm.trim()}
                sx={{ mt: 3, px: 4 }}
              >
                {loading.news ? 'Researching...' : 'Research News'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Research Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label="Real-time News" variant="outlined" size="small" />
                <Chip label="Multiple Sources" variant="outlined" size="small" />
                <Chip label="Content Ideas" variant="outlined" size="small" />
                <Chip label="Trending Topics" variant="outlined" size="small" />
                <Chip label="Multi-language" variant="outlined" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {renderJobResult('news', results.news, <NewsIcon />)}
    </>
  );
};

export default NewsResearchTab;
