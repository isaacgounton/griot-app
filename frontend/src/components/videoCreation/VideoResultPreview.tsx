import { Box, Button, IconButton, Tooltip } from '@mui/material';
import DownloadIcon from '@mui/icons-material/CloudDownload';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

interface VideoResultPreviewProps {
  url: string;
  /** Max height for the video player. Defaults to 420. */
  maxHeight?: number;
}

/**
 * Compact, centered video player for generated video results.
 * Constrains height (especially for tall 9:16 portrait videos),
 * adds a dark backdrop, and provides action buttons.
 */
export default function VideoResultPreview({ url, maxHeight = 420 }: VideoResultPreviewProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5 }}>
      {/* Video container — dark backdrop with constrained size */}
      <Box
        sx={{
          width: '100%',
          maxWidth: 480,
          bgcolor: '#0f0f0f',
          borderRadius: 3,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        }}
      >
        <video
          src={url}
          controls
          style={{
            display: 'block',
            width: '100%',
            maxHeight,
            objectFit: 'contain',
          }}
        />
      </Box>

      {/* Action buttons */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Button
          variant="contained"
          size="small"
          startIcon={<DownloadIcon />}
          href={url}
          target="_blank"
          sx={{ textTransform: 'none', borderRadius: 2, px: 2 }}
        >
          Download
        </Button>
        <Tooltip title="Copy video URL">
          <IconButton
            size="small"
            onClick={() => navigator.clipboard.writeText(url)}
            sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Open in new tab">
          <IconButton
            size="small"
            onClick={() => window.open(url, '_blank')}
            sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
          >
            <OpenInNewIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
