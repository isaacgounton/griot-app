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
  FormControlLabel,
  Divider,
  FormGroup,
  FormLabel
} from '@mui/material';
import {
  CloudDownload as DownloadIcon,
  YouTube as YouTubeIcon,
  AudioFile as AudioIcon,
  VideoFile as VideoIcon,
  Image as ImageIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const MediaDownloadTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [downloadForm, setDownloadForm] = useState({
    url: '',
    file_name: '',
    cookies_url: '',
    format: 'best',
    extract_subtitles: false,
    subtitle_languages: ['en', 'auto'],
    subtitle_formats: ['srt', 'vtt'],
    extract_thumbnail: false,
    embed_metadata: true,
    thumbnail_format: 'jpg'
  });

  const handleDownload = async () => {
    if (!downloadForm.url.trim()) {
      setErrors(prev => ({ ...prev, download: 'URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, download: true }));
    setErrors(prev => ({ ...prev, download: null }));
    setResults(prev => ({ ...prev, download: null }));

    try {
      const response = await directApi.post('/media/download', downloadForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'download');
      } else {
        setErrors(prev => ({ ...prev, download: 'Failed to create download job' }));
        setLoading(prev => ({ ...prev, download: false }));
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: unknown; message?: string } }; message?: string };
      const detail = error.response?.data?.detail;
      const errorMessage = Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ') : (typeof detail === 'string' ? detail : error.response?.data?.message || error.message || 'An error occurred');
      setErrors(prev => ({ ...prev, download: errorMessage }));
      setLoading(prev => ({ ...prev, download: false }));
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <DownloadIcon color="primary" />
              Media Download
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://www.youtube.com/watch?v=... or any media URL"
                  value={downloadForm.url}
                  onChange={(e) => setDownloadForm({ ...downloadForm, url: e.target.value })}
                  helperText="Supports 1000+ platforms: YouTube, Vimeo, TikTok, Instagram, Twitter, Facebook and more"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Format</InputLabel>
                  <Select
                    value={downloadForm.format}
                    label="Format"
                    onChange={(e) => setDownloadForm({ ...downloadForm, format: e.target.value })}
                  >
                    <MenuItem value="best">Best Quality</MenuItem>
                    <MenuItem value="mp4">MP4 Video</MenuItem>
                    <MenuItem value="mp3">MP3 Audio</MenuItem>
                    <MenuItem value="720p">720p Video</MenuItem>
                    <MenuItem value="480p">480p Video</MenuItem>
                    <MenuItem value="360p">360p Video</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Custom Filename (Optional)"
                  placeholder="my-video.mp4"
                  value={downloadForm.file_name}
                  onChange={(e) => setDownloadForm({ ...downloadForm, file_name: e.target.value })}
                  helperText="Auto-generated if not provided"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Cookies URL (Optional)"
                  placeholder="https://example.com/cookies.txt"
                  value={downloadForm.cookies_url}
                  onChange={(e) => setDownloadForm({ ...downloadForm, cookies_url: e.target.value })}
                  helperText="For private/protected content access"
                />
              </Grid>
            </Grid>

            {/* Additional Features */}
            <Box sx={{ mt: 3, mb: 2 }}>
              <Divider>
                <Chip label="Additional Features" color="primary" size="small" />
              </Divider>
            </Box>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset">
                  <FormLabel component="legend">Subtitle Extraction</FormLabel>
                  <FormGroup row>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={downloadForm.extract_subtitles}
                          onChange={(e) => setDownloadForm({ ...downloadForm, extract_subtitles: e.target.checked })}
                          color="primary"
                        />
                      }
                      label="Extract Subtitles"
                    />
                  </FormGroup>
                  {downloadForm.extract_subtitles && (
                    <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'auto'].map((lang) => (
                        <Chip
                          key={lang}
                          label={lang.toUpperCase()}
                          clickable
                          color={downloadForm.subtitle_languages.includes(lang) ? 'primary' : 'default'}
                          onClick={() => {
                            setDownloadForm(prev => ({
                              ...prev,
                              subtitle_languages: prev.subtitle_languages.includes(lang)
                                ? prev.subtitle_languages.filter(l => l !== lang)
                                : [...prev.subtitle_languages, lang]
                            }));
                          }}
                          size="small"
                        />
                      ))}
                    </Box>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset">
                  <FormLabel component="legend">Thumbnail Generation</FormLabel>
                  <FormGroup>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={downloadForm.extract_thumbnail}
                          onChange={(e) => setDownloadForm({ ...downloadForm, extract_thumbnail: e.target.checked })}
                          color="primary"
                        />
                      }
                      label="Extract Thumbnail"
                    />
                    {downloadForm.extract_thumbnail && (
                      <FormControl sx={{ mt: 1 }}>
                        <InputLabel size="small">Thumbnail Format</InputLabel>
                        <Select
                          value={downloadForm.thumbnail_format}
                          label="Thumbnail Format"
                          size="small"
                          onChange={(e) => setDownloadForm({ ...downloadForm, thumbnail_format: e.target.value })}
                        >
                          <MenuItem value="jpg">JPG</MenuItem>
                          <MenuItem value="png">PNG</MenuItem>
                          <MenuItem value="webp">WebP</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={downloadForm.embed_metadata}
                      onChange={(e) => setDownloadForm({ ...downloadForm, embed_metadata: e.target.checked })}
                      color="primary"
                    />
                  }
                  label="Embed Metadata in File"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading.download ? <CircularProgress size={20} /> : <DownloadIcon />}
              onClick={handleDownload}
              disabled={loading.download || !downloadForm.url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading.download ? 'Downloading...' : 'Download Media'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderJobResult('download', results.download, <DownloadIcon />) || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Features
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<YouTubeIcon />} label="1000+ Platforms" variant="outlined" />
                  <Chip icon={<VideoIcon />} label="Subtitle Extraction" variant="outlined" />
                  <Chip icon={<ImageIcon />} label="Thumbnail Generation" variant="outlined" />
                  <Chip icon={<AudioIcon />} label="Metadata Embedding" variant="outlined" />
                  <Chip label="Private Content Support" variant="outlined" />
                  <Chip label="Custom Formats" variant="outlined" />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Powered by yt-dlp with advanced features for media downloading.
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default MediaDownloadTab;
