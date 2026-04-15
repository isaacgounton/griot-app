import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  Alert,
  alpha,
  useTheme,
  Tooltip,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  RestorePageTwoTone as ResetIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { directApi } from '../../utils/api';
import ConfigSettingField from './ConfigSettingField';
import { useConfigSettings } from './useConfigSettings';

interface SettingsState {
  autoRefresh: boolean;
  emailNotifications: boolean;
  apiLogging: boolean;
  maxConcurrentJobs: number;
  defaultVideoResolution: string;
  storageRetentionDays: number;
}

const DEFAULTS: SettingsState = {
  autoRefresh: true,
  emailNotifications: true,
  apiLogging: true,
  maxConcurrentJobs: 5,
  defaultVideoResolution: '1080x1920',
  storageRetentionDays: 90,
};

const GENERAL_CONFIG_KEYS = [
  'CLEANUP_INTERVAL_HOURS', 'JOB_RETENTION_HOURS',
  'S3_CACHE_TTL_DAYS', 'ENABLE_S3_CLEANUP',
];

const GeneralTab: React.FC = () => {
  const theme = useTheme();
  const { apiKey: authApiKey, userRole } = useAuth();
  const [settings, setSettings] = useState<SettingsState>(DEFAULTS);
  const configHook = useConfigSettings();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    if (!authApiKey) return;
    try {
      const result = await directApi.getDashboardSettings();
      if (result.success && result.data) {
        const d = result.data;
        setSettings({
          autoRefresh: d.auto_refresh,
          emailNotifications: d.email_notifications,
          apiLogging: d.api_logging,
          maxConcurrentJobs: d.max_concurrent_jobs,
          defaultVideoResolution: d.default_video_resolution,
          storageRetentionDays: d.storage_retention_days,
        });
      }
    } catch {
      setError('Failed to load settings');
    }
  }, [authApiKey]);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await directApi.updateDashboardSettings({
        auto_refresh: settings.autoRefresh,
        email_notifications: settings.emailNotifications,
        api_logging: settings.apiLogging,
        max_concurrent_jobs: settings.maxConcurrentJobs,
        default_video_resolution: settings.defaultVideoResolution,
        storage_retention_days: settings.storageRetentionDays,
      });
      if (!result.success) throw new Error(result.error);
      setSuccess('Settings saved');
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const SettingCard: React.FC<{
    title: string;
    description: string;
    icon: React.ReactNode;
    children: React.ReactNode;
  }> = ({ title, description, icon, children }) => (
    <Card elevation={1}>
      <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 1,
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              color: theme.palette.primary.main
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="medium">{title}</Typography>
            <Typography variant="body2" color="text.secondary">{description}</Typography>
          </Box>
        </Box>
        {children}
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Save bar */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
        <Tooltip title="Reset to defaults">
          <IconButton onClick={() => setSettings(DEFAULTS)}>
            <ResetIcon />
          </IconButton>
        </Tooltip>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSave} disabled={loading}>
          {loading ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* General */}
        <Grid item xs={12} md={6}>
          <SettingCard title="General" description="Basic application preferences" icon={<SettingsIcon />}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={<Switch checked={settings.autoRefresh} onChange={(e) => setSettings(p => ({ ...p, autoRefresh: e.target.checked }))} />}
                label="Auto-refresh dashboard data"
              />
              <TextField
                label="Default Video Resolution"
                value={settings.defaultVideoResolution}
                onChange={(e) => setSettings(p => ({ ...p, defaultVideoResolution: e.target.value }))}
                helperText="Format: WIDTHxHEIGHT (e.g., 1080x1920)"
                fullWidth size="small"
              />
              <TextField
                label="Max Concurrent Jobs"
                type="number"
                value={settings.maxConcurrentJobs}
                onChange={(e) => setSettings(p => ({ ...p, maxConcurrentJobs: parseInt(e.target.value) || 5 }))}
                helperText="Maximum simultaneous jobs"
                fullWidth size="small"
                inputProps={{ min: 1, max: 20 }}
              />
            </Box>
          </SettingCard>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <SettingCard title="Notifications" description="Email and system notifications" icon={<NotificationsIcon />}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={<Switch checked={settings.emailNotifications} onChange={(e) => setSettings(p => ({ ...p, emailNotifications: e.target.checked }))} />}
                label="Email notifications for job completion"
              />
              <Typography variant="body2" color="text.secondary">
                Receive email notifications when video generation jobs complete or fail.
              </Typography>
            </Box>
          </SettingCard>
        </Grid>

        {/* Storage - Admin only */}
        {userRole === 'admin' && (
          <Grid item xs={12} md={6}>
            <SettingCard title="Storage" description="Data retention and cleanup" icon={<StorageIcon />}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Storage Retention (Days)"
                  type="number"
                  value={settings.storageRetentionDays}
                  onChange={(e) => setSettings(p => ({ ...p, storageRetentionDays: parseInt(e.target.value) || 90 }))}
                  helperText="Auto-delete content older than this"
                  fullWidth size="small"
                  inputProps={{ min: 1, max: 365 }}
                />
                <FormControlLabel
                  control={<Switch checked={settings.apiLogging} onChange={(e) => setSettings(p => ({ ...p, apiLogging: e.target.checked }))} />}
                  label="Enable detailed API logging"
                />
              </Box>
            </SettingCard>
          </Grid>
        )}
      </Grid>

      {/* Environment Config Settings - Admin only */}
      {userRole === 'admin' && !configHook.loading && (() => {
        const generalSettings = configHook.getSettingsForCategory('general');
        const visibleKeys = GENERAL_CONFIG_KEYS.filter((k) => k in generalSettings);
        if (visibleKeys.length === 0) return null;
        return (
          <>
            <Divider sx={{ my: 3 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TuneIcon fontSize="small" color="primary" />
                <Typography variant="subtitle1" fontWeight={600}>Video & Cleanup Defaults</Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={<SaveIcon />}
                onClick={() => configHook.saveCategory('general')}
                disabled={configHook.saving}
              >
                {configHook.saving ? 'Saving...' : 'Save Defaults'}
              </Button>
            </Box>
            {configHook.error && <Alert severity="error" sx={{ mb: 2 }}>{configHook.error}</Alert>}
            {configHook.success && <Alert severity="success" sx={{ mb: 2 }}>{configHook.success}</Alert>}
            <Grid container spacing={2}>
              {visibleKeys.map((key) => (
                <Grid item xs={12} sm={6} md={4} key={key}>
                  <ConfigSettingField
                    settingKey={key}
                    setting={generalSettings[key]}
                    value={configHook.editValues[key] ?? generalSettings[key].value}
                    onChange={configHook.setValue}
                  />
                </Grid>
              ))}
            </Grid>
          </>
        );
      })()}
    </Box>
  );
};

export default GeneralTab;
