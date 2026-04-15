import React, { useState, useEffect, useCallback } from 'react';
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
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  Pagination,
  InputAdornment,
  Tooltip,
  Card,
  CardContent,
  Grid,
  alpha,
  useTheme,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  People as PeopleIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
  Visibility as ViewerIcon,
  Email as EmailIcon,
  CalendarToday as DateIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { directApi } from '../utils/api';

interface User {
  id: string;
  username?: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'user' | 'viewer';
  created_at: string;
  updated_at?: string;
  last_login?: string;
  is_active: boolean;
  projects_count?: number;
  api_keys_count?: number;
}

interface UsersState {
  users: User[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  totalCount: number;
  searchQuery: string;
  selectedRole: string;
  dialogOpen: boolean;
  editingUser: User | null;
  deleteDialogOpen: boolean;
  userToDelete: User | null;
  stats: {
    total_users: number;
    active_users?: number;
    admin_count: number;
    user_count?: number;
    viewer_count?: number;
    this_month_count?: number;
  };
}

interface FormData {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role: string;
  is_active: boolean;
}

const Users: React.FC = () => {
  const theme = useTheme();
  const { isAuthenticated, apiKey } = useAuth();
  const [state, setState] = useState<UsersState>({
    users: [],
    loading: false,
    error: null,
    page: 1,
    totalPages: 1,
    totalCount: 0,
    searchQuery: '',
    selectedRole: 'all',
    dialogOpen: false,
    editingUser: null,
    deleteDialogOpen: false,
    userToDelete: null,
    stats: {
      total_users: 0,
      admin_count: 0,
      active_users: 0,
      this_month_count: 0
    }
  });

  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'user',
    is_active: true
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Load users from API
  const loadUsers = useCallback(async (page?: number, search?: string, role?: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const currentPage = page ?? state.page ?? 1;
      const currentSearch = search ?? state.searchQuery ?? '';
      const currentRole = (role ?? state.selectedRole ?? 'all') !== 'all' ? (role ?? state.selectedRole) : undefined;

      const response = await directApi.listUsers(currentPage, 50, currentSearch, currentRole);

      if (!response.success) {
        throw new Error(response.error || 'Failed to load users');
      }

      const data = response.data;
      if (!data) {
        throw new Error('No data received from server');
      }

      const users = (data?.users || []) as User[];
      const pagination = data?.pagination || { total_pages: 1, total_count: 0 };

      setState(prev => ({
        ...prev,
        users: users.length > 0 ? users : [],
        totalPages: pagination.total_pages || 1,
        totalCount: pagination.total_count || 0,
        loading: false,
        ...(page && { page })
      }));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load users';
      setState(prev => ({
        ...prev,
        users: [],
        error: errorMsg,
        loading: false
      }));
    }
  }, [state.page, state.searchQuery, state.selectedRole]);

  // Load user statistics
  const loadStats = useCallback(async () => {
    try {
      const response = await directApi.getUserStats();
      if (!response.success) {
        // Stats loading failure shouldn't block the UI - just log it
        console.error('Error loading user stats:', response.error);
        return;
      }

      if (!response.data) {
        console.error('No stats data received');
        return;
      }

      const statsData = response.data.stats || {
        total_users: 0,
        admin_count: 0,
        active_users: 0,
        user_count: 0,
        viewer_count: 0
      };

      setState(prev => ({
        ...prev,
        stats: statsData
      }));
    } catch (error) {
      // Stats loading failure shouldn't block the UI - just log it
      console.error('Error loading stats:', error);
    }
  }, []);

  // Load data when auth changes or filters change
  useEffect(() => {
    if (isAuthenticated && apiKey) {
      loadStats();
    }
  }, [isAuthenticated, apiKey, loadStats]);

