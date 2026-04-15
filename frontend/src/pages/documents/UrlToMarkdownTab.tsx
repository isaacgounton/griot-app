import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Paper,
  FormControlLabel,
  Switch,
  Chip,
} from '@mui/material';
import {
  Link as LinkIcon,
  Language as BrowserIcon,
  Article as ArticleIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface UrlToMarkdownResult {
  title: string;
  author: string;
  date: string;
  description: string;
  sitename: string;
  markdown: string;
  word_count: number;
  source_url: string;
}

interface Props {
  ctx: TabContext;
}

const UrlToMarkdownTab: React.FC<Props> = ({ ctx }) => {
  const { copyToClipboard, downloadMarkdown, copied } = ctx;

  // Local form state
  const [url, setUrl] = useState('');
  const [useBrowser, setUseBrowser] = useState(false);
  const [articleOnly, setArticleOnly] = useState(false);
  const [includeMetadata, setIncludeMetadata] = useState(true);

  // Local result state (sync endpoint, no job queue)
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UrlToMarkdownResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.post('/documents/url-to-markdown/', {
        url: url.trim(),
        use_browser: useBrowser,
        article_only: articleOnly,
        include_metadata: includeMetadata,
      });

      if (response.data) {
        setResult(response.data);
      } else {
        setError('No content extracted from URL');
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err.message || 'Failed to convert URL';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const renderResult = () => {
    if (!result && !error) return null;

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
          <LinkIcon color="primary" />
          Conversion Result
          {loading && <CircularProgress size={16} sx={{ ml: 1 }} />}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>
            {error}
          </Alert>
        )}

        {result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
              Page converted successfully!
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Page Info:
              </Typography>
              <Paper sx={{ p: 1.5, bgcolor: '#f8fafc' }}>
                <Grid container spacing={1} sx={{ fontSize: '0.7rem' }}>
                  {result.title && (
                    <Grid item xs={12}>
                      <strong>Title:</strong> {result.title.slice(0, 60)}{result.title.length > 60 ? '...' : ''}
                    </Grid>
                  )}
                  {result.author && (
                    <Grid item xs={6}>
                      <strong>Author:</strong> {result.author}
                    </Grid>
                  )}
                  {result.word_count > 0 && (
                    <Grid item xs={6}>
                      <strong>Words:</strong> {result.word_count.toLocaleString()}
                    </Grid>
                  )}
                  {result.sitename && (
                    <Grid item xs={6}>
                      <strong>Site:</strong> {result.sitename}
                    </Grid>
                  )}
                  {result.date && (
                    <Grid item xs={6}>
                      <strong>Date:</strong> {result.date}
                    </Grid>
                  )}
                </Grid>
              </Paper>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Preview:
              </Typography>
              <Paper sx={{
                p: 1.5,
                bgcolor: '#f0f9ff',
                maxHeight: 150,
                overflow: 'auto',
                fontSize: '0.75rem'
              }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {result.markdown.slice(0, 200)}
                  {result.markdown.length > 200 && '...'}
                </Typography>
              </Paper>
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => copyToClipboard(result.markdown)}
                  sx={{ fontSize: '0.7rem', px: 1 }}
                >
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => downloadMarkdown(
                    result.markdown,
                    `${(result.title || 'page').replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50)}.md`
                  )}
                  sx={{ fontSize: '0.7rem', px: 1 }}
                >
                  Download
                </Button>
              </Box>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            <Typography variant="h6" sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', alignItems: 'center', gap: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              <LinkIcon color="primary" />
              URL to Markdown
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Web Page URL"
                  placeholder="https://example.com/any-page"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  helperText="Enter the URL of any web page to convert to Markdown"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !loading) handleSubmit();
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={articleOnly}
                      onChange={(e) => setArticleOnly(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Article Only"
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={useBrowser}
                      onChange={(e) => setUseBrowser(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Browser Rendering"
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeMetadata}
                      onChange={(e) => setIncludeMetadata(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Include Metadata"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <LinkIcon />}
              onClick={handleSubmit}
              disabled={loading || !url.trim()}
              sx={{ mt: 3, px: { xs: 2, sm: 4 }, width: { xs: '100%', sm: 'auto' } }}
            >
              {loading ? 'Converting...' : 'Convert to Markdown'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
            {renderResult() || (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Quick Examples
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Try these example pages:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setUrl('https://en.wikipedia.org/wiki/Artificial_intelligence')}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Wikipedia Article
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setUrl('https://docs.python.org/3/tutorial/index.html')}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Python Docs
                  </Button>
                </Box>

                <Typography variant="h6" sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Conversion Modes
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<SpeedIcon />} label="Full Page (default)" variant="outlined" />
                  <Chip icon={<ArticleIcon />} label="Article Only (strips nav/ads)" variant="outlined" />
                  <Chip icon={<BrowserIcon />} label="Browser Rendering (JS sites)" variant="outlined" />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Uses trafilatura for article extraction and markdownify for full page conversion.
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default UrlToMarkdownTab;
