import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  alpha,
  useTheme,
  Chip,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Save as SaveIcon,
  CheckCircle as ConfiguredIcon,
  Psychology as LlmIcon,
  Image as ImageIcon,
  Hub as HubIcon,
} from '@mui/icons-material';
import ConfigSettingField from './ConfigSettingField';
import { useConfigSettings } from './useConfigSettings';

// Group providers by category for visual organization
const PROVIDER_GROUPS = [
  {
    label: 'LLM Providers',
    icon: <LlmIcon />,
    color: 'primary' as const,
    providers: ['OpenAI', 'DeepSeek', 'Anthropic', 'Groq', 'Gemini', 'Mistral', 'Perplexity', 'xAI', 'Cohere', 'Cerebras', 'Moonshot'],
  },
  {
    label: 'Image & Media',
    icon: <ImageIcon />,
    color: 'secondary' as const,
    providers: ['Pollinations', 'Together', 'HuggingFace', 'Fireworks'],
  },
  {
    label: 'Routing & Aggregators',
    icon: <HubIcon />,
    color: 'info' as const,
    providers: ['OpenRouter', 'SambaNova', 'Nebius', 'Inception', 'Z.AI', 'AnyLLM'],
  },
];

const AIProvidersTab: React.FC = () => {
  const theme = useTheme();
  const {
    editValues, loading, saving, error, success,
    setValue, saveCategory, getSettingsForCategory,
  } = useConfigSettings();

  const settings = getSettingsForCategory('ai_providers');

  // Group settings by provider name
  const providerMap = useMemo(() => {
    const grouped: Record<string, { key: string; setting: typeof settings[string] }[]> = {};
    for (const [key, setting] of Object.entries(settings)) {
      const provider = (setting as any).provider || 'Other';
      if (!grouped[provider]) grouped[provider] = [];
      grouped[provider].push({ key, setting });
    }
    return grouped;
  }, [settings]);

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  return (
    <Box>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="body2" color="text.secondary">
          API keys and endpoints for AI providers. Providers with a key configured become available in chat via AnyLLM.
        </Typography>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveCategory('ai_providers')} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Provider groups */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {PROVIDER_GROUPS.map((group) => {
          const groupProviders = group.providers
            .filter((name) => providerMap[name]?.length)
            .map((name) => ({ name, fields: providerMap[name] }));
          if (groupProviders.length === 0) return null;

          const themeColor = theme.palette[group.color].main;

          return (
            <Card elevation={1} key={group.label}>
              <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
                {/* Section header */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2.5 }}>
                  <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(themeColor, 0.1), color: themeColor }}>
                    {group.icon}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" fontWeight="medium">{group.label}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {groupProviders.filter(p => p.fields.some(f => f.setting.configured && f.setting.type === 'password')).length} of {groupProviders.length} configured
                    </Typography>
                  </Box>
                </Box>

                {/* Provider rows */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {groupProviders.map((provider) => {
                    const hasKey = provider.fields.some(
                      (f) => f.setting.configured && f.setting.type === 'password'
                    );

                    return (
                      <Box
                        key={provider.name}
                        sx={{
                          p: 2,
                          borderRadius: 1.5,
                          border: '1px solid',
                          borderColor: hasKey ? alpha(theme.palette.success.main, 0.3) : 'divider',
                          backgroundColor: hasKey ? alpha(theme.palette.success.main, 0.02) : 'transparent',
                        }}
                      >
                        {/* Provider name + status */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                          {hasKey && <ConfiguredIcon sx={{ fontSize: 16, color: 'success.main' }} />}
                          <Typography variant="subtitle2" fontWeight={600}>{provider.name}</Typography>
                          {hasKey && (
                            <Chip label="Active" size="small" color="success" variant="outlined"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          )}
                        </Box>

                        {/* Fields grid */}
                        <Grid container spacing={1.5}>
                          {provider.fields.map((f) => (
                            <Grid item xs={12} sm={6} md={f.setting.type === 'password' ? 6 : 4} key={f.key}>
                              <ConfigSettingField
                                settingKey={f.key}
                                setting={f.setting}
                                value={editValues[f.key] ?? f.setting.value}
                                onChange={setValue}
                              />
                            </Grid>
                          ))}
                        </Grid>
                      </Box>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          );
        })}
      </Box>
    </Box>
  );
};

export default AIProvidersTab;
