import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Save as SaveIcon,
  Share as SocialIcon,
  Payment as PaymentIcon,
  Search as SearchIcon,
  Language as WebIcon,
  SettingsInputComponent as InternalIcon,
} from '@mui/icons-material';
import ConfigSettingField from './ConfigSettingField';
import { useConfigSettings } from './useConfigSettings';

const SECTIONS = [
  {
    title: 'Social Media (Postiz)',
    description: 'Schedule and publish content to social media platforms',
    icon: <SocialIcon />,
    color: 'primary' as const,
    keys: ['POSTIZ_API_KEY', 'POSTIZ_API_URL'],
  },
  {
    title: 'Payments (Stripe)',
    description: 'Payment processing and subscription management',
    icon: <PaymentIcon />,
    color: 'secondary' as const,
    keys: ['STRIPE_PRICE_ID', 'STRIPE_WEBHOOK_SECRET'],
  },
  {
    title: 'Search & News',
    description: 'Web search and news content for research features',
    icon: <SearchIcon />,
    color: 'warning' as const,
    keys: ['NEWS_API_KEY', 'GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID'],
  },
  {
    title: 'Web Automation (Browserless)',
    description: 'Headless browser for web scraping and automation',
    icon: <WebIcon />,
    color: 'primary' as const,
    keys: ['BROWSERLESS_BASE_URL', 'BROWSERLESS_TOKEN'],
  },
  {
    title: 'Internal Services',
    description: 'Internal agent API connection',
    icon: <InternalIcon />,
    color: 'info' as const,
    keys: ['AGENT_INTERNAL_API_BASE_URL'],
  },
];

const IntegrationsTab: React.FC = () => {
  const theme = useTheme();
  const {
    editValues, loading, saving, error, success,
    setValue, saveCategory, getSettingsForCategory,
  } = useConfigSettings();

  const settings = getSettingsForCategory('integrations');

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  return (
    <Box>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Third-party integrations: social media, payments, analytics, search, and web tools.
        </Typography>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveCategory('integrations')} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Integration sections in Cards */}
      <Grid container spacing={3}>
        {SECTIONS.map((section) => {
          const visibleKeys = section.keys.filter((k) => k in settings);
          if (visibleKeys.length === 0) return null;
          const themeColor = theme.palette[section.color].main;

          return (
            <Grid item xs={12} md={visibleKeys.length <= 2 ? 6 : 12} key={section.title}>
              <Card elevation={1} sx={{ height: '100%' }}>
                <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(themeColor, 0.1), color: themeColor }}>
                      {section.icon}
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="medium">{section.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{section.description}</Typography>
                    </Box>
                  </Box>
                  <Grid container spacing={1.5}>
                    {visibleKeys.map((key) => (
                      <Grid item xs={12} sm={visibleKeys.length <= 2 ? 12 : 6} md={visibleKeys.length <= 2 ? 12 : 4} key={key}>
                        <ConfigSettingField
                          settingKey={key}
                          setting={settings[key]}
                          value={editValues[key] ?? settings[key].value}
                          onChange={setValue}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default IntegrationsTab;
