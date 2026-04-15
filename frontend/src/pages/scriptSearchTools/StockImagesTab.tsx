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
  ImageSearch as ImageSearchIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const StockImagesTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [stockImageForm, setStockImageForm] = useState({
    query: '',
    provider: 'pexels',
    limit: 20,
    category: 'all',
    orientation: 'all',
    size: 'all'
  });

  const handleStockImageSearch = async () => {
    if (!stockImageForm.query.trim()) {
      setErrors(prev => ({ ...prev, stockimages: 'Search query is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, stockimages: true }));
    setErrors(prev => ({ ...prev, stockimages: null }));
    setResults(prev => ({ ...prev, stockimages: null }));

    try {
      const response = await directApi.searchStockImages({
        query: stockImageForm.query,
        provider: stockImageForm.provider as 'pexels' | 'pixabay',
        per_page: stockImageForm.limit,
        orientation: stockImageForm.orientation === 'all' ? undefined :
          (stockImageForm.orientation === 'horizontal' ? 'landscape' :
            stockImageForm.orientation === 'vertical' ? 'portrait' :
              stockImageForm.orientation as 'landscape' | 'portrait' | 'square'),
        size: stockImageForm.size === 'all' ? undefined : stockImageForm.size as 'large' | 'medium' | 'small'
      });

      if (response.data && response.data.job_id) {
        setResults(prev => ({ ...prev, stockimages: { job_id: response.data!.job_id, status: 'pending', result: undefined } }));
        pollJobStatus(response.data.job_id, 'stockimages');
      } else {
        setErrors(prev => ({ ...prev, stockimages: 'Failed to create image search job' }));
        setLoading(prev => ({ ...prev, stockimages: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, stockimages: errorMessage }));
      setLoading(prev => ({ ...prev, stockimages: false }));
    }
  };

  return (
    <>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ImageSearchIcon color="primary" />
                Search Stock Images
              </Typography>

              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Search Query"
                    placeholder="Enter keywords to search for images..."
                    value={stockImageForm.query}
                    onChange={(e) => setStockImageForm({ ...stockImageForm, query: e.target.value })}
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={stockImageForm.provider}
                      label="Provider"
                      onChange={(e) => setStockImageForm({ ...stockImageForm, provider: e.target.value })}
                    >
                      <MenuItem value="pexels">Pexels</MenuItem>
                      <MenuItem value="pixabay">Pixabay</MenuItem>
                    </Select>
                  </FormControl>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Category</InputLabel>
                        <Select
                          value={stockImageForm.category}
                          label="Category"
                          onChange={(e) => setStockImageForm({ ...stockImageForm, category: e.target.value })}
                        >
                          <MenuItem value="all">All Categories</MenuItem>
                          <MenuItem value="backgrounds">Backgrounds</MenuItem>
                          <MenuItem value="fashion">Fashion</MenuItem>
                          <MenuItem value="nature">Nature</MenuItem>
                          <MenuItem value="science">Science</MenuItem>
                          <MenuItem value="education">Education</MenuItem>
                          <MenuItem value="people">People</MenuItem>
                          <MenuItem value="places">Places</MenuItem>
                          <MenuItem value="animals">Animals</MenuItem>
                          <MenuItem value="food">Food</MenuItem>
                          <MenuItem value="sports">Sports</MenuItem>
                          <MenuItem value="travel">Travel</MenuItem>
                          <MenuItem value="business">Business</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Orientation</InputLabel>
                        <Select
                          value={stockImageForm.orientation}
                          label="Orientation"
                          onChange={(e) => setStockImageForm({ ...stockImageForm, orientation: e.target.value })}
                        >
                          <MenuItem value="all">All Orientations</MenuItem>
                          <MenuItem value="horizontal">Horizontal</MenuItem>
                          <MenuItem value="vertical">Vertical</MenuItem>
                          <MenuItem value="square">Square</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Size</InputLabel>
                        <Select
                          value={stockImageForm.size}
                          label="Size"
                          onChange={(e) => setStockImageForm({ ...stockImageForm, size: e.target.value })}
                        >
                          <MenuItem value="all">All Sizes</MenuItem>
                          <MenuItem value="large">Large</MenuItem>
                          <MenuItem value="medium">Medium</MenuItem>
                          <MenuItem value="small">Small</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Number of Results"
                        value={stockImageForm.limit}
                        onChange={(e) => setStockImageForm({ ...stockImageForm, limit: parseInt(e.target.value) || 20 })}
                        inputProps={{ min: 1, max: 200 }}
                      />
                    </Grid>
                  </Grid>

                  <Button
                    variant="contained"
                    size="large"
                    startIcon={loading.stockimages ? <CircularProgress size={20} /> : <ImageSearchIcon />}
                    onClick={handleStockImageSearch}
                    disabled={loading.stockimages || !stockImageForm.query.trim()}
                    sx={{ px: 4 }}
                  >
                    {loading.stockimages ? 'Searching...' : 'Search Images'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Search Tips
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label="Pexels Photos" variant="outlined" size="small" />
                <Chip label="Pixabay Images" variant="outlined" size="small" />
                <Chip label="Category Filters" variant="outlined" size="small" />
                <Chip label="Orientation Filter" variant="outlined" size="small" />
                <Chip label="Free to Use" variant="outlined" size="small" />
                <Chip label="High Resolution" variant="outlined" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {renderJobResult('stockimages', results.stockimages, <ImageSearchIcon />)}
    </>
  );
};

export default StockImagesTab;
