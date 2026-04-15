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
  Chip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  ScreenshotMonitor as ScreenshotIcon,
  Image as ImageIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const WebScreenshotsTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [screenshotForm, setScreenshotForm] = useState({
    url: '',
    device_type: 'desktop',
    wait_time: 2000,
    full_page: false,
    css_inject: '',
    js_inject: '',
    format: 'png',
    quality: 80
  });

  const handleScreenshot = async () => {
    if (!screenshotForm.url.trim()) {
      setErrors(prev => ({ ...prev, screenshot: 'URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, screenshot: true }));
    setErrors(prev => ({ ...prev, screenshot: null }));
    setResults(prev => ({ ...prev, screenshot: null }));

    try {
      const response = await directApi.post('/web_screenshot/capture', screenshotForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'screenshot');
      } else {
        setErrors(prev => ({ ...prev, screenshot: 'Failed to create screenshot job' }));
        setLoading(prev => ({ ...prev, screenshot: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, screenshot: errorMessage }));
      setLoading(prev => ({ ...prev, screenshot: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <ScreenshotIcon color="primary" />
              Web Screenshots
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Webpage URL"
                  placeholder="https://example.com"
                  value={screenshotForm.url}
                  onChange={(e) => setScreenshotForm({ ...screenshotForm, url: e.target.value })}
                  helperText="URL of the webpage to capture"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Device Type</InputLabel>
                  <Select
                    value={screenshotForm.device_type}
                    label="Device Type"
                    onChange={(e) => setScreenshotForm({ ...screenshotForm, device_type: e.target.value })}
                  >
                    <MenuItem value="desktop">Desktop (1920x1080)</MenuItem>
                    <MenuItem value="mobile">Mobile (375x667)</MenuItem>
                    <MenuItem value="tablet">Tablet (768x1024)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Wait Time (ms)"
                  value={screenshotForm.wait_time}
                  onChange={(e) => setScreenshotForm({ ...screenshotForm, wait_time: parseInt(e.target.value) })}
                  helperText="Time to wait before capture (0-10000ms)"
                  inputProps={{ min: 0, max: 10000, step: 100 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Image Format</InputLabel>
                  <Select
                    value={screenshotForm.format}
                    label="Image Format"
                    onChange={(e) => setScreenshotForm({ ...screenshotForm, format: e.target.value })}
                  >
                    <MenuItem value="png">PNG (Best Quality)</MenuItem>
                    <MenuItem value="jpeg">JPEG (Smaller Size)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="CSS Injection (Optional)"
                  placeholder="body { background: red; } .hide { display: none; }"
                  value={screenshotForm.css_inject}
                  onChange={(e) => setScreenshotForm({ ...screenshotForm, css_inject: e.target.value })}
                  helperText="Inject custom CSS before capture (useful for hiding elements, custom styling)"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="JavaScript Injection (Optional)"
                  placeholder="document.querySelector('.popup').remove(); window.scrollTo(0, 500);"
                  value={screenshotForm.js_inject}
                  onChange={(e) => setScreenshotForm({ ...screenshotForm, js_inject: e.target.value })}
                  helperText="Execute JavaScript before capture (scrolling, removing elements, etc.)"
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={screenshotForm.full_page}
                      onChange={(e) => setScreenshotForm({ ...screenshotForm, full_page: e.target.checked })}
                      color="primary"
                    />
                  }
                  label="Capture Full Page (instead of viewport)"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.screenshot ? <CircularProgress size={20} /> : <ScreenshotIcon />}
              onClick={handleScreenshot}
              disabled={loading.screenshot || !screenshotForm.url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.screenshot ? 'Capturing...' : 'Capture Screenshot'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('screenshot', results.screenshot, <ScreenshotIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Screenshot Features
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<ScreenshotIcon />} label="Device Emulation" variant="outlined" />
                  <Chip icon={<ImageIcon />} label="Full Page Capture" variant="outlined" />
                  <Chip label="CSS/JS Injection" variant="outlined" />
                  <Chip label="Custom Viewports" variant="outlined" />
                  <Chip label="High Quality Output" variant="outlined" />
                  <Chip label="Multiple Formats" variant="outlined" />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Powered by Playwright with support for complex web applications and dynamic content.
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default WebScreenshotsTab;
