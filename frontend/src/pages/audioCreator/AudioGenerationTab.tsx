import React, { useState, useEffect, useCallback } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  VolumeUp as AudioIcon,
  Send as SendIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext, Voice, ModelItem } from './types';

interface Props {
  ctx: TabContext;
}

const AudioGenerationTab: React.FC<Props> = ({ ctx }) => {
  const {
    loading, setLoading, setError, setResult,
    setJobStatus, setJobProgress, setPollingJobId,
    pollJobStatus, renderJobResult,
    voices, models, providers, loadingVoices
  } = ctx;

  const [ttsForm, setTtsForm] = useState({
    text: '',
    voice: 'af_heart',
    provider: 'kokoro',
    model: 'tts-1',
    response_format: 'wav',
    speed: 1.0,
    volume_multiplier: 1.0,
    lang_code: 'en_us',
    return_timestamps: false,
    stream: false,
    stream_format: 'audio',
    remove_filter: false,
    normalize: true,
    unit_normalization: false,
    url_normalization: true,
    email_normalization: true,
    phone_normalization: true,
    replace_remaining_symbols: true
  });

  const playVoiceSample = async () => {
    if (!ttsForm.voice || !ttsForm.provider) {
      setError('Please select a voice and provider');
      return;
    }

    try {
      setLoading(true);
      setJobProgress('Generating voice sample...');

      const response = await directApi.post('/audio/voice-sample', null, {
        params: {
          voice: ttsForm.voice,
          provider: ttsForm.provider,
          response_format: 'mp3'
        }
      });

      if (response.data?.success && response.data?.audio_url) {
        const audio = new Audio(response.data.audio_url);
        audio.play().catch(err => {
          console.error('Failed to play audio:', err);
          setError('Failed to play voice sample');
        });
        setJobProgress('');
        setLoading(false);
      } else {
        setError('Failed to generate voice sample');
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate voice sample';
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleTtsSubmit = async () => {
    if (!ttsForm.text.trim()) {
      setError('Text content is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const requestData = {
        text: ttsForm.text,
        voice: ttsForm.voice,
        provider: ttsForm.provider,
        model: ttsForm.model,
        response_format: ttsForm.response_format,
        speed: ttsForm.speed,
        volume_multiplier: ttsForm.volume_multiplier,
        lang_code: ttsForm.lang_code || undefined,
        return_timestamps: ttsForm.return_timestamps,
        stream: ttsForm.stream,
        stream_format: ttsForm.stream_format,
        remove_filter: ttsForm.remove_filter,
        normalization_options: {
          normalize: ttsForm.normalize,
          unit_normalization: ttsForm.unit_normalization,
          url_normalization: ttsForm.url_normalization,
          email_normalization: ttsForm.email_normalization,
          phone_normalization: ttsForm.phone_normalization,
          replace_remaining_symbols: ttsForm.replace_remaining_symbols
        }
      };

      const response = await directApi.post('/audio/speech', requestData);
      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting processing...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to generate speech');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Helper functions to get dynamic options
  const getProviderOptions = useCallback(() => {
    if (providers.providers && Array.isArray(providers.providers) && providers.providers.length > 0) {
      return providers.providers;
    }
    return ['kokoro', 'piper', 'edge'];
  }, [providers.providers]);

  const getFormatOptions = useCallback(() => {
    if (!providers.formats) return ['mp3', 'wav'];
    const currentProvider = ttsForm.provider;
    return providers.formats[currentProvider] || ['mp3', 'wav'];
  }, [providers.formats, ttsForm.provider]);

  const getModelOptions = useCallback(() => {
    const modelsData = (models as Record<string, unknown>)?.models || models;
    if (!modelsData || typeof modelsData !== 'object' || Object.keys(modelsData).length === 0) return [];

    const currentProvider = ttsForm.provider;
    const providerModels = (modelsData as Record<string, unknown>)[currentProvider];
    if (providerModels && Array.isArray(providerModels)) {
      return providerModels.map((model: ModelItem) => model.id);
    }
    return [];
  }, [models, ttsForm.provider]);

  const getVoiceOptions = useCallback(() => {
    const currentProvider = ttsForm.provider;
    if (!voices[currentProvider]) return [];

    let filteredVoices = voices[currentProvider];

    if (ttsForm.lang_code) {
      filteredVoices = filteredVoices.filter((voice: Voice) => {
        const voiceLanguage = String(voice.language || '').toLowerCase();
        const selectedLang = ttsForm.lang_code.toLowerCase();

        return voiceLanguage.startsWith(selectedLang) ||
          voiceLanguage.includes(selectedLang) ||
          selectedLang.startsWith(voiceLanguage.split('-')[0]);
      });
    }

    return filteredVoices.map((voice: Voice) => {
      const id = String(voice.name || voice.id || '');
      let label = '';

      if (voice.display_name) {
        label = String(voice.display_name);
      } else if (voice.description) {
        label = String(voice.description);
      } else {
        label = String(voice.name || voice.id || 'Unknown Voice');
      }

      return {
        ...voice,
        id,
        label
      };
    });
  }, [voices, ttsForm.provider, ttsForm.lang_code]);

  // Update form defaults when data is loaded
  useEffect(() => {
    if (!loadingVoices && (voices || providers)) {
      try {
        const availableProviders = getProviderOptions();
        const currentProvider = availableProviders.includes(ttsForm.provider)
          ? ttsForm.provider
          : (availableProviders[0] || 'kokoro');

        const providerVoices = voices[currentProvider] || [];
        const languages = new Set<string>();
        providerVoices.forEach((voice: Voice) => {
          const lang = String(voice.language || '');
          if (lang) {
            languages.add(lang.toLowerCase());
          }
        });
        const availableLanguages = Array.from(languages).sort();

        const currentLangCode = availableLanguages.includes(ttsForm.lang_code)
          ? ttsForm.lang_code
          : (availableLanguages[0] || 'en_us');

        let availableVoices = providerVoices;

        if (currentLangCode) {
          availableVoices = availableVoices.filter((voice: Voice) => {
            const voiceLanguage = String(voice.language || '').toLowerCase();
            return voiceLanguage === currentLangCode || voiceLanguage.startsWith(currentLangCode);
          });
        }
        const currentVoice = availableVoices.find(v =>
          String(v.name || v.id) === String(ttsForm.voice)
        )
          ? ttsForm.voice
          : String(availableVoices[0]?.name || availableVoices[0]?.id || 'en_US-lessac-medium');

        const availableFormats = getFormatOptions();
        const currentFormat = availableFormats.includes(ttsForm.response_format)
          ? ttsForm.response_format
          : (availableFormats[0] || 'mp3');

        const availableModels = getModelOptions();
        const currentModel = availableModels.includes(ttsForm.model)
          ? ttsForm.model
          : (availableModels[0] || 'tts-1');

        setTtsForm(prev => ({
          ...prev,
          provider: String(currentProvider),
          lang_code: String(currentLangCode),
          voice: String(currentVoice),
          response_format: String(currentFormat),
          model: String(currentModel)
        }));
      } catch (error) {
        console.error('Error initializing form defaults:', error);
      }
    }
  }, [loadingVoices, voices, providers, getFormatOptions, getModelOptions, getProviderOptions]);

  const voiceOptions = getVoiceOptions();
  const formatOptions = getFormatOptions();
  const providerOptions = getProviderOptions();
  const modelOptions = getModelOptions();
  const streamFormatOptions = ['audio', 'sse'];

  const getAvailableLanguages = useCallback(() => {
    const currentProvider = ttsForm.provider;
    const providerVoices = voices[currentProvider] || [];
    const languages = new Set<string>();

    providerVoices.forEach((voice: Voice) => {
      const lang = String(voice.language || '');
      if (lang) {
        languages.add(lang.toLowerCase());
      }
    });

    return Array.from(languages).sort();
  }, [voices, ttsForm.provider]);

  const languageOptions = getAvailableLanguages();

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AudioIcon color="primary" />
              Text-to-Speech Configuration
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Text Content"
                  placeholder="Enter the text you want to convert to speech..."
                  value={ttsForm.text}
                  onChange={(e) => setTtsForm({ ...ttsForm, text: e.target.value })}
                  helperText="Maximum 5000 characters. Supports pause tags like [pause:0.5s]"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Provider</InputLabel>
                  <Select
                    value={ttsForm.provider || ''}
                    label="Provider"
                    onChange={(e) => {
                      const newProvider = String(e.target.value);
                      const newVoices = voices[newProvider] || [];
                      const newVoice = String(newVoices[0]?.name || newVoices[0]?.id || 'en_US-lessac-medium');
                      setTtsForm({
                        ...ttsForm,
                        provider: newProvider,
                        voice: newVoice
                      });
                    }}
                  >
                    {providerOptions.map((provider) => (
                      <MenuItem key={provider} value={provider}>
                        {provider.charAt(0).toUpperCase() + provider.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={languageOptions.includes(ttsForm.lang_code) ? ttsForm.lang_code : ''}
                    label="Language"
                    onChange={(e) => {
                      const newLangCode = e.target.value;
                      let filteredVoices = voices[ttsForm.provider] || [];
                      if (newLangCode) {
                        filteredVoices = filteredVoices.filter((voice: Voice) => {
                          const voiceLanguage = String(voice.language || '').toLowerCase();
                          return voiceLanguage === newLangCode || voiceLanguage.startsWith(newLangCode);
                        });
                      }

                      const newVoice = filteredVoices.length > 0
                        ? String(filteredVoices[0].name || filteredVoices[0].id)
                        : ttsForm.voice;

                      setTtsForm({
                        ...ttsForm,
                        lang_code: newLangCode,
                        voice: newVoice
                      });
                    }}
                  >
                    {languageOptions.map((lang: string) => (
                      <MenuItem key={lang} value={lang}>
                        {lang.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={8} sm={5}>
                <FormControl fullWidth>
                  <InputLabel>Voice</InputLabel>
                  <Select
                    value={voiceOptions.some(v => v.id === ttsForm.voice) ? ttsForm.voice : ''}
                    label="Voice"
                    onChange={(e) => setTtsForm({ ...ttsForm, voice: e.target.value })}
                    disabled={loadingVoices}
                  >
                    {loadingVoices ? (
                      <MenuItem disabled>Loading voices...</MenuItem>
                    ) : voiceOptions.length > 0 ? (
                      voiceOptions.map((voice: Voice) => (
                        <MenuItem key={voice.id} value={voice.id}>
                          {String(voice.label || voice.id || 'Unknown Voice')}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No voices available</MenuItem>
                    )}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={4} sm={1} sx={{ display: 'flex', alignItems: 'flex-end' }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => playVoiceSample()}
                  disabled={!ttsForm.voice || loadingVoices}
                  sx={{ width: '100%', height: '56px' }}
                  title="Play voice sample"
                >
                  <AudioIcon />
                </Button>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Output Format</InputLabel>
                  <Select
                    value={ttsForm.response_format || ''}
                    label="Output Format"
                    onChange={(e) => setTtsForm({ ...ttsForm, response_format: e.target.value })}
                  >
                    {formatOptions.map((format: string) => (
                      <MenuItem key={format} value={format}>
                        {format.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Model</InputLabel>
                  <Select
                    value={modelOptions.includes(ttsForm.model) ? ttsForm.model : ''}
                    label="Model"
                    onChange={(e) => setTtsForm({ ...ttsForm, model: e.target.value })}
                  >
                    {modelOptions.map((model: string) => (
                      <MenuItem key={model} value={model}>
                        {model}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Speed: {ttsForm.speed}x</Typography>
                <Slider
                  value={ttsForm.speed}
                  onChange={(_, value) => setTtsForm({ ...ttsForm, speed: value as number })}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: '0.5x' },
                    { value: 1.0, label: '1x' },
                    { value: 1.5, label: '1.5x' },
                    { value: 2.0, label: '2x' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Volume: {ttsForm.volume_multiplier}x</Typography>
                <Slider
                  value={ttsForm.volume_multiplier}
                  onChange={(_, value) => setTtsForm({ ...ttsForm, volume_multiplier: value as number })}
                  min={0.1}
                  max={3.0}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: '0.5x' },
                    { value: 1.0, label: '1x' },
                    { value: 2.0, label: '2x' },
                    { value: 3.0, label: '3x' }
                  ]}
                />
              </Grid>
            </Grid>

            {/* Advanced Options */}
            <Accordion sx={{ mt: 3 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SettingsIcon fontSize="small" />
                  Advanced Options
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={{ xs: 2, sm: 2 }}>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.return_timestamps}
                          onChange={(e) => setTtsForm({ ...ttsForm, return_timestamps: e.target.checked })}
                        />
                      }
                      label="Return Word Timestamps"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.stream}
                          onChange={(e) => setTtsForm({ ...ttsForm, stream: e.target.checked })}
                        />
                      }
                      label="Stream Response"
                    />
                  </Grid>
                  {ttsForm.stream && (
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Stream Format</InputLabel>
                        <Select
                          value={ttsForm.stream_format}
                          label="Stream Format"
                          onChange={(e) => setTtsForm({ ...ttsForm, stream_format: e.target.value })}
                        >
                          {streamFormatOptions.map((format: string) => (
                            <MenuItem key={format} value={format}>
                              {format === 'audio' ? 'Raw Audio' : 'Server-Sent Events (SSE)'}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  )}
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.remove_filter}
                          onChange={(e) => setTtsForm({ ...ttsForm, remove_filter: e.target.checked })}
                        />
                      }
                      label="Skip Text Preprocessing"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.normalize}
                          onChange={(e) => setTtsForm({ ...ttsForm, normalize: e.target.checked })}
                        />
                      }
                      label="Text Normalization"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.unit_normalization}
                          onChange={(e) => setTtsForm({ ...ttsForm, unit_normalization: e.target.checked })}
                        />
                      }
                      label="Unit Normalization"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ttsForm.url_normalization}
                          onChange={(e) => setTtsForm({ ...ttsForm, url_normalization: e.target.checked })}
                        />
                      }
                      label="URL Normalization"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleTtsSubmit}
              disabled={loading || !ttsForm.text.trim()}
              fullWidth
              sx={{
                mt: 3,
                px: 4,
                maxWidth: { sm: '300px' },
                alignSelf: { sm: 'flex-start' }
              }}
            >
              {loading ? 'Generating...' : 'Generate Speech'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            {renderJobResult(0) || (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Voice Options
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {loadingVoices ? (
                    <Typography variant="body2" color="text.secondary">
                      Loading voices...
                    </Typography>
                  ) : voiceOptions.length > 0 ? (
                    voiceOptions.slice(0, 6).map((voice: Voice) => (
                      <Chip
                        key={voice.id}
                        label={String(voice.id || 'Unknown')}
                        variant={ttsForm.voice === voice.id ? 'filled' : 'outlined'}
                        onClick={() => setTtsForm({ ...ttsForm, voice: voice.id })}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No voices available
                    </Typography>
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {loadingVoices
                    ? 'Loading available voices from API...'
                    : `${voiceOptions.length} voices available from ${ttsForm.provider} provider${ttsForm.lang_code ? ` (${ttsForm.lang_code.toUpperCase()})` : ''}. ${ttsForm.provider === 'kokoro' ? 'Kokoro supports voice combinations and weights.' : 'Provider-specific features available.'}`
                  }
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default AudioGenerationTab;
