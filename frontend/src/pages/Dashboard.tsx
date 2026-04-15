import React, { useState, useEffect, useMemo, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { directApi } from '../utils/api';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Paper,
  useTheme,
  alpha,
  IconButton,
  Tooltip,
  LinearProgress,
  Chip,
  Skeleton
} from '@mui/material';
import {
  VideoLibrary as VideoIcon,
  People as UsersIcon,
  VpnKey as ApiKeyIcon,
  TrendingUp,
  Schedule,
  CheckCircle,
  Refresh,
  PlayArrow,
  Timeline,
  Storage,
  Speed,
  SmartToy as SimoneIcon,
  VolumeUp as AudioIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';

interface DashboardStats {
  totalVideos: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
  totalUsers: number;
  activeApiKeys: number;
  storageUsed: number;
  storageTotal: number;
  avgProcessingTime: number;
}


interface QuickAction {
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  color: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error';
  disabled?: boolean;
}

interface RecentActivity {
  id: string;
  type: 'video_created' | 'job_completed' | 'user_added' | 'api_key_created';
  title: string;
  timestamp: string;
  status: 'success' | 'error' | 'info';
  details?: string;
  operation?: string;
  progress?: number;
}

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { userRole } = useAuth();

  const [stats, setStats] = useState<DashboardStats>({
    totalVideos: 0,
    activeJobs: 0,
    completedJobs: 0,
    failedJobs: 0,
    totalUsers: 0,
    activeApiKeys: 0,
    storageUsed: 0,
    storageTotal: 100,
    avgProcessingTime: 0
  });

  const [loading, setLoading] = useState(false);
  const [, setError] = useState<string | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [initialLoad, setInitialLoad] = useState(true);

  const quickActions: QuickAction[] = [
    {
      title: 'Create Video',
      description: 'Start generating a new AI video',
      icon: <PlayArrow />,
      action: () => navigate('/dashboard/video-studio'),
      color: 'primary'
    },
    {
      title: 'Simone AI',
      description: 'AI-powered content generation',
      icon: <SimoneIcon />,
      action: () => navigate('/dashboard/simone'),
      color: 'secondary'
    },
    {
      title: 'Audio Tools',
      description: 'Generate speech, music, and transcriptions',
      icon: <AudioIcon />,
      action: () => navigate('/dashboard/audio'),
      color: 'error'
    },
    {
      title: 'View Library',
      description: 'Browse all generated videos',
      icon: <VideoIcon />,
      action: () => navigate('/dashboard/library'),
      color: 'info'
    }
  ];

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
    trend?: { value: string; direction: 'up' | 'down' };
    loading?: boolean;
  }> = memo(({ title, value, icon, color, subtitle, trend, loading = false }) => (
    <Card
      elevation={0}
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, 
          rgba(255, 255, 255, 0.95) 0%, 
          ${alpha('#f8fafc', 0.8)} 100%
        )`,
        backdropFilter: 'blur(10px)',
        border: `1px solid ${alpha(color, 0.12)}`,
        borderLeft: `4px solid ${color}`,
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 25px ${alpha(color, 0.15)}`,
          borderColor: alpha(color, 0.3)
        }
      }}
    >
      <CardContent sx={{ p: { xs: 1.5, sm: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontSize: { xs: '0.65rem', sm: '0.75rem' },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                mt: 0.5,
                mb: 0.5,
                color: color,
                fontFamily: '"Inter", sans-serif',
                fontSize: { xs: '1.5rem', sm: '2.125rem' }
              }}
            >
              {loading ? '...' : value}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', lineHeight: 1.4 }}
              >
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp
                  sx={{
                    fontSize: 16,
                    mr: 0.5,
                    color: trend.direction === 'up' ? 'success.main' : 'error.main',
                    transform: trend.direction === 'down' ? 'rotate(180deg)' : 'none'
                  }}
                />
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 600,
                    color: trend.direction === 'up' ? 'success.main' : 'error.main'
                  }}
                >
                  {trend.value}
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: '12px',
              backgroundColor: alpha(color, 0.1),
              color: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {icon}
          </Box>
        </Box>
        {loading && (
          <LinearProgress
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 3,
              backgroundColor: alpha(color, 0.1),
              borderRadius: '0 0 8px 8px',
              '& .MuiLinearProgress-bar': {
                backgroundColor: color,
                background: `linear-gradient(90deg, ${color} 0%, ${alpha(color, 0.7)} 50%, ${color} 100%)`,
                animation: 'progressPulse 1.5s ease-in-out infinite'
              },
              '@keyframes progressPulse': {
                '0%': { opacity: 0.8 },
                '50%': { opacity: 1 },
                '100%': { opacity: 0.8 }
              },
              '@keyframes fadeIn': {
                '0%': { opacity: 0, transform: 'translateY(10px)' },
                '100%': { opacity: 1, transform: 'translateY(0)' }
              }
            }}
          />
        )}
      </CardContent>
    </Card>
  ));

  const QuickActionCard: React.FC<{ action: QuickAction }> = memo(({ action }) => (
    <Card
      elevation={0}
      sx={{
        height: '100%',
        cursor: action.disabled ? 'default' : 'pointer',
        transition: 'all 0.3s ease',
        border: '1px solid #e2e8f0',
        opacity: action.disabled ? 0.6 : 1,
        '&:hover': action.disabled ? {} : {
          transform: 'translateY(-4px)',
          boxShadow: `0 8px 25px ${alpha(theme.palette[action.color].main, 0.15)}`,
          borderColor: alpha(theme.palette[action.color].main, 0.3)
        }
      }}
      onClick={action.disabled ? undefined : action.action}
    >
      <CardContent sx={{ p: 3, textAlign: 'center', position: 'relative' }}>
        <Box
          sx={{
            width: 56,
            height: 56,
            borderRadius: '16px',
            backgroundColor: alpha(theme.palette[action.color].main, 0.1),
            color: theme.palette[action.color].main,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
            fontSize: 24
          }}
        >
          {action.icon}
        </Box>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            mb: 1,
            fontSize: '1rem'
          }}
        >
          {action.title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ lineHeight: 1.5 }}
        >
          {action.description}
        </Typography>

        <Button
          size="small"
          color={action.color}
          variant="contained"
          disabled={action.disabled}
          onClick={(e) => {
            e.stopPropagation();
            if (!action.disabled) action.action();
          }}
          sx={{
            mt: 2,
            borderRadius: 2,
            textTransform: 'none',
            fontWeight: 600,
            px: 3
          }}
        >
          {action.disabled ? 'Coming Soon' : 'Launch'}
        </Button>
      </CardContent>
    </Card>
  ));

  const ActivityItem: React.FC<{ activity: RecentActivity }> = memo(({ activity }) => {
    const getActivityIcon = () => {
      switch (activity.type) {
        case 'video_created': return <VideoIcon sx={{ fontSize: 20 }} />;
        case 'job_completed': return <CheckCircle sx={{ fontSize: 20 }} />;
        case 'user_added': return <UsersIcon sx={{ fontSize: 20 }} />;
        case 'api_key_created': return <ApiKeyIcon sx={{ fontSize: 20 }} />;
        default: return <Timeline sx={{ fontSize: 20 }} />;
      }
    };

    const getStatusColor = () => {
      switch (activity.status) {
        case 'success': return theme.palette.success.main;
        case 'error': return theme.palette.error.main;
        case 'info': return theme.palette.info.main;
        default: return theme.palette.grey[500];
      }
    };

    const getActivityDetails = () => {
      if (activity.type === 'video_created' && activity.status === 'success') {
        return `✨ ${activity.operation?.replace('_', ' ').toLowerCase() || 'Video'} creation completed successfully`;
      } else if (activity.type === 'job_completed') {
        if (activity.status === 'success') {
          return `✅ ${activity.operation?.replace('_', ' ').toLowerCase() || 'Job'} finished processing`;
        } else if (activity.status === 'error') {
          return `❌ ${activity.operation?.replace('_', ' ').toLowerCase() || 'Job'} failed - check logs`;
        } else {
          return `⏳ ${activity.operation?.replace('_', ' ').toLowerCase() || 'Job'} in progress${activity.progress ? ` (${activity.progress}%)` : ''}`;
        }
      }
      return activity.details || 'Activity updated';
    };

    const handleActivityClick = () => {
      if (activity.type === 'video_created' && activity.status === 'success') {
        navigate(`/dashboard/library/${activity.id}`);
      } else {
        navigate('/dashboard/jobs');
      }
    };

    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 2,
          py: 1.5,
          px: 1,
          cursor: 'pointer',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            backgroundColor: alpha(theme.palette.primary.main, 0.04),
            transform: 'translateX(4px)',
            boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.1)}`
          }
        }}
        onClick={handleActivityClick}
      >
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: '10px',
            backgroundColor: alpha(getStatusColor(), 0.1),
            color: getStatusColor(),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          {getActivityIcon()}
        </Box>
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              mb: 0.5,
              lineHeight: 1.4
            }}
          >
            {activity.title}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              fontSize: '0.75rem',
              display: 'block',
              lineHeight: 1.3,
              mb: 0.5
            }}
          >
            {getActivityDetails()}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: '0.7rem', opacity: 0.8 }}
          >
            {activity.timestamp}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
          <Chip
            size="small"
            label={activity.status}
            color={activity.status === 'success' ? 'success' : activity.status === 'error' ? 'error' : 'default'}
            sx={{
              textTransform: 'capitalize',
              fontSize: '0.7rem',
              height: 20,
              '& .MuiChip-label': { px: 1 }
            }}
          />
          {activity.type === 'video_created' && activity.status === 'success' && (
            <ViewIcon sx={{ fontSize: 16, color: 'text.secondary', opacity: 0.6 }} />
          )}
        </Box>
      </Box>
    );
  });

  const refreshStats = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch dashboard stats
      const statsResponse = await directApi.getDashboardStats();
      if (statsResponse.success && statsResponse.data) {
        const apiStats = statsResponse.data;
        setStats(prev => ({
          ...prev,
          totalVideos: apiStats.total_videos,
          activeJobs: apiStats.active_jobs,
          completedJobs: apiStats.completed_jobs,
          failedJobs: apiStats.failed_jobs,
          totalUsers: apiStats.total_users,
          activeApiKeys: apiStats.active_api_keys,
          storageUsed: apiStats.storage_used_gb || 0,
          storageTotal: apiStats.storage_total_gb || 100,
          avgProcessingTime: apiStats.avg_processing_time_seconds || 0
        }));
      } else {
        setError(statsResponse.error || 'Failed to fetch dashboard stats');
      }

      // Fetch recent activity
      const activityResponse = await directApi.getRecentActivity(6);
      if (activityResponse.success && activityResponse.data && Array.isArray(activityResponse.data)) {
        setRecentActivity(activityResponse.data.map(activity => ({
          id: activity.id,
          type: activity.type as RecentActivity['type'],
          title: activity.title,
          timestamp: activity.timestamp,
          status: activity.status as RecentActivity['status'],
          details: activity.details,
          operation: activity.operation,
          progress: activity.progress
        })));
      } else if (!Array.isArray(activityResponse.data)) {
        // Log the unexpected format for debugging
        console.warn('Unexpected activity response format:', activityResponse.data);
        setRecentActivity([]);
      }
    } catch (error: unknown) {
      console.error('Failed to refresh stats:', error);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
      setInitialLoad(false);
    }
  };

  useEffect(() => {
    refreshStats();
  }, []);

  // Memoize expensive calculations
  const successRate = useMemo(() => {
    const total = stats.completedJobs + stats.failedJobs;
    return total > 0 ? Math.round((stats.completedJobs / total) * 100) : 0;
  }, [stats.completedJobs, stats.failedJobs]);

  const storagePercentage = useMemo(() => {
    return ((stats.storageUsed / stats.storageTotal) * 100).toFixed(1);
  }, [stats.storageUsed, stats.storageTotal]);

  const avgProcessingMinutes = useMemo(() => {
    return stats.avgProcessingTime > 0 ? Math.round(stats.avgProcessingTime / 60) : 0;
  }, [stats.avgProcessingTime]);

  const filteredActivity = useMemo(() => {
    return recentActivity.filter(activity =>
      userRole === 'admin' ||
      (activity.type !== 'user_added' && activity.type !== 'api_key_created')
    );
  }, [recentActivity, userRole]);

  const handleRefreshStats = useCallback(() => {
    refreshStats();
  }, []);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        mb: { xs: 2, sm: 4 },
        flexWrap: 'wrap',
        gap: 2
      }}>
        <Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              mb: 0.5,
              color: '#1a202c',
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
            }}
          >
            Welcome back! 👋
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ fontSize: { xs: '0.95rem', sm: '1.1rem' } }}
          >
            Here's what's happening with your Griot platform today.
          </Typography>
        </Box>

        <Tooltip title={loading ? "Loading..." : "Refresh Dashboard Data"}>
          <Box component="span">
            <IconButton
              onClick={handleRefreshStats}
              disabled={loading}
              sx={{
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.main,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.2),
                  transform: 'scale(1.05)',
                  boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.25)}`
                },
                '&:active': {
                  transform: 'scale(0.95)'
                },
                '&:disabled': {
                  bgcolor: alpha(theme.palette.primary.main, 0.05)
                }
              }}
            >
              <Refresh sx={{
                animation: loading ? 'spin 1s linear infinite' : 'none',
                '@keyframes spin': {
                  '0%': { transform: 'rotate(0deg)' },
                  '100%': { transform: 'rotate(360deg)' }
                }
              }} />
            </IconButton>
          </Box>
        </Tooltip>
      </Box>

      {/* Statistics Grid */}
      <Grid container spacing={{ xs: 1.5, sm: 3 }} sx={{ mb: { xs: 2, sm: 4 } }}>
        <Grid item xs={6} sm={6} lg={userRole === 'admin' ? 2.4 : 4}>
          <StatCard
            title="Total Videos"
            value={stats.totalVideos}
            icon={<VideoIcon />}
            color={theme.palette.primary.main}
            subtitle="Generated this month"
            trend={{ value: '+12%', direction: 'up' }}
            loading={loading}
          />
        </Grid>
        <Grid item xs={6} sm={6} lg={userRole === 'admin' ? 2.4 : 4}>
          <StatCard
            title="Active Jobs"
            value={stats.activeJobs}
            icon={<Schedule />}
            color={theme.palette.warning.main}
            subtitle="Currently processing"
            trend={{ value: '+3', direction: 'up' }}
            loading={loading}
          />
        </Grid>
        <Grid item xs={6} sm={6} lg={userRole === 'admin' ? 2.4 : 4}>
          <StatCard
            title="Success Rate"
            value={successRate > 0 ? `${successRate}%` : 'N/A'}
            icon={<CheckCircle />}
            color={theme.palette.success.main}
            subtitle={`${stats.completedJobs} completed, ${stats.failedJobs} failed`}
            trend={{ value: '+5%', direction: 'up' }}
            loading={loading}
          />
        </Grid>
        {userRole === 'admin' && (
          <>
            <Grid item xs={6} sm={6} lg={2.4}>
              <StatCard
                title="Storage Used"
                value={`${stats.storageUsed}GB`}
                icon={<Storage />}
                color={theme.palette.info.main}
                subtitle={`of ${stats.storageTotal}GB total`}
                trend={{
                  value: `${storagePercentage}%`,
                  direction: 'up'
                }}
                loading={loading}
              />
            </Grid>
            <Grid item xs={6} sm={6} lg={2.4}>
              <StatCard
                title="Avg Processing"
                value={avgProcessingMinutes > 0 ? `${avgProcessingMinutes}m` : 'N/A'}
                icon={<Schedule />}
                color={theme.palette.secondary.main}
                subtitle={stats.avgProcessingTime > 0 ? `${Math.round(stats.avgProcessingTime)}s average` : 'No data yet'}
                trend={stats.avgProcessingTime > 0 && stats.avgProcessingTime < 180 ?
                  { value: 'Fast', direction: 'up' } :
                  { value: 'Normal', direction: 'up' }
                }
                loading={loading}
              />
            </Grid>
          </>
        )}
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ flexGrow: 1 }}>
        {/* Quick Actions */}
        <Grid item xs={12} lg={8}>
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2, sm: 3 },
              height: '100%',
              border: '1px solid #e2e8f0',
              borderRadius: 3
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 3,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Speed sx={{ color: theme.palette.primary.main }} />
              Quick Actions
            </Typography>
            <Grid container spacing={2.5}>
              {quickActions.map((action, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <QuickActionCard action={action} />
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={4}>
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2, sm: 3 },
              height: '100%',
              border: '1px solid #e2e8f0',
              borderRadius: 3,
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Timeline sx={{ color: theme.palette.secondary.main }} />
              Recent Activity
            </Typography>
            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
              {initialLoad ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {[1, 2, 3].map((item) => (
                    <Box key={item} sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 2,
                      py: 1.5,
                      px: 1,
                      borderRadius: 2,
                      background: alpha(theme.palette.grey[50], 0.5),
                      animation: `fadeIn 0.5s ease-in-out ${item * 0.1}s both`
                    }}>
                      <Skeleton
                        variant="circular"
                        width={40}
                        height={40}
                        sx={{
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          '&::after': {
                            background: `linear-gradient(90deg, transparent, ${alpha(theme.palette.primary.main, 0.15)}, transparent)`
                          }
                        }}
                      />
                      <Box sx={{ flexGrow: 1 }}>
                        <Skeleton
                          variant="text"
                          width="70%"
                          height={20}
                          sx={{
                            mb: 0.5,
                            bgcolor: alpha(theme.palette.grey[200], 0.7),
                            '&::after': {
                              background: `linear-gradient(90deg, transparent, ${alpha(theme.palette.grey[100], 0.8)}, transparent)`
                            }
                          }}
                        />
                        <Skeleton
                          variant="text"
                          width="90%"
                          height={16}
                          sx={{
                            mb: 0.5,
                            bgcolor: alpha(theme.palette.grey[200], 0.5),
                            '&::after': {
                              background: `linear-gradient(90deg, transparent, ${alpha(theme.palette.grey[100], 0.6)}, transparent)`
                            }
                          }}
                        />
                        <Skeleton
                          variant="text"
                          width="40%"
                          height={14}
                          sx={{
                            bgcolor: alpha(theme.palette.grey[200], 0.3),
                            '&::after': {
                              background: `linear-gradient(90deg, transparent, ${alpha(theme.palette.grey[100], 0.4)}, transparent)`
                            }
                          }}
                        />
                      </Box>
                      <Skeleton
                        variant="rounded"
                        width={60}
                        height={20}
                        sx={{
                          bgcolor: alpha(theme.palette.success.main, 0.1),
                          borderRadius: 3,
                          '&::after': {
                            background: `linear-gradient(90deg, transparent, ${alpha(theme.palette.success.main, 0.2)}, transparent)`
                          }
                        }}
                      />
                    </Box>
                  ))}
                </Box>
              ) : filteredActivity.length === 0 ? (
                <Box sx={{
                  textAlign: 'center',
                  py: 3,
                  color: 'text.secondary',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 1.5,
                  border: `2px dashed ${alpha(theme.palette.grey[400], 0.3)}`,
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.grey[50], 0.5)
                }}>
                  <Box sx={{
                    width: 56,
                    height: 56,
                    borderRadius: '50%',
                    backgroundColor: alpha(theme.palette.primary.main, 0.1),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 1
                  }}>
                    <Timeline sx={{ fontSize: 24, color: theme.palette.primary.main, opacity: 0.7 }} />
                  </Box>
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.9rem' }}>
                    No recent activity
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.75rem', maxWidth: '200px', lineHeight: 1.3 }}>
                    Activity will appear here as you create videos and manage jobs
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    color="primary"
                    startIcon={<PlayArrow />}
                    onClick={() => navigate('/dashboard/video-studio')}
                    sx={{
                      mt: 1,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontSize: '0.75rem',
                      px: 2,
                      py: 0.5
                    }}
                  >
                    Create Your First Video
                  </Button>
                </Box>
              ) : (
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.5
                }}>
                  {filteredActivity.map((activity, index, filteredArray) => (
                    <React.Fragment key={activity.id}>
                      <Box sx={{
                        borderRadius: 2,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.grey[100], 0.5)
                        }
                      }}>
                        <ActivityItem activity={activity} />
                      </Box>
                      {index < filteredArray.length - 1 && (
                        <Box sx={{
                          height: 1,
                          backgroundColor: alpha(theme.palette.grey[300], 0.5),
                          mx: 3,
                          my: 0.5
                        }} />
                      )}
                    </React.Fragment>
                  ))}
                </Box>
              )}
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={() => navigate('/dashboard/jobs')}
              sx={{
                mt: 2,
                borderRadius: 2,
                textTransform: 'none'
              }}
            >
              View All Activity
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;