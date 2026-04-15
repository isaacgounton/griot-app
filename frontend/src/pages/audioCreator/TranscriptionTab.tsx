import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  CircularProgress
} from '@mui/material';
import {
  Subtitles as TranscribeIcon,
  Send as SendIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const TranscriptionTab: React.FC<Props> = ({ ctx }) => {
  const {
    loading, setLoading, setError, setResult,
    setJobStatus, setJobProgress, setPollingJobId,
    pollJobStatus, renderJobResult
  } = ctx;

  const [transcriptionForm, setTranscriptionForm] = useState({
    media_url: '',
    include_text: true,
    include_srt: true,
    word_timestamps: false,
    include_segments: false,
    language: '',
    max_words_per_line: 10,
    beam_size: 5,
    model_size: 'base',
    temperature: 0,
    initial_prompt: ''
  });
  const [transcriptionFile, setTranscriptionFile] = useState<File | null>(null);

  const handleTranscriptionSubmit = async () => {
    const hasUrl = transcriptionForm.media_url.trim();
    const hasFile = !!transcriptionFile;

    if (!hasUrl && !hasFile) {
      setError('Please provide a media URL or upload a file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response;

      if (hasFile) {
        const formData = new FormData();
        formData.append('file', transcriptionFile!);
        formData.append('include_text', String(transcriptionForm.include_text));
        formData.append('include_srt', String(transcriptionForm.include_srt));
        formData.append('word_timestamps', String(transcriptionForm.word_timestamps));
        formData.append('include_segments', String(transcriptionForm.include_segments));
        if (transcriptionForm.language) formData.append('language', transcriptionForm.language);
        formData.append('max_words_per_line', String(transcriptionForm.max_words_per_line));
        formData.append('beam_size', String(transcriptionForm.beam_size));
        formData.append('model_size', transcriptionForm.model_size);
        formData.append('temperature', String(transcriptionForm.temperature));
        if (transcriptionForm.initial_prompt) formData.append('initial_prompt', transcriptionForm.initial_prompt);

        response = await directApi.post('/audio/transcriptions/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        response = await directApi.post('/audio/transcriptions', {
          ...transcriptionForm,
          language: transcriptionForm.language || undefined,
          initial_prompt: transcriptionForm.initial_prompt || undefined,
        });
      }

      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting transcription...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to create transcription job');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TranscribeIcon color="primary" />
              Media Transcription Configuration
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              {/* Media Source: Upload or URL side by side */}
              <Grid item xs={12} sm={6}>
                {transcriptionFile ? (
                  <Box
                    sx={{
                      border: '1px solid',
                      borderColor: 'primary.main',
                      borderRadius: 1.5,
                      p: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      bgcolor: 'primary.50',
                      height: '56px',
                    }}
                  >
                    <UploadIcon sx={{ fontSize: 20, color: 'primary.main', flexShrink: 0 }} />
                    <Typography variant="body2" fontWeight={500} noWrap sx={{ flex: 1, minWidth: 0 }}>
                      {transcriptionFile.name}
                    </Typography>
                    <Button
                      size="small"
                      color="error"
                      variant="text"
                      onClick={() => setTranscriptionFile(null)}
                      sx={{ minWidth: 'auto', px: 1, flexShrink: 0 }}
                    >
                      Remove
                    </Button>
                  </Box>
                ) : (
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<UploadIcon />}
                    onClick={() => document.getElementById('transcription-file-input')?.click()}
                    disabled={!!transcriptionForm.media_url.trim()}
                    sx={{
                      height: '56px',
                      borderStyle: 'dashed',
                      textTransform: 'none',
                      color: 'text.secondary',
                      borderColor: 'divider',
                      '&:hover': { borderColor: 'primary.main', borderStyle: 'dashed' }
                    }}
                  >
                    Upload file
                  </Button>
                )}
                <input
                  id="transcription-file-input"
                  type="file"
                  accept="audio/*,video/*,.mp3,.wav,.m4a,.flac,.ogg,.mp4,.mov,.avi,.mkv,.webm"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setTranscriptionFile(file);
                      setTranscriptionForm({ ...transcriptionForm, media_url: '' });
                    }
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Media URL"
                  placeholder="https://example.com/audio.mp3"
                  value={transcriptionForm.media_url}
                  onChange={(e) => {
                    setTranscriptionForm({ ...transcriptionForm, media_url: e.target.value });
                    if (e.target.value.trim()) setTranscriptionFile(null);
                  }}
                  disabled={!!transcriptionFile}
                  size="medium"
                />
              </Grid>

              {/* Model Selection */}
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Whisper Model</InputLabel>
                  <Select
                    value={transcriptionForm.model_size}
                    label="Whisper Model"
                    onChange={(e) => setTranscriptionForm({ ...transcriptionForm, model_size: e.target.value })}
                  >
                    <MenuItem value="tiny">Tiny (fastest, least accurate)</MenuItem>
                    <MenuItem value="base">Base (recommended)</MenuItem>
                    <MenuItem value="small">Small (better accuracy, slower)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Language (Optional)</InputLabel>
                  <Select
                    value={transcriptionForm.language}
                    label="Language (Optional)"
                    onChange={(e) => setTranscriptionForm({ ...transcriptionForm, language: e.target.value })}
                  >
                    <MenuItem value="">
                      <em>Auto-detect (Recommended)</em>
                    </MenuItem>
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="zh">Chinese</MenuItem>
                    <MenuItem value="de">German</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="ru">Russian</MenuItem>
                    <MenuItem value="ko">Korean</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                    <MenuItem value="ja">Japanese</MenuItem>
                    <MenuItem value="pt">Portuguese</MenuItem>
                    <MenuItem value="tr">Turkish</MenuItem>
                    <MenuItem value="pl">Polish</MenuItem>
                    <MenuItem value="ca">Catalan</MenuItem>
                    <MenuItem value="nl">Dutch</MenuItem>
                    <MenuItem value="ar">Arabic</MenuItem>
                    <MenuItem value="sv">Swedish</MenuItem>
                    <MenuItem value="it">Italian</MenuItem>
                    <MenuItem value="id">Indonesian</MenuItem>
                    <MenuItem value="hi">Hindi</MenuItem>
                    <MenuItem value="fi">Finnish</MenuItem>
                    <MenuItem value="vi">Vietnamese</MenuItem>
                    <MenuItem value="he">Hebrew</MenuItem>
                    <MenuItem value="uk">Ukrainian</MenuItem>
                    <MenuItem value="el">Greek</MenuItem>
                    <MenuItem value="ms">Malay</MenuItem>
                    <MenuItem value="cs">Czech</MenuItem>
                    <MenuItem value="ro">Romanian</MenuItem>
                    <MenuItem value="da">Danish</MenuItem>
                    <MenuItem value="hu">Hungarian</MenuItem>
                    <MenuItem value="ta">Tamil</MenuItem>
                    <MenuItem value="no">Norwegian</MenuItem>
                    <MenuItem value="th">Thai</MenuItem>
                    <MenuItem value="ur">Urdu</MenuItem>
                    <MenuItem value="hr">Croatian</MenuItem>
                    <MenuItem value="bg">Bulgarian</MenuItem>
                    <MenuItem value="lt">Lithuanian</MenuItem>
                    <MenuItem value="la">Latin</MenuItem>
                    <MenuItem value="mi">Maori</MenuItem>
                    <MenuItem value="ml">Malayalam</MenuItem>
                    <MenuItem value="cy">Welsh</MenuItem>
                    <MenuItem value="sk">Slovak</MenuItem>
                    <MenuItem value="te">Telugu</MenuItem>
                    <MenuItem value="fa">Persian</MenuItem>
                    <MenuItem value="lv">Latvian</MenuItem>
                    <MenuItem value="bn">Bengali</MenuItem>
                    <MenuItem value="sr">Serbian</MenuItem>
                    <MenuItem value="az">Azerbaijani</MenuItem>
                    <MenuItem value="sl">Slovenian</MenuItem>
                    <MenuItem value="kn">Kannada</MenuItem>
                    <MenuItem value="et">Estonian</MenuItem>
                    <MenuItem value="mk">Macedonian</MenuItem>
                    <MenuItem value="br">Breton</MenuItem>
                    <MenuItem value="eu">Basque</MenuItem>
                    <MenuItem value="is">Icelandic</MenuItem>
                    <MenuItem value="hy">Armenian</MenuItem>
                    <MenuItem value="ne">Nepali</MenuItem>
                    <MenuItem value="mn">Mongolian</MenuItem>
                    <MenuItem value="bs">Bosnian</MenuItem>
                    <MenuItem value="kk">Kazakh</MenuItem>
                    <MenuItem value="sq">Albanian</MenuItem>
                    <MenuItem value="sw">Swahili</MenuItem>
                    <MenuItem value="gl">Galician</MenuItem>
                    <MenuItem value="mr">Marathi</MenuItem>
                    <MenuItem value="pa">Punjabi</MenuItem>
                    <MenuItem value="si">Sinhala</MenuItem>
                    <MenuItem value="km">Khmer</MenuItem>
                    <MenuItem value="sn">Shona</MenuItem>
                    <MenuItem value="yo">Yoruba</MenuItem>
                    <MenuItem value="so">Somali</MenuItem>
                    <MenuItem value="af">Afrikaans</MenuItem>
                    <MenuItem value="oc">Occitan</MenuItem>
                    <MenuItem value="ka">Georgian</MenuItem>
                    <MenuItem value="be">Belarusian</MenuItem>
                    <MenuItem value="tg">Tajik</MenuItem>
                    <MenuItem value="sd">Sindhi</MenuItem>
                    <MenuItem value="gu">Gujarati</MenuItem>
                    <MenuItem value="am">Amharic</MenuItem>
                    <MenuItem value="yi">Yiddish</MenuItem>
                    <MenuItem value="lo">Lao</MenuItem>
                    <MenuItem value="uz">Uzbek</MenuItem>
                    <MenuItem value="fo">Faroese</MenuItem>
                    <MenuItem value="ht">Haitian Creole</MenuItem>
                    <MenuItem value="ps">Pashto</MenuItem>
                    <MenuItem value="tk">Turkmen</MenuItem>
                    <MenuItem value="nn">Nynorsk</MenuItem>
                    <MenuItem value="mt">Maltese</MenuItem>
                    <MenuItem value="sa">Sanskrit</MenuItem>
                    <MenuItem value="lb">Luxembourgish</MenuItem>
                    <MenuItem value="my">Myanmar</MenuItem>
                    <MenuItem value="bo">Tibetan</MenuItem>
                    <MenuItem value="tl">Tagalog</MenuItem>
                    <MenuItem value="mg">Malagasy</MenuItem>
                    <MenuItem value="as">Assamese</MenuItem>
                    <MenuItem value="tt">Tatar</MenuItem>
                    <MenuItem value="haw">Hawaiian</MenuItem>
                    <MenuItem value="ln">Lingala</MenuItem>
                    <MenuItem value="ha">Hausa</MenuItem>
                    <MenuItem value="ba">Bashkir</MenuItem>
                    <MenuItem value="jw">Javanese</MenuItem>
                    <MenuItem value="su">Sundanese</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Max Words Per Line: {transcriptionForm.max_words_per_line}</Typography>
                <Slider
                  value={transcriptionForm.max_words_per_line}
                  onChange={(_, value) => setTranscriptionForm({ ...transcriptionForm, max_words_per_line: value as number })}
                  min={1}
                  max={20}
                  step={1}
                  marks={[
                    { value: 5, label: '5' },
                    { value: 10, label: '10' },
                    { value: 15, label: '15' },
                    { value: 20, label: '20' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Beam Size: {transcriptionForm.beam_size}</Typography>
                <Slider
                  value={transcriptionForm.beam_size}
                  onChange={(_, value) => setTranscriptionForm({ ...transcriptionForm, beam_size: value as number })}
                  min={1}
                  max={10}
                  step={1}
                  marks={[
                    { value: 1, label: '1' },
                    { value: 5, label: '5' },
                    { value: 10, label: '10' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Temperature: {transcriptionForm.temperature}</Typography>
                <Slider
                  value={transcriptionForm.temperature}
                  onChange={(_, value) => setTranscriptionForm({ ...transcriptionForm, temperature: value as number })}
                  min={0}
                  max={1}
                  step={0.1}
                  marks={[
                    { value: 0, label: '0' },
                    { value: 0.5, label: '0.5' },
                    { value: 1, label: '1' }
                  ]}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Initial Prompt (Optional)"
                  placeholder="Provide context, spelling hints, or style guidance for the transcription..."
                  value={transcriptionForm.initial_prompt}
                  onChange={(e) => setTranscriptionForm({ ...transcriptionForm, initial_prompt: e.target.value })}
                  multiline
                  rows={2}
                  helperText="Guide the model with context, proper nouns, or formatting hints."
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Output Options
                </Typography>
                <Grid container spacing={{ xs: 2, sm: 2 }}>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={transcriptionForm.include_text}
                          onChange={(e) => setTranscriptionForm({ ...transcriptionForm, include_text: e.target.checked })}
                        />
                      }
                      label="Include Plain Text"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={transcriptionForm.include_srt}
                          onChange={(e) => setTranscriptionForm({ ...transcriptionForm, include_srt: e.target.checked })}
                        />
                      }
                      label="Include SRT Subtitles"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={transcriptionForm.word_timestamps}
                          onChange={(e) => setTranscriptionForm({ ...transcriptionForm, word_timestamps: e.target.checked })}
                        />
                      }
                      label="Word-level Timestamps"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={transcriptionForm.include_segments}
                          onChange={(e) => setTranscriptionForm({ ...transcriptionForm, include_segments: e.target.checked })}
                        />
                      }
                      label="Include Segments"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleTranscriptionSubmit}
              disabled={loading || (!transcriptionForm.media_url.trim() && !transcriptionFile)}
              fullWidth
              sx={{
                mt: 3,
                px: 4,
                maxWidth: { sm: '300px' },
                alignSelf: { sm: 'flex-start' }
              }}
            >
              {loading ? 'Creating Job...' : 'Start Transcription'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            {renderJobResult(2) || (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Transcription Features
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Powered by Speaches.ai running faster-whisper for fast, accurate transcription.
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      File Upload & URL
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Upload files directly or provide a URL. Supports MP3, WAV, M4A, FLAC, OGG, MP4, and more.
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      7 Model Sizes
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      From Tiny (fastest) to Large v3 (most accurate). Base is recommended for most use cases.
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      Output Formats
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Plain text, SRT subtitles, word-level timestamps, and segment data with quality metrics.
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      Initial Prompt
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Guide the model with context, proper nouns, acronyms, or formatting hints for better results.
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      99+ Languages
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Auto-detection or manual selection. Processing time: 10-25% of media duration.
                    </Typography>
                  </Box>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default TranscriptionTab;
