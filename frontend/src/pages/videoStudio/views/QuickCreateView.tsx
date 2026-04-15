import { useState, useCallback } from 'react';
import { Box, Typography, IconButton, useMediaQuery, useTheme } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import BoltIcon from '@mui/icons-material/Bolt';

import VideoCreatorTab from '../../../components/videoCreation/tabs/VideoCreatorTab';
import SettingsSidebar from '../components/SettingsSidebar';
import { DEFAULT_FORM_STATE } from '../types';
import type { FormState } from '../types';

interface QuickCreateViewProps {
  onBack: () => void;
}

export default function QuickCreateView({ onBack }: QuickCreateViewProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [formState, setFormState] = useState<FormState>({ ...DEFAULT_FORM_STATE });

  const handleFormChange = useCallback(<K extends keyof FormState>(field: K, value: FormState[K]) => {
    setFormState(prev => ({ ...prev, [field]: value }));
  }, []);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <IconButton onClick={onBack} size="small"><ArrowBackIcon /></IconButton>
        <BoltIcon color="primary" />
        <Typography variant="h6" fontWeight={600}>Quick Create</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
          Topic to video in one click
        </Typography>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Main: VideoCreatorTab */}
        <Box sx={{ flex: isMobile ? 1 : '0 0 65%', overflow: 'auto', p: 2 }}>
          <VideoCreatorTab formState={formState} onFormChange={handleFormChange} />
        </Box>

        {/* Sidebar: Settings */}
        {!isMobile && (
          <Box sx={{ flex: '0 0 35%', borderLeft: 1, borderColor: 'divider', overflow: 'auto', p: 1 }}>
            <SettingsSidebar formState={formState} onFormChange={handleFormChange} />
          </Box>
        )}
      </Box>

      {/* Mobile settings FAB handled inside SettingsSidebar */}
      {isMobile && <SettingsSidebar formState={formState} onFormChange={handleFormChange} />}
    </Box>
  );
}
