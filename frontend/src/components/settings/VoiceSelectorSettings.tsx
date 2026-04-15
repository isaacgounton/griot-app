import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Slider,
  Typography,
  Switch,
  FormControlLabel,
} from '@mui/material';

import { VoiceInfo } from '../../types/contentCreation';

const VOICE_PROVIDERS = ['kokoro', 'piper', 'edge'] as const;
const LANGUAGES = ['en', 'fr', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'] as const;

/* eslint-disable no-unused-vars */
interface VoiceSelectorProps {
  voiceProvider: string;
  voiceName: string;
  language: string;
  enabled?: boolean;
  ttsSpeed?: number;
  voices: VoiceInfo[];
  onVoiceProviderChange: (provider: string) => void;
  onVoiceNameChange: (name: string) => void;
  onLanguageChange: (language: string) => void;
  onEnabledChange?: (enabled: boolean) => void;
  onTtsSpeedChange?: (speed: number) => void;
}
/* eslint-enable no-unused-vars */

const VoiceSelector: React.FC<VoiceSelectorProps> = ({
  voiceProvider,
  voiceName,
  language,
  enabled = true,
  ttsSpeed = 1.0,
  voices,
  onVoiceProviderChange,
  onVoiceNameChange,
  onLanguageChange,
  onEnabledChange,
  onTtsSpeedChange,
}) => {
  // Filter voices by provider AND language (strict filtering)
  const availableVoices = voices.filter(voice => {
    if (voice.provider !== voiceProvider) return false;
    const voiceLangBase = (voice.language || 'en').toLowerCase().split(/[-_]/)[0];
    const selectedLangBase = (language || 'en').toLowerCase().split(/[-_]/)[0];
    return voiceLangBase === selectedLangBase;
  });

  const handleProviderChange = (newProvider: string) => {
    onVoiceProviderChange(newProvider);
    // Find first voice for the new provider that matches current language
    const selectedLangBase = (language || 'en').toLowerCase().split(/[-_]/)[0];
    const firstVoice = voices.find(voice => {
      if (voice.provider !== newProvider) return false;
      const voiceLangBase = (voice.language || 'en').toLowerCase().split(/[-_]/)[0];
      return voiceLangBase === selectedLangBase;
    });
    if (firstVoice) onVoiceNameChange(firstVoice.name);
  };

  const handleLanguageChange = (newLanguage: string) => {
    onLanguageChange(newLanguage);
    const selectedLangBase = newLanguage.toLowerCase().split(/[-_]/)[0];
    const firstVoice = voices.find(voice => {
      if (voice.provider !== voiceProvider) return false;
      const voiceLangBase = (voice.language || 'en').toLowerCase().split(/[-_]/)[0];
      return voiceLangBase === selectedLangBase;
    });
    if (firstVoice) onVoiceNameChange(firstVoice.name);
  };

  const getProviderName = (p: string) => ({ kokoro: 'Kokoro', piper: 'Piper', edge: 'Edge' }[p] || p);
  const getLangName = (l: string) => ({
    en: 'English', fr: 'French', es: 'Spanish', de: 'German', it: 'Italian',
    pt: 'Portuguese', ru: 'Russian', ja: 'Japanese', ko: 'Korean', zh: 'Chinese'
  }[l] || l);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={6} md={3}>
          <FormControlLabel
            control={<Switch checked={enabled} onChange={(e) => onEnabledChange?.(e.target.checked)} />}
            label="Enable Voice Over"
          />
        </Grid>

        {enabled && (
          <>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Provider</InputLabel>
                <Select value={voiceProvider} onChange={(e) => handleProviderChange(e.target.value)} label="Provider">
                  {VOICE_PROVIDERS.map((p) => <MenuItem key={p} value={p}>{getProviderName(p)}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Language</InputLabel>
                <Select value={(language || 'en').split('-')[0].toLowerCase()} onChange={(e) => handleLanguageChange(e.target.value)} label="Language">
                  {LANGUAGES.map((l) => <MenuItem key={l} value={l}>{getLangName(l)}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Voice</InputLabel>
                <Select 
                  value={availableVoices.length > 0 ? voiceName : ''} 
                  onChange={(e) => onVoiceNameChange(e.target.value)} 
                  label="Voice" 
                  disabled={availableVoices.length === 0}
                >
                  {availableVoices.map((v) => (
                    <MenuItem key={v.name} value={v.name}>{v.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {onTtsSpeedChange && (
              <Grid item xs={12}>
                <Typography variant="body2" gutterBottom>Speed: {ttsSpeed}x</Typography>
                <Slider
                  value={ttsSpeed}
                  onChange={(_, v) => onTtsSpeedChange(Array.isArray(v) ? v[0] : v)}
                  min={0.5} max={2.0} step={0.1}
                  marks={[{ value: 0.5, label: '0.5x' }, { value: 1, label: '1x' }, { value: 2, label: '2x' }]}
                  size="small"
                />
              </Grid>
            )}
          </>
        )}
      </Grid>
    </Box>
  );
};

export default VoiceSelector;