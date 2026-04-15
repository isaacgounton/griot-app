import { useState, useCallback } from 'react';
import { Box, Typography, IconButton, useMediaQuery, useTheme } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ScienceIcon from '@mui/icons-material/Science';

import AISceneBuilder from '../../../components/videoCreation/AISceneBuilder';
import SettingsSidebar from '../components/SettingsSidebar';
import { DEFAULT_FORM_STATE } from '../types';
import type { FormState } from '../types';
import type { VideoScene } from '../../../types/contentCreation';

interface SceneBuilderViewProps {
  onBack: () => void;
}

export default function SceneBuilderView({ onBack }: SceneBuilderViewProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [formState, setFormState] = useState<FormState>({ ...DEFAULT_FORM_STATE });
  const [scenes, setScenes] = useState<VideoScene[]>([{ text: '', duration: 3, searchTerms: [''] }]);

  const handleFormChange = useCallback(<K extends keyof FormState>(field: K, value: FormState[K]) => {
    setFormState(prev => ({ ...prev, [field]: value }));
  }, []);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <IconButton onClick={onBack} size="small"><ArrowBackIcon /></IconButton>
        <ScienceIcon color="primary" />
        <Typography variant="h6" fontWeight={600}>AI Scene Builder</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
          Research, generate scenes, and create
        </Typography>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Main: AISceneBuilder */}
        <Box sx={{ flex: isMobile ? 1 : '0 0 65%', overflow: 'auto', p: 2 }}>
          <AISceneBuilder
            scenes={scenes}
            onChange={setScenes}
            voiceProvider={formState.voiceProvider}
            voiceName={formState.voiceName}
            resolution={`${formState.imageWidth}x${formState.imageHeight}`}
            onVoiceProviderChange={v => handleFormChange('voiceProvider', v)}
            onVoiceNameChange={v => handleFormChange('voiceName', v)}
            onResolutionChange={res => {
              const [w, h] = res.split('x').map(Number);
              handleFormChange('imageWidth', w);
              handleFormChange('imageHeight', h);
            }}
            footageProvider={formState.footageProvider}
            footageQuality={formState.footageQuality}
            searchSafety={formState.searchSafety}
            mediaType={formState.mediaType}
            aiVideoProvider={formState.aiVideoProvider}
            aiVideoModel={formState.aiVideoModel}
            aiImageProvider={formState.aiImageProvider}
            aiImageModel={formState.aiImageModel}
            backgroundMusic={formState.backgroundMusic}
            backgroundMusicVolume={formState.backgroundMusicVolume}
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
            ttsSpeed={formState.ttsSpeed}
            enableVoiceOver={formState.enableVoiceOver}
            enableBuiltInAudio={formState.enableBuiltInAudio}
            effectType={formState.effectType}
            zoomSpeed={formState.zoomSpeed}
            panDirection={formState.panDirection}
            kenBurnsKeypoints={formState.kenBurnsKeypoints}
          />
        </Box>

        {/* Sidebar: Settings */}
        {!isMobile && (
          <Box sx={{ flex: '0 0 35%', borderLeft: 1, borderColor: 'divider', overflow: 'auto', p: 1 }}>
            <SettingsSidebar formState={formState} onFormChange={handleFormChange} />
          </Box>
        )}
      </Box>

      {/* Mobile settings FAB */}
      {isMobile && <SettingsSidebar formState={formState} onFormChange={handleFormChange} />}
    </Box>
  );
}
