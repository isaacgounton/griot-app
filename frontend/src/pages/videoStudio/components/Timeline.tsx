import React from 'react';
import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import type { StudioScene } from '../types';
import { SCENE_STATUS_COLORS } from '../types';

interface TimelineProps {
  scenes: StudioScene[];
  selectedSceneId: string | null;
  onSelectScene: (id: string) => void;
  onAddScene: () => void;
  totalDuration: number;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${s}s`;
}

export default function Timeline({ scenes, selectedSceneId, onSelectScene, onAddScene, totalDuration }: TimelineProps) {
  const minWidth = 120;

  return (
    <Box sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Ruler */}
      <Box sx={{ display: 'flex', alignItems: 'center', px: 1, py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
          Timeline
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Total: {formatTime(totalDuration)}
        </Typography>
      </Box>

      {/* Scene blocks */}
      <Box sx={{ display: 'flex', overflowX: 'auto', p: 1, gap: 0.5, minHeight: 100 }}>
        {scenes.map((scene, i) => {
          const isSelected = scene.id === selectedSceneId;
          const statusColor = SCENE_STATUS_COLORS[scene.status] || '#9e9e9e';
          const widthPx = Math.max(minWidth, scene.duration * 30);

          return (
            <Box
              key={scene.id}
              onClick={() => onSelectScene(scene.id)}
              sx={{
                minWidth: widthPx,
                maxWidth: widthPx,
                height: 80,
                borderRadius: 1,
                border: isSelected ? '2px solid' : '1px solid',
                borderColor: isSelected ? 'primary.main' : 'divider',
                bgcolor: isSelected ? 'action.selected' : 'background.paper',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                transition: 'border-color 0.15s',
                '&:hover': { borderColor: 'primary.light' },
                position: 'relative',
              }}
            >
              {/* Status indicator */}
              <Box sx={{ height: 3, bgcolor: statusColor, width: '100%' }} />

              {/* Thumbnail or placeholder */}
              {scene.media_url ? (
                <Box
                  component="img"
                  src={scene.thumbnail_url || scene.media_url}
                  sx={{ width: '100%', height: 40, objectFit: 'cover' }}
                  onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              ) : (
                <Box sx={{ height: 40, bgcolor: 'grey.900', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="caption" color="grey.600">
                    Scene {i + 1}
                  </Typography>
                </Box>
              )}

              {/* Info bar */}
              <Box sx={{ px: 0.5, py: 0.25, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" noWrap sx={{ fontSize: '0.65rem', maxWidth: '60%' }}>
                  {scene.script_text ? scene.script_text.slice(0, 25) + (scene.script_text.length > 25 ? '...' : '') : 'Empty'}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                  {formatTime(scene.duration)}
                </Typography>
              </Box>
            </Box>
          );
        })}

        {/* Add scene button */}
        <Tooltip title="Add Scene">
          <IconButton
            onClick={onAddScene}
            sx={{
              minWidth: 50,
              height: 80,
              borderRadius: 1,
              border: '1px dashed',
              borderColor: 'divider',
              '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
            }}
          >
            <AddIcon />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
