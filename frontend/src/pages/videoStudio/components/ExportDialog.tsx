import { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  FormControlLabel, Checkbox, LinearProgress, Typography, Box, Alert,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import ReplayIcon from '@mui/icons-material/Replay';
import type { JobStatus } from '../types';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  onExport: (data: { include_captions: boolean; include_background_music: boolean }) => void | Promise<void>;
  jobStatus: JobStatus | null;
  isProcessing: boolean;
  finalVideoUrl: string | null;
}

export default function ExportDialog({ open, onClose, onExport, jobStatus, isProcessing, finalVideoUrl }: ExportDialogProps) {
  const [captions, setCaptions] = useState(true);
  const [music, setMusic] = useState(true);
  const [wantsReexport, setWantsReexport] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset re-export intent when dialog opens/closes
  useEffect(() => {
    if (open) {
      setWantsReexport(false);
      setIsSubmitting(false);
    }
  }, [open]);

  // Clear submitting state once polling starts (isProcessing becomes true)
  useEffect(() => {
    if (isProcessing) setIsSubmitting(false);
  }, [isProcessing]);

  const handleExport = async () => {
    setIsSubmitting(true);
    try {
      await onExport({ include_captions: captions, include_background_music: music });
      // Only hide form after API call succeeds and polling starts
      setWantsReexport(false);
    } catch {
      setIsSubmitting(false);
    }
  };

  const isExporting = isSubmitting || (isProcessing && jobStatus?.status === 'processing');
  const isCompleted = !isSubmitting && jobStatus?.status === 'completed';
  const isFailed = !isSubmitting && jobStatus?.status === 'failed';
  const freshVideoUrl = jobStatus?.result?.video_url as string | undefined;
  const videoUrl = freshVideoUrl || finalVideoUrl;

  // Show export form when: no active job, no result yet, and either no previous video or user wants re-export
  const showForm = wantsReexport || (!isExporting && !isCompleted && !isFailed && !videoUrl);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Export Video</DialogTitle>
      <DialogContent>
        {/* Previous or completed export — show video */}
        {!isExporting && !showForm && videoUrl && !isFailed && (
          <Box sx={{ mt: 2 }}>
            {isCompleted && (
              <Alert severity="success" sx={{ mb: 2 }}>Video exported successfully!</Alert>
            )}
            {!isCompleted && finalVideoUrl && (
              <Alert severity="info" sx={{ mb: 2 }}>Previously exported video</Alert>
            )}
            <video key={videoUrl} src={videoUrl} controls style={{ width: '100%', maxHeight: 300, borderRadius: 8 }} />
            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => window.open(videoUrl, '_blank')}
                sx={{ flex: 1 }}
              >
                Download
              </Button>
              <Button
                variant="outlined"
                startIcon={<ReplayIcon />}
                onClick={() => setWantsReexport(true)}
                sx={{ flex: 1 }}
              >
                Re-export
              </Button>
            </Box>
            {isCompleted && typeof jobStatus?.result?.processing_time === 'number' && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Processed in {jobStatus.result.processing_time.toFixed(1)}s
              </Typography>
            )}
          </Box>
        )}

        {/* Export form */}
        {showForm && !isExporting && (
          <Box sx={{ mt: 1 }}>
            {videoUrl && (
              <Alert severity="info" sx={{ mb: 2 }}>
                This will replace the existing exported video.
              </Alert>
            )}
            <FormControlLabel
              control={<Checkbox checked={captions} onChange={e => setCaptions(e.target.checked)} />}
              label="Include captions"
            />
            <FormControlLabel
              control={<Checkbox checked={music} onChange={e => setMusic(e.target.checked)} />}
              label="Include background music"
            />
          </Box>
        )}

        {/* Exporting progress */}
        {isExporting && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>Exporting video...</Typography>
            <LinearProgress sx={{ mb: 1 }} />
            {jobStatus?.progress && (
              <Typography variant="caption" color="text.secondary">{jobStatus.progress}</Typography>
            )}
          </Box>
        )}

        {/* Failed state */}
        {isFailed && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="error" sx={{ mb: 2 }}>
              Export failed: {jobStatus?.error || 'Unknown error'}
            </Alert>
            <Button
              variant="outlined"
              startIcon={<ReplayIcon />}
              onClick={() => setWantsReexport(true)}
              fullWidth
            >
              Retry Export
            </Button>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {showForm && !isExporting && (
          <Button variant="contained" onClick={handleExport} disabled={isProcessing || isSubmitting}>
            Start Export
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
