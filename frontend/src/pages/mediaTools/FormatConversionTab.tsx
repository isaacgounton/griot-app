import React, { useState } from 'react';
import {
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
  Transform as ConvertIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const FormatConversionTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult, supportedFormats } = ctx;

  const [conversionForm, setConversionForm] = useState({
    input_url: '',
    output_format: 'mp3',
    quality: 'medium',
    custom_options: ''
  });

  const handleConversion = async () => {
    if (!conversionForm.input_url.trim()) {
      setErrors(prev => ({ ...prev, conversion: 'URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, conversion: true }));
    setErrors(prev => ({ ...prev, conversion: null }));
    setResults(prev => ({ ...prev, conversion: null }));

    try {
      const response = await directApi.post('/media/conversions/', conversionForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'conversion');
      } else {
        setErrors(prev => ({ ...prev, conversion: 'Failed to create conversion job' }));
        setLoading(prev => ({ ...prev, conversion: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, conversion: errorMessage }));
      setLoading(prev => ({ ...prev, conversion: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <ConvertIcon color="primary" />
              Convert Media Format
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://example.com/video.mp4"
                  value={conversionForm.input_url}
                  onChange={(e) => setConversionForm({ ...conversionForm, input_url: e.target.value })}
                  helperText="URL of the media file to convert"
                />
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Output Format</InputLabel>
                  <Select
                    value={conversionForm.output_format}
                    label="Output Format"
                    onChange={(e) => setConversionForm({ ...conversionForm, output_format: e.target.value })}
                  >
                    <MenuItem value="mp3">MP3 (Audio)</MenuItem>
                    <MenuItem value="wav">WAV (Audio)</MenuItem>
                    <MenuItem value="mp4">MP4 (Video)</MenuItem>
                    <MenuItem value="webm">WebM (Video)</MenuItem>
                    <MenuItem value="avi">AVI (Video)</MenuItem>
                    <MenuItem value="mov">MOV (Video)</MenuItem>
                    <MenuItem value="jpg">JPEG (Image)</MenuItem>
                    <MenuItem value="png">PNG (Image)</MenuItem>
                    <MenuItem value="webp">WebP (Image)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <FormControl fullWidth>
                  <InputLabel>Quality</InputLabel>
                  <Select
                    value={conversionForm.quality}
                    label="Quality"
                    onChange={(e) => setConversionForm({ ...conversionForm, quality: e.target.value })}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="lossless">Lossless</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} lg={4}>
                <TextField
                  fullWidth
                  label="Custom Options"
                  placeholder="-vf scale=1280:-1"
                  value={conversionForm.custom_options}
                  onChange={(e) => setConversionForm({ ...conversionForm, custom_options: e.target.value })}
                  helperText="FFmpeg options"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.conversion ? <CircularProgress size={20} /> : <ConvertIcon />}
              onClick={handleConversion}
              disabled={loading.conversion || !conversionForm.input_url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.conversion ? 'Converting...' : 'Convert Media'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('conversion', results.conversion, <ConvertIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Conversion Info
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Convert between 50+ media formats using FFmpeg.
                </Typography>
                {supportedFormats && (
                  <Typography variant="caption" color="text.secondary">
                    {supportedFormats.total_formats} formats supported
                  </Typography>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default FormatConversionTab;
