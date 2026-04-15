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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Article as ArticleIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Check as CheckIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

interface ArticleScriptResult {
  script: string;
  article_title: string;
  article_word_count: number;
  script_word_count: number;
  source_url: string;
  script_type: string;
}

const SCRIPT_TYPES = [
  { value: 'educational', label: 'Educational' },
  { value: 'facts', label: 'Facts' },
  { value: 'story', label: 'Story' },
  { value: 'motivation', label: 'Motivation' },
  { value: 'life_wisdom', label: 'Life Wisdom' },
  { value: 'daily_news', label: 'Daily News' },
  { value: 'life_hacks', label: 'Life Hacks' },
  { value: 'dark_psychology', label: 'Dark Psychology' },
  { value: 'reddit_stories', label: 'Reddit Stories' },
  { value: 'shower_thoughts', label: 'Shower Thoughts' },
  { value: 'pov', label: 'POV' },
];

const ArticleToScriptTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors } = ctx;

  const [form, setForm] = useState({
    url: '',
    script_type: 'educational',
    max_duration: 60,
    language: 'english',
    use_browser: false,
  });

  const [result, setResult] = useState<ArticleScriptResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async () => {
    if (!form.url.trim()) {
      setErrors(prev => ({ ...prev, article: 'URL is required' }));
      return;
    }

    setLoading(prev => ({ ...prev, article: true }));
    setErrors(prev => ({ ...prev, article: null }));
    setResult(null);

    try {
      const response = await directApi.post('/text/article-to-script', form);
      if (response.data) {
        setResult(response.data);
      } else {
        setErrors(prev => ({ ...prev, article: 'No script generated' }));
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err.message || 'Failed to generate script';
      setErrors(prev => ({ ...prev, article: detail }));
    } finally {
      setLoading(prev => ({ ...prev, article: false }));
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadScript = () => {
    if (!result) return;
    const filename = (result.article_title || 'script').replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50) + '.txt';
    const blob = new Blob([result.script], { type: 'text/plain' });
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  };

  return (
    <>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ArticleIcon color="primary" />
                Article to Script
              </Typography>

              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Article URL"
                    placeholder="https://example.com/blog/article-title"
                    value={form.url}
                    onChange={(e) => setForm({ ...form, url: e.target.value })}
                    InputProps={{
                      startAdornment: <LinkIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !loading.article) handleSubmit();
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Script Type</InputLabel>
                    <Select
                      value={form.script_type}
                      label="Script Type"
                      onChange={(e) => setForm({ ...form, script_type: e.target.value })}
                    >
                      {SCRIPT_TYPES.map((t) => (
                        <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={form.language}
                      label="Language"
                      onChange={(e) => setForm({ ...form, language: e.target.value })}
                    >
                      <MenuItem value="english">English</MenuItem>
                      <MenuItem value="french">French</MenuItem>
                      <MenuItem value="spanish">Spanish</MenuItem>
                      <MenuItem value="german">German</MenuItem>
                      <MenuItem value="portuguese">Portuguese</MenuItem>
                      <MenuItem value="arabic">Arabic</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Max Duration: {form.max_duration}s (~{Math.round(form.max_duration * 2.8)} words)
                  </Typography>
                  <Slider
                    value={form.max_duration}
                    onChange={(_, value) => setForm({ ...form, max_duration: value as number })}
                    min={15}
                    max={300}
                    step={5}
                    marks={[
                      { value: 15, label: '15s' },
                      { value: 60, label: '60s' },
                      { value: 120, label: '2m' },
                      { value: 300, label: '5m' },
                    ]}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.use_browser}
                        onChange={(e) => setForm({ ...form, use_browser: e.target.checked })}
                        size="small"
                      />
                    }
                    label={
                      <Typography variant="body2">
                        Use browser rendering (for JS-heavy sites)
                      </Typography>
                    }
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    onClick={handleSubmit}
                    disabled={loading.article || !form.url.trim()}
                    startIcon={loading.article ? <CircularProgress size={18} color="inherit" /> : <ArticleIcon />}
                    sx={{ textTransform: 'none' }}
                  >
                    {loading.article ? 'Converting Article...' : 'Convert Article to Script'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                How It Works
              </Typography>
              <Typography variant="body2" color="text.secondary">
                1. Paste any article URL
                <br />
                2. We extract the article content (removing ads, navigation, etc.)
                <br />
                3. AI converts it into a video script of your chosen type and duration
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {ctx.errors.article && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {ctx.errors.article}
        </Alert>
      )}

      {result && (
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 2, mt: 3 }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            {result.article_title && (
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                {result.article_title}
              </Typography>
            )}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <Chip label={`Article: ${result.article_word_count} words`} size="small" variant="outlined" />
              <Chip label={`Script: ${result.script_word_count} words`} size="small" color="primary" variant="outlined" />
              <Chip label={result.script_type} size="small" variant="outlined" />
            </Box>

            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Tooltip title={copied ? 'Copied!' : 'Copy script'}>
                <IconButton onClick={() => copyToClipboard(result.script)} size="small">
                  {copied ? <CheckIcon color="success" /> : <CopyIcon />}
                </IconButton>
              </Tooltip>
              <Tooltip title="Download script">
                <IconButton onClick={downloadScript} size="small">
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            </Box>

            <Paper
              elevation={0}
              sx={{
                p: 2,
                bgcolor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: 1,
                maxHeight: 500,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: 1.8,
              }}
            >
              {result.script}
            </Paper>
          </CardContent>
        </Card>
      )}
    </>
  );
};

export default ArticleToScriptTab;
