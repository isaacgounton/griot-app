import React, { useState, useEffect } from 'react';
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
  Alert,
  Pagination,
  InputAdornment,
  TextField,
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
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tab,
  Tabs,
  Badge,
  Switch,
  FormControlLabel,
  Snackbar
} from '@mui/material';
import WorkIcon from '@mui/icons-material/Work';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import ScheduleIcon from '@mui/icons-material/Schedule';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
// import CancelIcon from '@mui/icons-material/Cancel';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import ReplayIcon from '@mui/icons-material/Replay';
import ShareIcon from '@mui/icons-material/Share';
import BuildIcon from '@mui/icons-material/Build';
import ClearIcon from '@mui/icons-material/Clear';
import TimerIcon from '@mui/icons-material/Timer';
import BarChartIcon from '@mui/icons-material/BarChart';
import { Job, JobStatus, JobType } from '../types/griot';
import { directApi } from '../utils/api';
import { PostizScheduleDialog } from '../components/PostizScheduleDialog';
import { useAuth } from '../contexts/AuthContext';

interface JobsState {
  jobs: Job[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  searchQuery: string;
  selectedStatus: string;
  selectedType: string;
  dialogOpen: boolean;
  selectedJob: Job | null;
  deletedJobs: Set<string>;
  deleteDialogOpen: boolean;
  scheduleDialogOpen: boolean;
  jobToDelete: Job | null;
  autoRefresh: boolean;
  tabValue: number;
  // Cleanup state
  cleanupStatus: {
    last_cleanup?: string;
    jobs_deleted?: number;
    jobs_archived?: number;
    next_cleanup?: string;
    status?: string;
    scheduler?: {
      running?: boolean;
      [key: string]: unknown;
    };
    job_counts?: {
      [key: string]: number;
    };
    [key: string]: unknown;
  } | null;
  cleanupLoading: boolean;
  manualCleanupAge: number;
  snackbarOpen: boolean;
  snackbarMessage: string;
  snackbarSeverity: 'success' | 'error';
  // Confirmation dialog state
  confirmDialogOpen: boolean;
  confirmDialogTitle: string;
  confirmDialogMessage: string;
  confirmDialogAction: (() => void) | null;
}

const JobManagement: React.FC = () => {
  const theme = useTheme();
  const { apiKey, userRole } = useAuth();
  const [state, setState] = useState<JobsState>({
    jobs: [],
    loading: false,
    error: null,
    page: 1,
    totalPages: 1,
    searchQuery: '',
    selectedStatus: 'all',
    selectedType: 'all',
    dialogOpen: false,
    selectedJob: null,
    deleteDialogOpen: false,
    scheduleDialogOpen: false,
    jobToDelete: null,
    autoRefresh: false,
    deletedJobs: new Set<string>(),
    tabValue: 0,
    cleanupStatus: null,
    cleanupLoading: false,
    manualCleanupAge: 24,
    snackbarOpen: false,
    snackbarMessage: '',
    snackbarSeverity: 'success',
    confirmDialogOpen: false,
    confirmDialogTitle: '',
    confirmDialogMessage: '',
    confirmDialogAction: null
  });

  const showNotification = (message: string, severity: 'success' | 'error' = 'success') => {
    setState(prev => ({
      ...prev,
      snackbarOpen: true,
      snackbarMessage: message,
      snackbarSeverity: severity
    }));
  };

  const showConfirmDialog = (title: string, message: string, action: () => void) => {
    setState(prev => ({
      ...prev,
      confirmDialogOpen: true,
      confirmDialogTitle: title,
      confirmDialogMessage: message,
      confirmDialogAction: action
    }));
  };

  const handleConfirmAction = () => {
    if (state.confirmDialogAction) {
      state.confirmDialogAction();
    }
    setState(prev => ({
      ...prev,
      confirmDialogOpen: false,
      confirmDialogAction: null
    }));
  };

  const loadJobs = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const response = await directApi.listJobs(state.page, 20);
      if (response.success && response.data) {
        const filteredJobs = response.data.jobs.filter((job: Job) =>
          !state.deletedJobs.has(job.id || job.job_id || '')
        );

        setState(prev => ({
          ...prev,
          jobs: filteredJobs,
          totalPages: Math.ceil((response.data?.total || 0) / 20),
          loading: false
        }));
      } else {
        throw new Error(response.error || 'Failed to load jobs');
      }
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load jobs';
      setState(prev => ({
        ...prev,
        error: errorMsg,
        loading: false
      }));
    }
  };

  const loadCleanupStatus = async () => {
    try {
      if (!apiKey) return;

      const result = await directApi.getCleanupStatus();

      if (result.success && result.data) {
        setState(prev => ({ ...prev, cleanupStatus: result.data || null }));
      }
    } catch (error) {
      console.error('Failed to load cleanup status:', error);
    }
  };

  const triggerCleanup = async () => {
    setState(prev => ({ ...prev, cleanupLoading: true }));

    try {
      if (!apiKey) throw new Error('API key not found');

      const result = await directApi.triggerCleanup();

      if (result.success) {
        showNotification(result.data?.message || 'Cleanup completed successfully');
        await loadCleanupStatus();
        await loadJobs();
      } else {
        throw new Error(result.error || 'Cleanup failed');
      }
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to trigger cleanup';
      showNotification(errorMsg, 'error');
    } finally {
      setState(prev => ({ ...prev, cleanupLoading: false }));
    }
  };

  const performManualCleanup = async () => {
    setState(prev => ({ ...prev, cleanupLoading: true }));

    try {
      if (!apiKey) throw new Error('API key not found');

      const result = await directApi.manualCleanup(state.manualCleanupAge);

      if (result.success) {
        showNotification(result.data?.message || `Manual cleanup completed`);
        await loadCleanupStatus();
        await loadJobs();
      } else {
        throw new Error('Manual cleanup failed');
      }
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to perform manual cleanup';
      showNotification(errorMsg, 'error');
    } finally {
      setState(prev => ({ ...prev, cleanupLoading: false }));
    }
  };

  const manualCleanup = () => {
    showConfirmDialog(
      'Delete Old Jobs',
      `This will permanently delete all jobs older than ${state.manualCleanupAge} hours. This action cannot be undone.`,
      performManualCleanup
    );
  };

  useEffect(() => {
    if (state.tabValue === 0) {
      loadJobs();
    } else if (state.tabValue === 1) {
      loadCleanupStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.page, state.searchQuery, state.selectedStatus, state.selectedType, state.tabValue]);

  // Auto-reset tab if non-admin tries to access cleanup tab
  useEffect(() => {
    if (userRole !== 'admin' && state.tabValue === 1) {
      setState(prev => ({ ...prev, tabValue: 0 }));
    }
  }, [userRole, state.tabValue]);

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case JobStatus.PENDING: return <ScheduleIcon />;
      case JobStatus.PROCESSING: return <PlayArrowIcon />;
      case JobStatus.COMPLETED: return <CheckCircleIcon />;
      case JobStatus.FAILED: return <ErrorIcon />;
      // case JobStatus.CANCELLED: return <CancelIcon />;
      default: return <InfoIcon />;
    }
  };

  const getStatusColor = (status: JobStatus): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    switch (status) {
      case JobStatus.PENDING: return 'default';
      case JobStatus.PROCESSING: return 'primary';
      case JobStatus.COMPLETED: return 'success';
      case JobStatus.FAILED: return 'error';
      // case JobStatus.CANCELLED: return 'warning';
      default: return 'info';
    }
  };

  const getTypeColor = (type?: JobType | string): string => {
    if (!type) return theme.palette.grey[500];

    const typeStr = typeof type === 'string' ? type : type;

    switch (typeStr) {
      case JobType.SHORT_VIDEO_CREATION:
      case 'short_video_creation':
        return theme.palette.primary.main;
      case JobType.FOOTAGE_TO_VIDEO:
      case 'footage_to_video':
        return theme.palette.secondary.main;
      case JobType.AIIMAGE_TO_VIDEO:
      case 'aiimage_to_video':
        return theme.palette.success.main;
      case JobType.AI_SCRIPT_GENERATION:
      case 'ai_script_generation':
        return theme.palette.warning.main;
      case JobType.VIDEO_SEARCH_QUERY_GENERATION:
      case 'video_search_query_generation':
        return theme.palette.info.main;
      case 'research_news':
        return theme.palette.secondary.main;
      default: return theme.palette.grey[500];
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = end.getTime() - start.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const handleViewJob = (job: Job) => {
    setState(prev => ({
      ...prev,
      dialogOpen: true,
      selectedJob: job
    }));
  };

  const handleDeleteJob = (job: Job) => {
    setState(prev => ({
      ...prev,
      deleteDialogOpen: true,
      jobToDelete: job
    }));
  };

  const handleScheduleJob = (job: Job) => {
    setState(prev => ({
      ...prev,
      scheduleDialogOpen: true,
      selectedJob: job
    }));
  };

  const isJobSchedulable = (job: Job): boolean => {
    if (job.status !== JobStatus.COMPLETED) return false;

    if (job.result && typeof job.result === 'object' && 'scheduling' in job.result) {
      const scheduling = (job.result as unknown as Record<string, unknown>).scheduling;
      return (scheduling as Record<string, unknown>)?.available === true;
    }

    const schedulableTypes = [
      'footage_to_video', 'aiimage_to_video', 'scenes_to_video',
      'short_video_creation', 'image_to_video', 'image_generation', 'audio_generation'
    ];
    return schedulableTypes.includes(job.operation?.toLowerCase() || '');
  };

  const handleScheduleSubmit = async (scheduleData: {
    jobId: string;
    content: string;
    integrations: string[];
    postType: string;
    scheduleDate?: Date;
    tags?: string[];
  }): Promise<void> => {
    try {
      if (!apiKey) {
        throw new Error('API key not found');
      }

      const result = await directApi.schedulePost({
        job_id: scheduleData.jobId,
        content: scheduleData.content,
        integrations: scheduleData.integrations,
        post_type: scheduleData.postType,
        schedule_date: scheduleData.scheduleDate?.toISOString() || new Date().toISOString(),
        tags: scheduleData.tags
      });

      if (!result.success) {
        throw new Error(result.error || 'Failed to schedule post');
      }

      setState(prev => ({
        ...prev,
        scheduleDialogOpen: false,
        selectedJob: null
      }));

      showNotification('Post scheduled successfully');

    } catch (error: unknown) {
      console.error('Failed to schedule post:', error);
      throw error;
    }
  };

  const handleRetryJob = async (job: Job) => {
    if (job.status !== JobStatus.FAILED) return;

    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const response = await directApi.retryJob(job.id || job.job_id || '');
      if (!response.success) {
        throw new Error(response.error || 'Failed to retry job');
      }

      setState(prev => ({ ...prev, loading: false }));
      loadJobs();
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to retry job';
      setState(prev => ({
        ...prev,
        error: `Failed to retry job: ${errorMsg}`,
        loading: false
      }));
    }
  };

  const confirmDelete = async () => {
    if (!state.jobToDelete) return;

    const deletedJobId = state.jobToDelete.id;

    setState(prev => {
      const newDeletedJobs = new Set(prev.deletedJobs);
      newDeletedJobs.add(deletedJobId || '');

      const filteredJobs = prev.jobs.filter(job => job.id !== deletedJobId);

      return {
        ...prev,
        jobs: filteredJobs,
        deleteDialogOpen: false,
        jobToDelete: null,
        deletedJobs: newDeletedJobs
      };
    });

    try {
      await directApi.deleteJob(deletedJobId || '');
    } catch (err) {
      // Ignore backend errors - the UI is already updated
    }
  };

  const StatsCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
  }> = ({ title, value, icon, color, subtitle }) => (
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
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
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

  const renderJobsTab = () => (
    <Box>
      {/* Stats */}
      <Grid container spacing={{ xs: 1.5, sm: 3 }} sx={{ mb: { xs: 2, sm: 4 } }}>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Total Jobs"
            value={state.jobs.length}
            icon={<WorkIcon />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Processing"
            value={state.jobs.filter(j => j.status === JobStatus.PROCESSING).length}
            icon={<PlayArrowIcon />}
            color={theme.palette.warning.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Completed"
            value={state.jobs.filter(j => j.status === JobStatus.COMPLETED).length}
            icon={<CheckCircleIcon />}
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <StatsCard
            title="Failed"
            value={state.jobs.filter(j => j.status === JobStatus.FAILED).length}
            icon={<ErrorIcon />}
            color={theme.palette.error.main}
          />
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search jobs by ID or type..."
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
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={state.selectedType}
                label="Type"
                onChange={(e) => setState(prev => ({ ...prev, selectedType: e.target.value }))}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="video_generation">Video Generation</MenuItem>
                <MenuItem value="script_generation">Script Generation</MenuItem>
                <MenuItem value="audio_generation">Audio Generation</MenuItem>
                <MenuItem value="image_generation">Image Generation</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Jobs Table */}
      <TableContainer component={Paper} elevation={1} sx={{ overflowX: 'auto' }}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>Job ID</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {state.jobs.map((job) => (
              <TableRow key={job.id} hover>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {job.id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={job.operation ? job.operation.replace('_', ' ').toUpperCase() : 'UNKNOWN'}
                    size="small"
                    sx={{
                      backgroundColor: alpha(getTypeColor(job.operation), 0.1),
                      color: getTypeColor(job.operation),
                      fontWeight: 'medium'
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    icon={getStatusIcon(job.status)}
                    label={job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    color={getStatusColor(job.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
                    <LinearProgress
                      variant="determinate"
                      value={job.progress || 0}
                      sx={{
                        flexGrow: 1,
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: alpha(theme.palette.primary.main, 0.1)
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                      {job.progress || 0}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {job.created_at ? new Date(job.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    }) : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {job.created_at && job.updated_at ? formatDuration(job.created_at, job.updated_at) : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => handleViewJob(job)}>
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    {isJobSchedulable(job) && (
                      <Tooltip title="Schedule to Social Media">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleScheduleJob(job)}
                          disabled={state.loading}
                        >
                          <ShareIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {userRole === 'admin' && job.status === JobStatus.FAILED && (
                      <Tooltip title="Retry Job">
                        <IconButton
                          size="small"
                          color="warning"
                          onClick={() => handleRetryJob(job)}
                          disabled={state.loading}
                        >
                          <ReplayIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {userRole === 'admin' && (
                      <Tooltip title="Delete Job">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteJob(job)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    )}
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
    </Box>
  );

  const renderCleanupTab = () => {
    const scheduler = state.cleanupStatus?.scheduler || {};
    const jobCounts = state.cleanupStatus?.job_counts || {};
    const totalJobs = Object.values(jobCounts).reduce((a: number, b: unknown) => a + (typeof b === 'number' ? b : 0), 0);

    return (
      <Box>
        {/* Scheduler Status Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Scheduler Status"
              value={scheduler.running ? 'Running' : 'Stopped'}
              icon={<TimerIcon />}
              color={scheduler.running ? theme.palette.success.main : theme.palette.error.main}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Total Jobs"
              value={totalJobs.toString()}
              icon={<BarChartIcon />}
              color={theme.palette.primary.main}
              subtitle="Across all statuses"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Cleanup Interval"
              value={`${scheduler.cleanup_interval_hours || 6}h`}
              icon={<ClearIcon />}
              color={theme.palette.info.main}
              subtitle="Automatic cleanup frequency"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Job Retention"
              value={`${scheduler.job_retention_hours || 24}h`}
              icon={<BuildIcon />}
              color={theme.palette.warning.main}
              subtitle="How long jobs are kept"
            />
          </Grid>
        </Grid>

        {/* Cleanup Controls */}
        <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ClearIcon />
            Cleanup Controls
          </Typography>

          <Grid container spacing={3}>
            {/* Quick Actions */}
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    startIcon={<ClearIcon />}
                    onClick={triggerCleanup}
                    disabled={state.cleanupLoading}
                    color="warning"
                  >
                    {state.cleanupLoading ? 'Cleaning...' : 'Clean Now'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={loadCleanupStatus}
                    disabled={state.cleanupLoading}
                  >
                    Refresh Status
                  </Button>
                </Box>
              </Box>
            </Grid>

            {/* Manual Cleanup */}
            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Manual Cleanup
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'end', flexWrap: 'wrap' }}>
                  <TextField
                    label="Max Age (hours)"
                    type="number"
                    value={state.manualCleanupAge}
                    onChange={(e) => setState(prev => ({ ...prev, manualCleanupAge: parseInt(e.target.value) || 24 }))}
                    inputProps={{ min: 1, max: 168 }}
                    sx={{ minWidth: 140 }}
                    size="small"
                  />
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={manualCleanup}
                    disabled={state.cleanupLoading}
                  >
                    Delete Old Jobs
                  </Button>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  Delete jobs older than specified hours (1-168 hours)
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>

      </Box>
    );
  };

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
            <WorkIcon />
          </Box>
          <Box>
            <Typography variant="h4" fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
              Jobs Management
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Monitor jobs and system maintenance
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={state.autoRefresh}
                onChange={(e) => setState(prev => ({ ...prev, autoRefresh: e.target.checked }))}
              />
            }
            label="Auto Refresh"
          />
          <Tooltip title="Refresh Data">
            <span>
              <IconButton
                onClick={() => {
                  if (state.tabValue === 0) loadJobs();
                  else loadCleanupStatus();
                }}
                disabled={state.loading}
              >
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {state.error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {state.error}
        </Alert>
      )}

      {/* Role-based notice for non-admin users */}
      {userRole !== 'admin' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Note:</strong> Some job management features like cleanup operations, job deletion, and retry functionality are only available to administrators.
            Contact your system administrator for advanced job management tasks.
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Paper elevation={1} sx={{ mb: 3 }}>
        <Tabs
          value={state.tabValue}
          onChange={(_, newValue) => setState(prev => ({ ...prev, tabValue: newValue }))}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WorkIcon />
                Jobs
                <Badge badgeContent={state.jobs.length} color="primary" />
              </Box>
            }
          />
          {userRole === 'admin' && (
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BuildIcon />
                  Cleanup & Maintenance
                  {state.cleanupStatus &&
                    Object.values(state.cleanupStatus.job_counts || {}).reduce((a: number, b: unknown) => a + (typeof b === 'number' ? b : 0), 0) > 0 && (
                      <Badge
                        badgeContent={
                          Object.values(state.cleanupStatus.job_counts || {}).reduce((a: number, b: unknown) => a + (typeof b === 'number' ? b : 0), 0)
                        }
                        color="warning"
                      />
                    )}
                </Box>
              }
            />
          )}
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {state.tabValue === 0 && renderJobsTab()}
      {userRole === 'admin' && state.tabValue === 1 && renderCleanupTab()}

      {/* Job Details Dialog */}
      <Dialog
        open={state.dialogOpen}
        onClose={() => setState(prev => ({ ...prev, dialogOpen: false }))}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Job Details: {state.selectedJob?.id}
        </DialogTitle>
        <DialogContent>
          {state.selectedJob && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Type
                  </Typography>
                  <Typography variant="body1">
                    {state.selectedJob.operation?.replace('_', ' ').toUpperCase() || 'Unknown'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    icon={getStatusIcon(state.selectedJob.status)}
                    label={state.selectedJob.status?.charAt(0).toUpperCase() + state.selectedJob.status?.slice(1) || 'Unknown'}
                    color={getStatusColor(state.selectedJob.status)}
                    size="small"
                  />
                </Grid>
              </Grid>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Job Data</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <pre style={{
                    backgroundColor: theme.palette.grey[100],
                    padding: 16,
                    borderRadius: 4,
                    overflow: 'auto',
                    fontSize: '0.875rem'
                  }}>
                    {JSON.stringify(state.selectedJob.params || {}, null, 2)}
                  </pre>
                </AccordionDetails>
              </Accordion>

              {state.selectedJob.result && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">Result</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <pre style={{
                      backgroundColor: theme.palette.grey[100],
                      padding: 16,
                      borderRadius: 4,
                      overflow: 'auto',
                      fontSize: '0.875rem'
                    }}>
                      {JSON.stringify(state.selectedJob.result, null, 2)}
                    </pre>
                  </AccordionDetails>
                </Accordion>
              )}

              {state.selectedJob.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Error Details:</Typography>
                  <Typography variant="body2">{state.selectedJob.error}</Typography>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {userRole === 'admin' && state.selectedJob?.status === JobStatus.FAILED && (
            <Button
              variant="outlined"
              color="warning"
              startIcon={<ReplayIcon />}
              onClick={() => {
                if (state.selectedJob) {
                  handleRetryJob(state.selectedJob);
                  setState(prev => ({ ...prev, dialogOpen: false }));
                }
              }}
              disabled={state.loading}
            >
              Retry Job
            </Button>
          )}
          <Button onClick={() => setState(prev => ({ ...prev, dialogOpen: false }))}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={state.deleteDialogOpen} onClose={() => setState(prev => ({ ...prev, deleteDialogOpen: false }))}>
        <DialogTitle>Delete Job</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete job "{state.jobToDelete?.id}"? This action cannot be undone.
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

      {/* Postiz Schedule Dialog */}
      <PostizScheduleDialog
        open={state.scheduleDialogOpen}
        onClose={() => setState(prev => ({ ...prev, scheduleDialogOpen: false, selectedJob: null }))}
        job={state.selectedJob}
        onSchedule={handleScheduleSubmit}
      />

      {/* Confirmation Dialog */}
      <Dialog open={state.confirmDialogOpen} onClose={() => setState(prev => ({ ...prev, confirmDialogOpen: false }))}>
        <DialogTitle>{state.confirmDialogTitle}</DialogTitle>
        <DialogContent>
          <Typography>
            {state.confirmDialogMessage}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setState(prev => ({ ...prev, confirmDialogOpen: false }))}>
            Cancel
          </Button>
          <Button
            color="warning"
            variant="contained"
            onClick={handleConfirmAction}
            disabled={state.cleanupLoading}
          >
            {state.cleanupLoading ? 'Processing...' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={state.snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setState(prev => ({ ...prev, snackbarOpen: false }))}
      >
        <Alert
          onClose={() => setState(prev => ({ ...prev, snackbarOpen: false }))}
          severity={state.snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {state.snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default JobManagement;