  useEffect(() => {
    if (isAuthenticated && apiKey) {
      loadUsers(state.page, state.searchQuery, state.selectedRole);
    }
  }, [state.page, state.searchQuery, state.selectedRole, isAuthenticated, apiKey, loadUsers]);

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      full_name: '',
      password: '',
      role: 'user',
      is_active: true
    });
    setFormErrors({});
  };

  const handleCreateUser = () => {
    resetForm();
    setState(prev => ({
      ...prev,
      dialogOpen: true,
      editingUser: null
    }));
  };

  const handleEditUser = (user: User) => {
    setFormData({
      username: user.username || '',
      email: user.email,
      full_name: user.full_name || '',
      password: '', // Don't pre-fill password
      role: user.role,
      is_active: user.is_active
    });
    setFormErrors({});
    setState(prev => ({
      ...prev,
      dialogOpen: true,
      editingUser: user
    }));
  };

  const handleDeleteUser = (user: User) => {
    setState(prev => ({
      ...prev,
      deleteDialogOpen: true,
      userToDelete: user
    }));
  };

  const confirmDelete = async () => {
    if (!state.userToDelete) return;

    try {
      const response = await directApi.deleteUser(state.userToDelete.id);
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete user');
      }

      setState(prev => ({
        ...prev,
        deleteDialogOpen: false,
        userToDelete: null
      }));

      // Reload data after successful operation
      try {
        await loadUsers(1); // Reset to page 1 after delete
        await loadStats();
      } catch (reloadError) {
        // Don't set error state for reload failures, deletion was successful
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to delete user'
      }));
    }
  };

  const handleSubmitUser = async () => {
    setFormErrors({});

    // Basic validation
    const errors: Record<string, string> = {};
    if (!formData.email) errors.email = 'Email is required';
    if (!formData.username) errors.username = 'Username is required';
    if (!state.editingUser && !formData.password) errors.password = 'Password is required';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      if (state.editingUser) {
        // Update existing user
        const updateData: {
          username?: string;
          email?: string;
          full_name?: string;
          password?: string;
          role?: string;
          is_active?: boolean;
        } = {
          username: formData.username,
          email: formData.email,
          full_name: formData.full_name,
          role: formData.role,
          is_active: formData.is_active
        };

        if (formData.password) {
          updateData.password = formData.password;
        }

        const response = await directApi.updateUser(state.editingUser.id, updateData);
        if (!response.success) {
          throw new Error(response.error || 'Failed to update user');
        }
      } else {
        // Create new user
        const response = await directApi.createUser({
          username: formData.username,
          email: formData.email,
          full_name: formData.full_name,
          password: formData.password,
          role: formData.role,
          is_active: formData.is_active
        });
        if (!response.success) {
          throw new Error(response.error || 'Failed to create user');
        }
      }

      setState(prev => ({
        ...prev,
        dialogOpen: false,
        editingUser: null,
        page: 1 // Reset to page 1
      }));

      // Reload data after successful operation
      try {
        await loadUsers(1); // Reset to page 1 after create/update
        await loadStats();
      } catch (reloadError) {
        // Don't set error state for reload failures, user creation was successful
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to save user'
      }));
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <AdminIcon />;
      case 'user': return <UserIcon />;
      case 'viewer': return <ViewerIcon />;
      default: return <UserIcon />;
    }
  };

  const getRoleColor = (role: string): 'primary' | 'secondary' | 'default' => {
    switch (role) {
      case 'admin': return 'primary';
      case 'user': return 'secondary';
      case 'viewer': return 'default';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isAuthenticated) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Please log in to access user management.</Typography>
      </Box>
    );
  }

  const StatsCard: React.FC<{
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
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
              {value}
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
            <PeopleIcon />
          </Box>
          <Box>
            <Typography variant="h4" fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
              Users Management
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Manage user accounts and permissions
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, alignItems: 'center' }}>
          <Tooltip title="Refresh Users">
            <span>
              <IconButton onClick={() => loadUsers()} disabled={state.loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateUser}
          >
            Add User
          </Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={{ xs: 1.5, sm: 3 }} sx={{ mb: { xs: 2, sm: 4 } }}>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Total Users"
            value={state.stats.total_users}
            icon={<PeopleIcon />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Admins"
            value={state.stats.admin_count}
            icon={<AdminIcon />}
            color={theme.palette.error.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Active Users"
            value={state.stats.active_users || 0}
            icon={<UserIcon />}
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="This Month"
            value={state.stats.this_month_count || 0}
            icon={<DateIcon />}
            color={theme.palette.info.main}
          />
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search users by email..."
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
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={state.selectedRole}
                label="Role"
                onChange={(e) => setState(prev => ({ ...prev, selectedRole: e.target.value }))}
              >
                <MenuItem value="all">All Roles</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="user">User</MenuItem>
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

      {/* Users Table */}
      <TableContainer component={Paper} elevation={1} sx={{ overflowX: 'auto' }}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell>Projects</TableCell>
              <TableCell>API Keys</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {state.loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                  <Typography sx={{ mt: 1 }}>Loading users...</Typography>
                </TableCell>
              </TableRow>
            ) : state.users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No users found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              state.users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box
                        sx={{
                          p: 1,
                          borderRadius: 1,
                          backgroundColor: alpha(theme.palette.primary.main, 0.1),
                          color: theme.palette.primary.main
                        }}
                      >
                        <EmailIcon sx={{ fontSize: 20 }} />
                      </Box>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {user.email}
                        </Typography>
                        {user.full_name && (
                          <Typography variant="caption" color="text.secondary">
                            {user.full_name}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={getRoleIcon(user.role)}
                      label={user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      color={getRoleColor(user.role)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(user.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {user.last_login ? formatDate(user.last_login) : 'Never'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.projects_count}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.api_keys_count}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      color={user.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="Edit User">
                        <IconButton size="small" onClick={() => handleEditUser(user)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete User">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteUser(user)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
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

      {/* User Dialog */}
      <Dialog open={state.dialogOpen} onClose={() => setState(prev => ({ ...prev, dialogOpen: false }))} maxWidth="sm" fullWidth>
        <DialogTitle>
          {state.editingUser ? 'Edit User' : 'Create New User'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              error={!!formErrors.username}
              helperText={formErrors.username}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              error={!!formErrors.email}
              helperText={formErrors.email}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Full Name"
              value={formData.full_name}
              onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              error={!!formErrors.password}
              helperText={formErrors.password || (state.editingUser ? 'Leave empty to keep current password' : '')}
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                label="Role"
                onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
              >
                <MenuItem value="admin">Admin</MenuItem>
                <MenuItem value="user">User</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.is_active ? 'active' : 'inactive'}
                label="Status"
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.value === 'active' }))}
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setState(prev => ({ ...prev, dialogOpen: false }))}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmitUser}>
            {state.editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={state.deleteDialogOpen} onClose={() => setState(prev => ({ ...prev, deleteDialogOpen: false }))}>
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the user "{state.userToDelete?.email}"? This action cannot be undone.
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
    </Box>
  );
};

export default Users;