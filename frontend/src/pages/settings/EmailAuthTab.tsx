import React, { useState } from 'react';
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
  Send as SendIcon,
  Email as EmailIcon,
  VpnKey as OAuthIcon,
} from '@mui/icons-material';
import ConfigSettingField from './ConfigSettingField';
import { useConfigSettings } from './useConfigSettings';
import { directApi } from '../../utils/api';

const EMAIL_KEYS = ['RESEND_API_KEY', 'EMAIL_FROM_ADDRESS', 'EMAIL_FROM_NAME'];

const OAUTH_SECTIONS = [
  { title: 'Google OAuth', keys: ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'] },
  { title: 'GitHub OAuth', keys: ['GITHUB_CLIENT_ID', 'GITHUB_CLIENT_SECRET'] },
  { title: 'Discord OAuth', keys: ['DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET'] },
];

const EmailAuthTab: React.FC = () => {
  const theme = useTheme();
  const {
    editValues, loading, saving, error, success,
    setValue, saveCategory, getSettingsForCategory,
  } = useConfigSettings();

  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const settings = getSettingsForCategory('email_auth');

  const handleSendTestEmail = async () => {
    setSendingTestEmail(true);
    setEmailMessage(null);
    try {
      const profileResp = await directApi.getUserProfile();
      if (!profileResp.success || !profileResp.data) {
        throw new Error('Failed to load profile');
      }
      const result = await directApi.sendTestEmail({
        recipient_email: profileResp.data.email,
        subject: 'Test Email from Griot',
        message: 'This is a test email to verify your email service configuration.',
      });
      if (result.success) {
        setEmailMessage({ type: 'success', text: `Test email sent to ${profileResp.data.email}` });
      } else {
        throw new Error(result.error);
      }
    } catch (err) {
      setEmailMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to send test email' });
    } finally {
      setSendingTestEmail(false);
      setTimeout(() => setEmailMessage(null), 5000);
    }
  };

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  // Flatten OAuth fields that exist in settings
  const oauthFields = OAUTH_SECTIONS.flatMap((section) =>
    section.keys.filter((k) => k in settings).map((key) => ({
      key,
      provider: section.title,
    }))
  );

  return (
    <Box>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Email service (Resend) and OAuth provider credentials.
        </Typography>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={() => saveCategory('email_auth')} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Email Service Card */}
        <Card elevation={1}>
          <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(theme.palette.primary.main, 0.1), color: theme.palette.primary.main }}>
                <EmailIcon />
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" fontWeight="medium">Email Service</Typography>
                <Typography variant="body2" color="text.secondary">Resend API for transactional emails and notifications</Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={sendingTestEmail ? <CircularProgress size={16} /> : <SendIcon />}
                onClick={handleSendTestEmail}
                disabled={sendingTestEmail}
              >
                {sendingTestEmail ? 'Sending...' : 'Send Test'}
              </Button>
            </Box>

            <Grid container spacing={1.5}>
              {EMAIL_KEYS.map((key) =>
                settings[key] ? (
                  <Grid item xs={12} sm={6} md={4} key={key}>
                    <ConfigSettingField
                      settingKey={key}
                      setting={settings[key]}
                      value={editValues[key] ?? settings[key].value}
                      onChange={setValue}
                    />
                  </Grid>
                ) : null
              )}
            </Grid>

            {emailMessage && (
              <Alert severity={emailMessage.type} sx={{ mt: 2 }}>
                {emailMessage.text}
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* OAuth Providers Card */}
        {oauthFields.length > 0 && (
          <Card elevation={1}>
            <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(theme.palette.secondary.main, 0.1), color: theme.palette.secondary.main }}>
                  <OAuthIcon />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight="medium">OAuth Providers</Typography>
                  <Typography variant="body2" color="text.secondary">Social login credentials for Google, GitHub, and Discord</Typography>
                </Box>
              </Box>

              <Grid container spacing={1.5}>
                {oauthFields.map(({ key }) => (
                  <Grid item xs={12} sm={6} md={4} key={key}>
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
        )}
      </Box>
    </Box>
  );
};

export default EmailAuthTab;
