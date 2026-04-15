import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  alpha,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Psychology as AIIcon,
  RecordVoiceOver as SpeechIcon,
  Email as EmailIcon,
  Extension as IntegrationsIcon,
  Info as SystemIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import GeneralTab from './GeneralTab';
import AIProvidersTab from './AIProvidersTab';
import SpeechMediaTab from './SpeechMediaTab';
import EmailAuthTab from './EmailAuthTab';
import IntegrationsTab from './IntegrationsTab';
import SystemTab from './SystemTab';

const Settings: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { userRole } = useAuth();
  const [tab, setTab] = useState(0);

  const isAdmin = userRole === 'admin';

  // All users see General; admin sees all tabs
  const tabs = [
    { label: 'General', icon: <SettingsIcon /> },
    ...(isAdmin ? [
      { label: 'AI Providers', icon: <AIIcon /> },
      { label: 'Speech & Media', icon: <SpeechIcon /> },
      { label: 'Email & Auth', icon: <EmailIcon /> },
      { label: 'Integrations', icon: <IntegrationsIcon /> },
      { label: 'System', icon: <SystemIcon /> },
    ] : []),
  ];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: { xs: 2, sm: 3 } }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            color: theme.palette.primary.main
          }}
        >
          <SettingsIcon />
        </Box>
        <Box>
          <Typography variant="h4" fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
            Settings
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            Configure system preferences and services
          </Typography>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          variant={isMobile ? 'scrollable' : 'standard'}
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 500,
              minHeight: 48,
              gap: 1,
            }
          }}
        >
          {tabs.map((t, i) => (
            <Tab
              key={i}
              icon={t.icon}
              iconPosition="start"
              label={t.label}
            />
          ))}
        </Tabs>
      </Box>

      {/* Tab Content */}
      {tab === 0 && <GeneralTab />}
      {isAdmin && tab === 1 && <AIProvidersTab />}
      {isAdmin && tab === 2 && <SpeechMediaTab />}
      {isAdmin && tab === 3 && <EmailAuthTab />}
      {isAdmin && tab === 4 && <IntegrationsTab />}
      {isAdmin && tab === 5 && <SystemTab />}
    </Box>
  );
};

export default Settings;
