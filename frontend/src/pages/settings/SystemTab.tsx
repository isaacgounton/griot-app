import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Alert,
  Divider,
  alpha,
  useTheme,
  Card,
  CardContent,
} from '@mui/material';
import {
  BugReport as BugReportIcon,
  Clear as ClearIcon,
  DeleteForever as DeleteForeverIcon,
  LinkOff as LinkOffIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useVideoCreation } from '../../hooks/useContentCreation';
import { directApi } from '../../utils/api';

interface SystemInfo {
  version: string;
  api_status: string;
  database: { status: string; version?: string; size_mb?: number; tables?: number };
  redis: { status: string };
  storage: { status: string; total_gb?: number; used_gb?: number; free_gb?: number; usage_percent?: number };
  jobs?: { active?: number; completed?: number; failed?: number; total?: number };
  api_keys?: { total?: number; active?: number; total_usage?: number };
}

const SystemTab: React.FC = () => {
  const theme = useTheme();
  const { apiKey: authApiKey } = useAuth();
  const { clearAllJobs, clearOrphanedJobs } = useVideoCreation();
  const [debugStatus, setDebugStatus] = useState('');
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    version: 'Loading...',
    api_status: 'unknown',
    database: { status: 'unknown' },
    redis: { status: 'unknown' },
    storage: { status: 'unknown' },
  });

  const loadSystemInfo = useCallback(async () => {
    if (!authApiKey) return;
    try {
      const result = await directApi.getSystemInfo();
      if (result.success && result.data) setSystemInfo(result.data);
    } catch { /* ignore */ }
  }, [authApiKey]);

  useEffect(() => { loadSystemInfo(); }, [loadSystemInfo]);

  const showDebug = (msg: string, timeout = 3000) => {
    setDebugStatus(msg);
    setTimeout(() => setDebugStatus(''), timeout);
  };

  const handleClearOrphanedJobs = async () => {
    try {
      showDebug('Checking for orphaned jobs...', 60000);
      await clearOrphanedJobs();
      showDebug('✅ Cleaned up orphaned jobs');
    } catch (e) {
      showDebug(`❌ Error: ${e}`, 5000);
    }
  };

  const handleClearAllJobs = () => {
    try {
      clearAllJobs();
      showDebug('✅ Cleared all jobs from localStorage');
    } catch (e) {
      showDebug(`❌ Error: ${e}`, 5000);
    }
  };

  const handleCleanupOrphanedFiles = async () => {
    if (!window.confirm('Delete library records pointing to missing S3 files?')) return;
    try {
      showDebug('Scanning for orphaned files...', 60000);
      const result = await directApi.cleanupOrphanedFiles(true, false);
      if (result.success && result.data) {
        showDebug(`✅ Removed ${result.data.deleted_records} broken records (${result.data.missing_files_found} missing files)`);
      } else {
        showDebug(`❌ ${result.error}`, 5000);
      }
    } catch (e) {
      showDebug(`❌ Error: ${e}`, 5000);
    }
  };

  const handleDeleteAllContent = async () => {
    if (window.prompt('Type "DELETE ALL" to confirm deleting ALL content:') !== 'DELETE ALL') return;
    try {
      showDebug('Deleting ALL content...', 60000);
      const result = await directApi.deleteAllLibraryContent();
      if (result.success && result.data) {
        showDebug(`✅ Deleted ${result.data.deleted_records} items and ${result.data.deleted_s3_files} S3 files`);
      } else {
        showDebug(`❌ ${result.error}`, 5000);
      }
    } catch (e) {
      showDebug(`❌ Error: ${e}`, 5000);
    }
  };

  const StatusValue: React.FC<{ label: string; value: string; color?: string; sub?: string }> = ({ label, value, color, sub }) => (
    <Grid item xs={6} sm={4} md={3}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body1" fontWeight="medium" color={color || 'text.primary'}>{value}</Typography>
      {sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}
    </Grid>
  );

  return (
    <Box>
      {/* System Information */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(theme.palette.info.main, 0.1), color: theme.palette.info.main }}>
            <SecurityIcon />
          </Box>
          <Typography variant="h6" fontWeight="medium">System Information</Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={2}>
          <StatusValue label="Version" value={`Griot v${systemInfo.version}`} />
          <StatusValue
            label="API Status"
            value={systemInfo.api_status?.charAt(0).toUpperCase() + systemInfo.api_status?.slice(1)}
            color={systemInfo.api_status === 'operational' ? 'success.main' : 'error.main'}
          />
          <StatusValue
            label="Database"
            value={systemInfo.database.status?.charAt(0).toUpperCase() + systemInfo.database.status?.slice(1)}
            color={systemInfo.database.status === 'connected' ? 'success.main' : 'error.main'}
            sub={systemInfo.database.size_mb ? `${systemInfo.database.size_mb}MB, ${systemInfo.database.tables} tables` : undefined}
          />
          <StatusValue
            label="Storage"
            value={systemInfo.storage.status?.charAt(0).toUpperCase() + systemInfo.storage.status?.slice(1)}
            color={systemInfo.storage.status === 'available' ? 'success.main' : 'error.main'}
            sub={systemInfo.storage.used_gb && systemInfo.storage.total_gb ? `${systemInfo.storage.used_gb}GB / ${systemInfo.storage.total_gb}GB (${systemInfo.storage.usage_percent}%)` : undefined}
          />
          <StatusValue
            label="Redis Cache"
            value={systemInfo.redis.status?.charAt(0).toUpperCase() + systemInfo.redis.status?.slice(1)}
            color={systemInfo.redis.status === 'connected' ? 'success.main' : 'error.main'}
          />
          {systemInfo.jobs && (
            <StatusValue label="Jobs" value={`${systemInfo.jobs.active || 0} active, ${systemInfo.jobs.completed || 0} completed`} />
          )}
          {systemInfo.api_keys && (
            <StatusValue label="API Keys" value={`${systemInfo.api_keys.active || 0} active, ${systemInfo.api_keys.total_usage || 0} total usage`} />
          )}
        </Grid>
      </Paper>

      {/* Debug Tools */}
      <Card elevation={1}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{ p: 1, borderRadius: 1, backgroundColor: alpha(theme.palette.warning.main, 0.1), color: theme.palette.warning.main }}>
              <BugReportIcon />
            </Box>
            <Box>
              <Typography variant="h6" fontWeight="medium">Debug Tools</Typography>
              <Typography variant="body2" color="text.secondary">Development and troubleshooting utilities</Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Button variant="outlined" size="small" startIcon={<ClearIcon />} onClick={handleClearOrphanedJobs} fullWidth>
              Clear Orphaned Jobs (Client)
            </Button>
            <Button variant="outlined" size="small" startIcon={<LinkOffIcon />} onClick={handleCleanupOrphanedFiles} color="warning" fullWidth>
              Fix Broken Library Links (Server)
            </Button>
            <Button variant="outlined" size="small" startIcon={<ClearIcon />} onClick={handleClearAllJobs} color="warning" fullWidth>
              Clear All Jobs (Client)
            </Button>
            <Button variant="contained" size="small" startIcon={<DeleteForeverIcon />} onClick={handleDeleteAllContent} color="error" fullWidth sx={{ mt: 1 }}>
              Delete EVERYTHING (Library & S3)
            </Button>
            {debugStatus && (
              <Alert severity={debugStatus.includes('❌') ? 'error' : 'success'} sx={{ mt: 1 }}>
                {debugStatus}
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemTab;
