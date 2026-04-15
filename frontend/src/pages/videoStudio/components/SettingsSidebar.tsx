import { useState, useEffect } from 'react';
import {
  Box, Typography, Accordion, AccordionSummary, AccordionDetails,
  Drawer, IconButton, useMediaQuery, useTheme,
  FormControl, InputLabel, Select, MenuItem, Grid,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SettingsIcon from '@mui/icons-material/Settings';

import VoiceSelector from '../../../components/settings/VoiceSelectorSettings';
import UnifiedMediaProviderSettings from '../../../components/settings/UnifiedMediaProviderSettings';
import CaptionSettings from '../../../components/settings/CaptionSettings';
import BackgroundMusicSettings from '../../../components/settings/BackgroundMusicSettings';
import ImageToVideoSettings from '../../../components/settings/ImageToVideoSettings';
import { useVoices } from '../../../hooks/useContentCreation';
import { VIDEO_ORIENTATIONS } from '../../../constants/videoSettings';
import type { FormState } from '../types';

interface SettingsSidebarProps {
  formState: FormState;
  onFormChange: <K extends keyof FormState>(field: K, value: FormState[K]) => void;
}

export default function SettingsSidebar({ formState, onFormChange }: SettingsSidebarProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { voices, fetchVoices } = useVoices();

  // Fetch voices on mount
  useEffect(() => {
    if (voices.length === 0) fetchVoices();
  }, [voices.length, fetchVoices]);

  // Derive current aspect ratio key from dimensions
  const currentOrientation = VIDEO_ORIENTATIONS.find(
    o => o.width === formState.imageWidth && o.height === formState.imageHeight
  )?.value || 'portrait';

  const content = (
    <Box sx={{ p: isMobile ? 2 : 0, width: isMobile ? 320 : 'auto' }}>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, px: 1 }}>
        Settings
      </Typography>

      {/* Resolution / Video */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2" fontWeight={600}>Video</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Resolution</InputLabel>
                <Select
                  value={currentOrientation}
                  label="Resolution"
                  onChange={e => {
                    const o = VIDEO_ORIENTATIONS.find(v => v.value === e.target.value);
                    if (o) {
                      onFormChange('imageWidth', o.width);
                      onFormChange('imageHeight', o.height);
                      onFormChange('aspectRatio', o.value === 'portrait' ? '9:16' : o.value === 'landscape' ? '16:9' : '1:1');
                    }
                  }}
                >
                  {VIDEO_ORIENTATIONS.map(o => (
                    <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Frame Rate</InputLabel>
                <Select
                  value={formState.frameRate}
                  label="Frame Rate"
                  onChange={e => onFormChange('frameRate', Number(e.target.value))}
                >
                  {[24, 30, 60].map(r => (
                    <MenuItem key={r} value={r}>{r} fps</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Crossfade</InputLabel>
                <Select
                  value={formState.crossfadeDuration}
                  label="Crossfade"
                  onChange={e => onFormChange('crossfadeDuration', Number(e.target.value))}
                >
                  {[0, 0.2, 0.3, 0.5, 0.8, 1.0].map(d => (
                    <MenuItem key={d} value={d}>{d === 0 ? 'None' : `${d}s`}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Voice */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2" fontWeight={600}>Voice</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <VoiceSelector
            voiceProvider={formState.voiceProvider}
            voiceName={formState.voiceName}
            language={formState.language}
            enabled={formState.enableVoiceOver}
            ttsSpeed={formState.ttsSpeed}
            voices={voices}
            onVoiceProviderChange={v => onFormChange('voiceProvider', v)}
            onVoiceNameChange={v => onFormChange('voiceName', v)}
            onLanguageChange={v => onFormChange('language', v)}
            onEnabledChange={v => onFormChange('enableVoiceOver', v)}
            onTtsSpeedChange={v => onFormChange('ttsSpeed', v)}
          />
        </AccordionDetails>
      </Accordion>

      {/* Media Provider */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2" fontWeight={600}>Media</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <UnifiedMediaProviderSettings
            mediaType={formState.mediaType as 'video' | 'image'}
            provider={formState.footageProvider as 'pexels' | 'pixabay' | 'ai_generated'}
            aiVideoProvider={formState.aiVideoProvider}
            aiImageProvider={formState.aiImageProvider}
            aiVideoModel={formState.aiVideoModel}
            aiImageModel={formState.aiImageModel}
            searchSafety={formState.searchSafety}
            quality={formState.footageQuality}
            searchTermsPerScene={formState.searchTermsPerScene}
            guidanceScale={formState.guidanceScale}
            inferenceSteps={formState.inferenceSteps}
            onMediaTypeChange={v => onFormChange('mediaType', v)}
            onProviderChange={v => onFormChange('footageProvider', v)}
            onAiVideoProviderChange={v => onFormChange('aiVideoProvider', v)}
            onAiImageProviderChange={v => onFormChange('aiImageProvider', v)}
            onAiVideoModelChange={v => onFormChange('aiVideoModel', v)}
            onAiImageModelChange={v => onFormChange('aiImageModel', v)}
            onSearchSafetyChange={v => onFormChange('searchSafety', v)}
            onQualityChange={v => onFormChange('footageQuality', v)}
            onSearchTermsPerSceneChange={v => onFormChange('searchTermsPerScene', v)}
            onGuidanceScaleChange={v => onFormChange('guidanceScale', v)}
            onInferenceStepsChange={v => onFormChange('inferenceSteps', v)}
          />
        </AccordionDetails>
      </Accordion>

      {/* Captions */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2" fontWeight={600}>Captions</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <CaptionSettings
            enableCaptions={formState.enableCaptions}
            captionStyle={formState.captionStyle}
            captionColor={formState.captionColor}
            highlightColor={formState.highlightColor}
            captionPosition={formState.captionPosition}
            fontSize={formState.fontSize}
            fontFamily={formState.fontFamily}
            wordsPerLine={formState.wordsPerLine}
            marginV={formState.marginV}
            outlineWidth={formState.outlineWidth}
            allCaps={formState.allCaps}
            onEnableCaptionsChange={v => onFormChange('enableCaptions', v)}
            onCaptionStyleChange={v => onFormChange('captionStyle', v)}
            onCaptionColorChange={v => onFormChange('captionColor', v)}
            onHighlightColorChange={v => onFormChange('highlightColor', v)}
            onCaptionPositionChange={v => onFormChange('captionPosition', v)}
            onFontSizeChange={v => onFormChange('fontSize', v)}
            onFontFamilyChange={v => onFormChange('fontFamily', v)}
            onWordsPerLineChange={v => onFormChange('wordsPerLine', v)}
            onMarginVChange={v => onFormChange('marginV', v)}
            onOutlineWidthChange={v => onFormChange('outlineWidth', v)}
            onAllCapsChange={v => onFormChange('allCaps', v)}
          />
        </AccordionDetails>
      </Accordion>

      {/* Background Music */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2" fontWeight={600}>Music</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <BackgroundMusicSettings
            backgroundMusic={formState.backgroundMusic}
            backgroundMusicVolume={formState.backgroundMusicVolume}
            musicDuration={formState.musicDuration}
            onBackgroundMusicChange={v => onFormChange('backgroundMusic', v)}
            onBackgroundMusicVolumeChange={v => onFormChange('backgroundMusicVolume', v)}
            onMusicDurationChange={v => onFormChange('musicDuration', v)}
          />
        </AccordionDetails>
      </Accordion>

      {/* Image-to-Video Effects (only when media type is image) */}
      {formState.mediaType === 'image' && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2" fontWeight={600}>Motion Effects</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ImageToVideoSettings
              effectType={formState.effectType}
              zoomSpeed={formState.zoomSpeed}
              panDirection={formState.panDirection}
              onEffectTypeChange={v => onFormChange('effectType', v)}
              onZoomSpeedChange={v => onFormChange('zoomSpeed', v)}
              onPanDirectionChange={v => onFormChange('panDirection', v)}
            />
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );

  // Mobile: floating button + drawer
  if (isMobile) {
    return (
      <>
        <IconButton
          onClick={() => setDrawerOpen(true)}
          sx={{ position: 'fixed', bottom: 16, right: 16, bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' }, zIndex: 10 }}
        >
          <SettingsIcon />
        </IconButton>
        <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          {content}
        </Drawer>
      </>
    );
  }

  // Desktop: inline sidebar
  return (
    <Box sx={{ overflow: 'auto', height: '100%' }}>
      {content}
    </Box>
  );
}
