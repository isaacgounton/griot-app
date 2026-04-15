import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { directApi } from '../utils/api';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Alert,
  alpha,
  useTheme,
  Divider,
  Avatar,
  IconButton,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Save as SaveIcon,
  Edit as EditIcon,
  Cancel as CancelIcon,
  PhotoCamera as PhotoCameraIcon,
  Visibility,
  VisibilityOff,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  role: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

interface PasswordChangeData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const Profile: React.FC = () => {
  const theme = useTheme();
  const { apiKey } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [profile, setProfile] = useState<UserProfile>({
    id: '',
    username: '',
    email: '',
    full_name: '',
    role: 'user',
    created_at: '',
    is_active: true
  });

  const [editedProfile, setEditedProfile] = useState<UserProfile>(profile);

  const [passwordData, setPasswordData] = useState<PasswordChangeData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await directApi.getUserProfile();

      if (!response.success) {
        throw new Error(response.error || 'Failed to load profile');
      }

      if (response.data) {
        setProfile(response.data);
        setEditedProfile(response.data);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (apiKey) {
      loadProfile();
    }
  }, [apiKey, loadProfile]);

  const handleEditToggle = () => {
    if (editMode) {
      setEditedProfile(profile);
    }
    setEditMode(!editMode);
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updateData = {
        username: editedProfile.username,
        email: editedProfile.email,
        full_name: editedProfile.full_name
      };

      const response = await directApi.updateUserProfile(updateData);

      if (!response.success) {
        throw new Error(response.error || 'Failed to update profile');
      }

      if (response.data) {
        setProfile(response.data);
        setEditedProfile(response.data);
        setSuccess('Profile updated successfully!');
        setEditMode(false);

        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    setError(null);
    setSuccess(null);

    // Validate passwords
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      setError('All password fields are required');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    setSaving(true);

    try {
      const response = await directApi.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to change password');
      }

      setSuccess('Password changed successfully!');
      setPasswordDialogOpen(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Error changing password:', err);
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError(null);
    setSuccess(null);

    try {
      const response = await directApi.uploadAvatar(file);
      if (!response.success) {
        throw new Error(response.error || 'Failed to upload avatar');
      }
      if (response.data) {
        setProfile(response.data);
        setEditedProfile(response.data);
        setSuccess('Avatar updated successfully!');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      console.error('Error uploading avatar:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload avatar');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2, mb: { xs: 2, sm: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              color: theme.palette.primary.main
            }}
          >
            <PersonIcon />
          </Box>
          <Box>
            <Typography variant="h4" fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
              My Profile
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Manage your account information and preferences
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* Profile Card */}
        <Grid item xs={12} md={4}>
          <Card elevation={1}>
            <CardContent sx={{ textAlign: 'center', p: { xs: 2, sm: 4 } }}>
              <Box sx={{ position: 'relative', display: 'inline-block', mb: 2 }}>
                <Avatar
                  src={profile.avatar_url || undefined}
                  sx={{
                    width: { xs: 80, sm: 120 },
                    height: { xs: 80, sm: 120 },
                    bgcolor: theme.palette.primary.main,
                    fontSize: '3rem',
                    fontWeight: 'bold'
                  }}
                >
                  {profile.full_name ? profile.full_name.charAt(0).toUpperCase() : profile.username.charAt(0).toUpperCase()}
                </Avatar>
                <Tooltip title="Upload Photo">
                  <IconButton
                    component="label"
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      bgcolor: theme.palette.background.paper,
                      border: `2px solid ${theme.palette.divider}`,
                      '&:hover': {
                        bgcolor: theme.palette.action.hover
                      }
                    }}
                  >
                    <PhotoCameraIcon fontSize="small" />
                    <input
                      type="file"
                      hidden
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      onChange={handleAvatarUpload}
                    />
                  </IconButton>
                </Tooltip>
              </Box>

              <Typography variant="h5" fontWeight="bold" gutterBottom>
                {profile.full_name || profile.username}
              </Typography>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                @{profile.username}
              </Typography>

              <Box sx={{ mt: 2, mb: 3 }}>
                <Box
                  sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.5,
                    px: 2,
                    py: 0.5,
                    borderRadius: 2,
                    bgcolor: alpha(
                      profile.role === 'admin' ? theme.palette.primary.main : theme.palette.secondary.main,
                      0.1
                    ),
                    color: profile.role === 'admin' ? theme.palette.primary.main : theme.palette.secondary.main
                  }}
                >
                  <Typography variant="caption" fontWeight="bold" textTransform="uppercase">
                    {profile.role}
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ textAlign: 'left' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Member Since:</strong> {formatDate(profile.created_at)}
                </Typography>
                {profile.last_login && (
                  <Typography variant="body2" color="text.secondary">
                    <strong>Last Login:</strong> {formatDate(profile.last_login)}
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Card elevation={1}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" fontWeight="bold">
                  Personal Information
                </Typography>
                <Button
                  startIcon={editMode ? <CancelIcon /> : <EditIcon />}
                  onClick={handleEditToggle}
                  disabled={saving}
                >
                  {editMode ? 'Cancel' : 'Edit'}
                </Button>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Username"
                    value={editMode ? editedProfile.username : profile.username}
                    onChange={(e) => setEditedProfile({ ...editedProfile, username: e.target.value })}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    value={editMode ? editedProfile.full_name : profile.full_name}
                    onChange={(e) => setEditedProfile({ ...editedProfile, full_name: e.target.value })}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email Address"
                    type="email"
                    value={editMode ? editedProfile.email : profile.email}
                    onChange={(e) => setEditedProfile({ ...editedProfile, email: e.target.value })}
                    disabled={!editMode}
                    InputProps={{
                      startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
              </Grid>

              {editMode && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={handleEditToggle}
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Security Card */}
          <Card elevation={1} sx={{ mt: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 1,
                    backgroundColor: alpha(theme.palette.error.main, 0.1),
                    color: theme.palette.error.main
                  }}
                >
                  <LockIcon />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    Security
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Manage your password and security settings
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body1" fontWeight="medium">
                    Password
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last changed: Never or hidden for security
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<LockIcon />}
                  onClick={() => setPasswordDialogOpen(true)}
                >
                  Change Password
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Password Change Dialog */}
      <Dialog
        open={passwordDialogOpen}
        onClose={() => !saving && setPasswordDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LockIcon color="primary" />
            Change Password
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Current Password"
              type={showCurrentPassword ? 'text' : 'password'}
              value={passwordData.currentPassword}
              onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    edge="end"
                  >
                    {showCurrentPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                )
              }}
            />

            <TextField
              fullWidth
              label="New Password"
              type={showNewPassword ? 'text' : 'password'}
              value={passwordData.newPassword}
              onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
              sx={{ mb: 2 }}
              helperText="Password must be at least 8 characters long"
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    edge="end"
                  >
                    {showNewPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                )
              }}
            />

            <TextField
              fullWidth
              label="Confirm New Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={passwordData.confirmPassword}
              onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                )
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setPasswordDialogOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handlePasswordChange}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <CheckCircleIcon />}
          >
            {saving ? 'Changing...' : 'Change Password'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Profile;
