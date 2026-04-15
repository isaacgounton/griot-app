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
  Search as SearchIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const WebSearchTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, renderJobResult } = ctx;

  const [webSearchForm, setWebSearchForm] = useState({
    query: '',
    engine: 'perplexity',
    maxResults: 10
  });

  const handleWebSearch = async () => {
    if (!webSearchForm.query.trim()) {
      setErrors(prev => ({ ...prev, websearch: 'Search query is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, websearch: true }));
    setErrors(prev => ({ ...prev, websearch: null }));
    setResults(prev => ({ ...prev, websearch: null }));

    try {
      const response = await directApi.post('/research/web', {
        query: webSearchForm.query,
        engine: webSearchForm.engine,
        max_results: webSearchForm.maxResults
      });

      if (response.data && (response.data.articles || response.data.results)) {
        setResults(prev => ({
          ...prev,
          websearch: {
            job_id: 'direct',
            result: response.data,
            status: 'completed'
          }
        }));
        setLoading(prev => ({ ...prev, websearch: false }));
      } else {
        setErrors(prev => ({ ...prev, websearch: 'No results found' }));
        setLoading(prev => ({ ...prev, websearch: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, websearch: errorMessage }));
      setLoading(prev => ({ ...prev, websearch: false }));
    }
  };

  return (
    <>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <SearchIcon color="primary" />
                Web Search
              </Typography>

              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Search Query"
                    placeholder="Search anything on the web..."
                    value={webSearchForm.query}
                    onChange={(e) => setWebSearchForm({ ...webSearchForm, query: e.target.value })}
                    helperText="Enter any search query to find information from the web"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Search Engine</InputLabel>
                    <Select
                      value={webSearchForm.engine}
                      label="Search Engine"
                      onChange={(e) => setWebSearchForm({ ...webSearchForm, engine: e.target.value })}
                    >
                      <MenuItem value="perplexity">Perplexity AI</MenuItem>
                      <MenuItem value="google">Google Search</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Results"
                    value={webSearchForm.maxResults}
                    onChange={(e) => setWebSearchForm({ ...webSearchForm, maxResults: parseInt(e.target.value) })}
                    inputProps={{ min: 1, max: 50 }}
                  />
                </Grid>
              </Grid>

              <Button
                variant="contained"
                size="large"
                startIcon={loading.websearch ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleWebSearch}
                disabled={loading.websearch || !webSearchForm.query.trim()}
                sx={{ mt: 3, px: 4 }}
              >
                {loading.websearch ? 'Searching...' : 'Search Web'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Search Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label="Multiple Engines" variant="outlined" size="small" />
                <Chip label="Perplexity AI" variant="outlined" size="small" />
                <Chip label="Google Search" variant="outlined" size="small" />
                <Chip label="Real-time Results" variant="outlined" size="small" />
                <Chip label="Web Sources" variant="outlined" size="small" />
                <Chip label="Search Anything" variant="outlined" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {renderJobResult('websearch', results.websearch, <SearchIcon />)}
    </>
  );
};

export default WebSearchTab;
