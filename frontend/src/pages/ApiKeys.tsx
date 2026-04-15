import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Pagination,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Card,
  CardContent,
  Grid,
  alpha,
  useTheme,
  Snackbar,
} from '@mui/material';
import {
  VpnKey as ApiKeyIcon,
  Add as AddIcon,
  ContentCopy as CopyIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  Today as TodayIcon,
  TrendingUp as UsageIcon
} from '@mui/icons-material';
import { directApi } from '../utils/api';

interface ApiKey {
  id: string;
  name: string;
  key: string;
  userId: string;
  userEmail: string;
  isActive: boolean;
  createdAt: string;
  lastUsed?: string;
  expiresAt?: string;
  usageCount: number;
  rateLimit: number;
  permissions: string[];
}

interface User {
  id: string;
  email: string;
  role: string;
  fullName?: string;
}

interface ApiKeyFormData {
  name: string;
  user_id: string;
  rate_limit: number;
  expires_at: string;
  permissions: string[];
}

interface ApiKeysState {
  apiKeys: ApiKey[];
  users: User[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  searchQuery: string;
  selectedStatus: string;
  dialogOpen: boolean;
  editingKey: ApiKey | null;
  deleteDialogOpen: boolean;
  keyToDelete: ApiKey | null;
  snackbarOpen: boolean;
  snackbarMessage: string;
  newKeyDialogOpen: boolean;
  newlyCreatedKey: string | null;
}

const ApiKeys: React.FC = () => {
  const theme = useTheme();
  const { apiKey: authApiKey } = useAuth();
  const [state, setState] = useState<ApiKeysState>({
    apiKeys: [],
    users: [],
    loading: false,
    error: null,
    page: 1,
    totalPages: 1,
    searchQuery: '',
    selectedStatus: 'all',
    dialogOpen: false,
    editingKey: null,
    deleteDialogOpen: false,
    keyToDelete: null,
    snackbarOpen: false,
    snackbarMessage: '',
    newKeyDialogOpen: false,
    newlyCreatedKey: null
  });


  const loadApiKeys = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      if (!authApiKey) {
        throw new Error('No API key found');
      }

      const result = await directApi.listApiKeys(state.page, 50, state.searchQuery, state.selectedStatus);

      if (!result.success || !result.data) {
        throw new Error(result.error || 'Failed to fetch API keys');
      }

      // Transform snake_case API response to camelCase for frontend
      const transformedApiKeys = (result.data.api_keys || []).map((item) => ({
        id: item.id,
        name: item.name,
        key: item.key,
        userId: item.user_id,
        userEmail: item.user_email,
        isActive: item.is_active,
        createdAt: item.created_at,
        lastUsed: item.last_used,
        expiresAt: item.expires_at,
        usageCount: item.usage_count,
        rateLimit: item.rate_limit,
        permissions: item.permissions
      }));

      setState(prev => ({
        ...prev,
        apiKeys: transformedApiKeys.length > 0 ? transformedApiKeys : [],
        totalPages: (result.data?.total) ? Math.ceil(result.data.total / 50) : 1,
        loading: false
      }));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load API keys';
      console.error('Error loading API keys:', error);
      setState(prev => ({
        ...prev,
        apiKeys: [],
        totalPages: 1,
        loading: false,
        error: errorMsg
      }));
    }
  }, [state.page, state.searchQuery, state.selectedStatus, authApiKey]);

  const loadUsers = useCallback(async () => {
    try {
      if (!authApiKey) {
        return;
      }

      const result = await directApi.listUsers(1, 100);

      if (!result.success || !result.data) {
        console.error('Failed to fetch users');
        return;
      }

      // Transform snake_case API response to camelCase for frontend
      const transformedUsers = (result.data.users || []).map((item) => ({
        id: String(item.id),
        email: item.email,
        role: item.role,
        fullName: `${item.email} (${item.role})` // Create display name
      }));

      setState(prev => ({ ...prev, users: transformedUsers.length > 0 ? transformedUsers : [] }));
    } catch (error) {
      // User loading for dropdown shouldn't block the UI
      console.error('Error loading users:', error);
    }
  }, [authApiKey]);

  useEffect(() => {
    loadApiKeys();
    loadUsers();
  }, [loadApiKeys, loadUsers]);

  const handleCreateKey = () => {
    setState(prev => ({
      ...prev,
      dialogOpen: true,
      editingKey: null
    }));
  };

  const handleEditKey = (apiKey: ApiKey) => {
    setState(prev => ({
      ...prev,
      dialogOpen: true,
      editingKey: apiKey
    }));
  };

  const handleDeleteKey = (apiKey: ApiKey) => {
    setState(prev => ({
      ...prev,
      deleteDialogOpen: true,
      keyToDelete: apiKey
    }));
  };

  const confirmDelete = async () => {
    if (!state.keyToDelete) return;

    try {
      if (!authApiKey) {
        throw new Error('No API key found');
      }

      const result = await directApi.deleteApiKey(state.keyToDelete.id);

      if (!result.success) {
        throw new Error(result.error || 'Failed to delete API key');
      }

      setState(prev => ({
        ...prev,
        deleteDialogOpen: false,
        keyToDelete: null,
        snackbarOpen: true,
        snackbarMessage: 'API key deleted successfully'
      }));
      loadApiKeys();
    } catch (error) {
      console.error('Error deleting API key:', error);
      setState(prev => ({ ...prev, error: 'Failed to delete API key' }));
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setState(prev => ({
      ...prev,
      snackbarOpen: true,
      snackbarMessage: 'API key copied to clipboard'
    }));
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const StatsCard: React.FC<{
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
    suffix?: string;
  }> = ({ title, value, icon, color, suffix = '' }) => (
    <Card
      elevation={1}
      sx={{
        background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
        border: `1px solid ${alpha(color, 0.1)}`
      }}
    >
      <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h4" fontWeight="bold" color={color} sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
              {value.toLocaleString()}{suffix}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              {title}
            </Typography>
          </Box>
          <Box
            sx={{
              p: { xs: 1, sm: 1.5 },
              borderRadius: 2,
              backgroundColor: alpha(color, 0.1),
              color: color
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2, mb: { xs: 2, sm: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              color: theme.palette.primary.main
            }}
          >
            <ApiKeyIcon />
          </Box>
          <Box>
            <Typography variant="h4" fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
              API Keys Management
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Manage API keys and access permissions
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, alignItems: 'center' }}>
          <Tooltip title="Refresh API Keys">
            <span>
              <IconButton onClick={loadApiKeys} disabled={state.loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateKey}
          >
            Create API Key
          </Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={{ xs: 1.5, sm: 3 }} sx={{ mb: { xs: 2, sm: 4 } }}>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Total API Keys"
            value={state.apiKeys.length}
            icon={<ApiKeyIcon />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Active Keys"
            value={state.apiKeys.filter(k => k.isActive).length}
            icon={<ActiveIcon />}
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Total Usage"
            value={state.apiKeys.reduce((sum, k) => sum + (k.usageCount || 0), 0)}
            icon={<UsageIcon />}
            color={theme.palette.info.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="This Month"
            value={state.apiKeys.filter(k => {
              if (!k.createdAt) return false;
              try {
                return new Date(k.createdAt) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
              } catch {
                return false;
              }
            }).length}
            icon={<TodayIcon />}
            color={theme.palette.warning.main}
          />
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              placeholder="Search API keys by name, user, or key..."
              value={state.searchQuery}
              onChange={(e) => setState(prev => ({ ...prev, searchQuery: e.target.value }))}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={state.selectedStatus}
                label="Status"
                onChange={(e) => setState(prev => ({ ...prev, selectedStatus: e.target.value }))}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Alert */}
      {state.error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {state.error}
        </Alert>
      )}

      {/* API Keys Table */}
      <TableContainer component={Paper} elevation={1} sx={{ overflowX: 'auto' }}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>User</TableCell>
              <TableCell>API Key</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Usage</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last Used</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {state.apiKeys.map((apiKey) => (
              <TableRow key={apiKey.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {apiKey.name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                    <Chip
                      label={(apiKey.permissions && apiKey.permissions.length > 0) ? apiKey.permissions[0] : 'user'}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {apiKey.userEmail}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="body2"
                      fontFamily="monospace"
                      sx={{ maxWidth: 200, overflow: 'hidden' }}
                    >
                      {apiKey.key}
                    </Typography>
                    <Tooltip title="Copy to clipboard">
                      <IconButton
                        size="small"
                        onClick={() => copyToClipboard(apiKey.key)}
                      >
                        <CopyIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    ⚠️ Full key only visible during creation
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={apiKey.isActive ? <ActiveIcon /> : <InactiveIcon />}
                    label={apiKey.isActive ? 'Active' : 'Inactive'}
                    color={apiKey.isActive ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {(apiKey.usageCount || 0).toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      / {apiKey.rateLimit || 100} limit
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(apiKey.createdAt)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {apiKey.lastUsed ? formatDate(apiKey.lastUsed) : 'Never'}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Edit API Key">
                      <IconButton size="small" onClick={() => handleEditKey(apiKey)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete API Key">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteKey(apiKey)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination
          count={state.totalPages}
          page={state.page}
          onChange={(_, page) => setState(prev => ({ ...prev, page }))}
          color="primary"
        />
      </Box>

      {/* API Key Dialog */}
      <CreateApiKeyDialog
        open={state.dialogOpen}
        editingKey={state.editingKey}
        users={state.users}
        onClose={() => setState(prev => ({ ...prev, dialogOpen: false }))}
        onSubmit={async (keyData) => {
          try {
            if (!authApiKey) {
              throw new Error('No API key found');
            }

            // Format the data for the backend
            const formattedData = {
              name: keyData.name,
              user_id: keyData.user_id,
              rate_limit: keyData.rate_limit,
              permissions: keyData.permissions,
              expires_at: keyData.expires_at || undefined
            };

            let result;
            if (state.editingKey) {
              result = await directApi.updateApiKey(state.editingKey.id, formattedData);
            } else {
              result = await directApi.createApiKey(formattedData);
            }

            if (!result.success) {
              throw new Error(result.error || `Failed to ${state.editingKey ? 'update' : 'create'} API key`);
            }

            setState(prev => ({
              ...prev,
              dialogOpen: false,
              editingKey: null,
              snackbarOpen: true,
              snackbarMessage: `API key ${state.editingKey ? 'updated' : 'created'} successfully`,
              // Show the new key dialog only for new keys (not edits)
              newKeyDialogOpen: !state.editingKey,
              // @ts-ignore - result.data might have key property for new keys
              newlyCreatedKey: !state.editingKey ? result.data?.key : null
            }));
            loadApiKeys();
          } catch (error) {
            console.error(`Error ${state.editingKey ? 'updating' : 'creating'} API key:`, error);
            setState(prev => ({ ...prev, error: `Failed to ${state.editingKey ? 'update' : 'create'} API key` }));
          }
        }}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={state.deleteDialogOpen} onClose={() => setState(prev => ({ ...prev, deleteDialogOpen: false }))}>
        <DialogTitle>Delete API Key</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the API key "{state.keyToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setState(prev => ({ ...prev, deleteDialogOpen: false }))}>
            Cancel
          </Button>
          <Button color="error" variant="contained" onClick={confirmDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Newly Created API Key Dialog */}
      <Dialog
        open={state.newKeyDialogOpen}
        onClose={() => setState(prev => ({ ...prev, newKeyDialogOpen: false, newlyCreatedKey: null }))}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
          🎉 API Key Created Successfully!
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>⚠️ Important:</strong> This is the only time you'll see the full API key.
            Please copy it now and store it securely.
          </Alert>

          <Typography variant="body2" gutterBottom>
            Your new API key:
          </Typography>

          <Box
            sx={{
              p: 2,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: 'background.paper',
              fontFamily: 'monospace',
              wordBreak: 'break-all',
              position: 'relative'
            }}
          >
            <Typography variant="body2" fontFamily="monospace">
              {state.newlyCreatedKey}
            </Typography>
            <Tooltip title="Copy API key">
              <IconButton
                size="small"
                onClick={() => {
                  if (state.newlyCreatedKey) {
                    copyToClipboard(state.newlyCreatedKey);
                  }
                }}
                sx={{ position: 'absolute', top: 8, right: 8 }}
              >
                <CopyIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            In the API keys list, you'll only see a masked version of this key for security purposes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            variant="contained"
            onClick={() => setState(prev => ({ ...prev, newKeyDialogOpen: false, newlyCreatedKey: null }))}
          >
            I've Saved My API Key
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={state.snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setState(prev => ({ ...prev, snackbarOpen: false }))}
        message={state.snackbarMessage}
      />
    </Box>
  );
};

// Create API Key Dialog Component
interface CreateApiKeyDialogProps {
  open: boolean;
  editingKey: ApiKey | null;
  users: User[];
  onClose: () => void;
  // eslint-disable-next-line no-unused-vars
  onSubmit: (data: ApiKeyFormData) => Promise<void>;
}

const CreateApiKeyDialog: React.FC<CreateApiKeyDialogProps> = ({
  open,
  editingKey,
  users,
  onClose,
  onSubmit
}) => {
  const [formData, setFormData] = React.useState({
    name: '',
    user_id: users.length > 0 ? users[0].id : '',
    rate_limit: 100,
    expires_at: '',
    role: 'user' as 'admin' | 'user' | 'viewer'
  });
  const [loading, setLoading] = React.useState(false);

  // Define permissions based on role
  const getPermissionsForRole = (role: 'admin' | 'user' | 'viewer'): string[] => {
    return [role];
  };

  React.useEffect(() => {
    if (editingKey) {
      // For editing, get role from permissions (permissions array contains the role)
      const permissions = editingKey.permissions || [];
      const role = permissions.length > 0 ? permissions[0] as 'admin' | 'user' | 'viewer' : 'user';

      setFormData({
        name: editingKey.name,
        user_id: editingKey.userId,
        rate_limit: editingKey.rateLimit || 100,
        expires_at: editingKey.expiresAt || '',
        role: role
      });
    } else {
      setFormData({
        name: '',
        user_id: users.length > 0 ? users[0].id : '',
        rate_limit: 100,
        expires_at: '',
        role: 'user'
      });
    }
  }, [editingKey, users]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Convert role to permissions
      const permissions = getPermissionsForRole(formData.role);

      const submitData = {
        name: formData.name,
        user_id: formData.user_id,
        rate_limit: formData.rate_limit,
        expires_at: formData.expires_at || '',
        permissions: permissions
      };

      await onSubmit(submitData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {editingKey ? 'Edit API Key' : 'Create New API Key'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mb: 2 }}
            required
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>User</InputLabel>
            <Select
              value={formData.user_id}
              label="User"
              onChange={(e) => setFormData(prev => ({ ...prev, user_id: e.target.value }))}
            >
              {users.map((user) => (
                <MenuItem key={user.id} value={user.id}>
                  {user.email} ({user.role})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Rate Limit (requests/hour)"
            type="number"
            value={formData.rate_limit}
            onChange={(e) => setFormData(prev => ({ ...prev, rate_limit: parseInt(e.target.value) || 100 }))}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Expires At (optional)"
            type="datetime-local"
            value={formData.expires_at ? new Date(formData.expires_at).toISOString().slice(0, 16) : ''}
            onChange={(e) => setFormData(prev => ({ ...prev, expires_at: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
            sx={{ mb: 2 }}
            InputLabelProps={{ shrink: true }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Role</InputLabel>
            <Select
              value={formData.role}
              label="Role"
              onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as 'admin' | 'user' }))}
            >
              <MenuItem value="user">User - Create and manage content</MenuItem>
              <MenuItem value="admin">Admin - Full system access</MenuItem>
            </Select>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {formData.role === 'admin' && 'Full access to all features including system administration'}
              {formData.role === 'user' && 'Can create, read, and update content but no admin features'}
            </Typography>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !formData.name.trim()}
        >
          {loading ? 'Processing...' : (editingKey ? 'Update' : 'Create')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ApiKeys;