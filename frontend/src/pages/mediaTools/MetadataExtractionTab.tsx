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
  Info as MetadataIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const MetadataExtractionTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [metadataForm, setMetadataForm] = useState({
    media_url: ''
  });

  const handleMetadata = async () => {
    if (!metadataForm.media_url.trim()) {
      setErrors(prev => ({ ...prev, metadata: 'Media URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, metadata: true }));
    setErrors(prev => ({ ...prev, metadata: null }));
    setResults(prev => ({ ...prev, metadata: null }));

    try {
      const response = await directApi.post('/media/metadata', metadataForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'metadata');
      } else {
        setErrors(prev => ({ ...prev, metadata: 'Failed to create metadata job' }));
        setLoading(prev => ({ ...prev, metadata: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, metadata: errorMessage }));
      setLoading(prev => ({ ...prev, metadata: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <MetadataIcon color="primary" />
              Extract Media Metadata
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://example.com/video.mp4"
                  value={metadataForm.media_url}
                  onChange={(e) => setMetadataForm({ ...metadataForm, media_url: e.target.value })}
                  helperText="URL of the media file to analyze"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.metadata ? <CircularProgress size={20} /> : <MetadataIcon />}
              onClick={handleMetadata}
              disabled={loading.metadata || !metadataForm.media_url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.metadata ? 'Analyzing...' : 'Extract Metadata'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('metadata', results.metadata, <MetadataIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Metadata Info
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Extracts comprehensive information including:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="caption">&#8226; Duration & file size</Typography>
                  <Typography variant="caption">&#8226; Video resolution & codec</Typography>
                  <Typography variant="caption">&#8226; Audio channels & bitrate</Typography>
                  <Typography variant="caption">&#8226; Format & technical details</Typography>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default MetadataExtractionTab;
