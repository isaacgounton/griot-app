import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardMedia,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
  InputAdornment,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Avatar,
  Tooltip,
  CardActionArea,
  CardActions,
  Stack
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  VideoLibrary as VideoIcon,
  AudioFile as AudioIcon,
  Image as ImageIcon,
  TextSnippet as TextIcon,
  PlayArrow as PlayIcon,
  Download as _DownloadIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Visibility as PreviewIcon,
  GetApp as GetAppIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Delete as DeleteIcon,
  Schedule as ScheduleIcon,
  ContentCopy as ContentCopyIcon
} from '@mui/icons-material';

import { directApi } from '../utils/api';
import { PostizScheduleDialog } from '../components/PostizScheduleDialog';
import { JobStatus } from '../types/griot';

// Content Types
// eslint-disable-next-line react-refresh/only-export-components
export enum ContentType {
  // eslint-disable-next-line no-unused-vars
  VIDEO = 'video',
  // eslint-disable-next-line no-unused-vars
  AUDIO = 'audio',
  // eslint-disable-next-line no-unused-vars
  IMAGE = 'image',
  // eslint-disable-next-line no-unused-vars
  TEXT = 'text',
  // eslint-disable-next-line no-unused-vars
  ALL = 'all'
}

// Content Item Interface
interface ContentItem {
  job_id: string;
  job_type: string;
  content_type: ContentType;
  title?: string;
  description?: string;
  file_url: string;
  thumbnail_url?: string;
  file_size?: number;
  duration?: number;
  dimensions?: { width: number; height: number };
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  parameters: Record<string, unknown>;
}

// Library Response Interface
interface LibraryResponse {
  content: ContentItem[];
  total_count: number;
  content_type_filter: ContentType;
  pagination: {
    limit: number;
    offset: number;
    total_count: number;
    has_next: boolean;
    has_previous: boolean;
    next_offset?: number;
    previous_offset?: number;
  };
}

// Stats Interface
interface LibraryStats {
  stats: {
    video: number;
    audio: number;
    image: number;
    text: number;
    total: number;
  };
  total_items: number;
}

// Helper function to generate user-friendly title from job_type
const generateTitleFromJobType = (jobType: string, _fallbackId?: string): string => {
  // Map of job type patterns to user-friendly titles
  const typeMapping: Record<string, string> = {
    'IMAGE_GENERATION': 'AI Generated Image',
    'IMAGE_EDITING': 'Edited Image',
    'IMAGE_UPSCALING': 'Upscaled Image',
    'TEXT_TO_SPEECH': 'AI Voice Recording',
    'MUSIC_GENERATION': 'AI Generated Music',
    'AUDIO_TRANSCRIPTION': 'Audio Transcription',
    'VOICE_CLONING': 'Voice Clone',
    'FOOTAGE_TO_VIDEO': 'Stock Footage Video',
    'AIIMAGE_TO_VIDEO': 'AI Image to Video',
    'SCENES_TO_VIDEO': 'Scenes Compilation Video',
    'SHORT_VIDEO_CREATION': 'Short Video',
    'IMAGE_TO_VIDEO': 'Image to Video',
    'MEDIA_DOWNLOAD': 'Downloaded Media',
    'MEDIA_CONVERSION': 'Converted Media',
    'METADATA_EXTRACTION': 'Media Metadata',
    'YOUTUBE_TRANSCRIPT': 'YouTube Transcript',
    'VIDEO_COMPOSITION': 'Video Composition',
    'VIDEO_COMPOSITE': 'Video Composite',
  };

  // Check if we have a direct mapping
  const upperJobType = jobType.toUpperCase().replace(/-/g, '_');
  if (typeMapping[upperJobType]) {
    return typeMapping[upperJobType];
  }

  // Otherwise, convert job_type to readable format
  return jobType
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/\s+/g, ' ')
    .trim();
};

const Library: React.FC = () => {
  // State
  const [content, setContent] = useState<ContentItem[]>([]);
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [contentTypeFilter, setContentTypeFilter] = useState<ContentType>(ContentType.ALL);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<string | null>(null);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [itemToSchedule, setItemToSchedule] = useState<ContentItem | null>(null);

  const itemsPerPage = 20;

  // Helper function to safely access metadata properties
  const isFavorite = (item: ContentItem): boolean => {
    return Boolean(item.metadata && typeof item.metadata === 'object' && 'is_favorite' in item.metadata && item.metadata.is_favorite);
  };

  // Helper function to render media preview based on content type
  const renderMediaPreview = (item: ContentItem) => {
    const typeDisplay = contentTypeConfig[item.content_type as ContentType] || contentTypeConfig[ContentType.ALL];

    // For images, show the actual image
    if (item.content_type === ContentType.IMAGE && item.file_url) {
      return (
        <Box sx={{ position: 'relative', height: '100%', overflow: 'hidden' }}>
          <CardMedia
            component="img"
            height="180"
            image={item.file_url}
            alt={item.title || 'Image content'}
            sx={{
              objectFit: 'cover',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'scale(1.05)'
              }
            }}
          />
          {/* Preview overlay on hover */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              bgcolor: 'rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0,
              transition: 'opacity 0.3s ease',
              '&:hover': {
                opacity: 1
              }
            }}
          >
            <PreviewIcon sx={{ color: 'white', fontSize: 32 }} />
          </Box>
        </Box>
      );
    }

    // For videos, show thumbnail with play overlay
    if (item.content_type === ContentType.VIDEO) {
      return (
        <Box sx={{ position: 'relative', height: 180, overflow: 'hidden' }}>
          {item.thumbnail_url ? (
            <CardMedia
              component="img"
              height="180"
              image={item.thumbnail_url}
              alt={item.title || 'Video content'}
              sx={{
                objectFit: 'cover',
                transition: 'transform 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)'
                }
              }}
            />
          ) : (
            <CardMedia
              component="video"
              height="180"
              src={item.file_url}
              sx={{
                objectFit: 'cover',
                transition: 'transform 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)'
                }
              }}
              preload="metadata"
              muted
            />
          )}
          {/* Play overlay */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              bgcolor: 'rgba(0,0,0,0.7)',
              borderRadius: '50%',
              width: 56,
              height: 56,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              transition: 'all 0.3s ease',
              '&:hover': {
                bgcolor: 'rgba(0,0,0,0.8)',
                transform: 'translate(-50%, -50%) scale(1.1)'
              }
            }}
          >
            <PlayIcon sx={{ fontSize: 32 }} />
          </Box>
          {/* Duration badge */}
          {item.duration && (
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                right: 8,
                bgcolor: 'rgba(0,0,0,0.8)',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.75rem'
              }}
            >
              {formatDuration(item.duration)}
            </Box>
          )}
        </Box>
      );
    }

    // For audio, show enhanced waveform visualization
    if (item.content_type === ContentType.AUDIO) {
      // Create consistent wave heights based on title hash for same content
      const titleHash = (item.title || item.job_id).split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
      }, 0);

      return (
        <Box
          sx={{
            height: 180,
            background: 'linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 50%, #45b7d1 100%)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {/* Background pattern */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: 0.1,
              background: 'radial-gradient(circle at 30% 20%, rgba(255,255,255,0.3) 0%, transparent 50%)'
            }}
          />

          {/* Main audio icon */}
          <AudioIcon sx={{ fontSize: 48, color: 'white', opacity: 0.9, zIndex: 1 }} />

          {/* Enhanced audio wave visualization */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 15,
              left: 15,
              right: 15,
              height: 50,
              display: 'flex',
              alignItems: 'end',
              gap: 0.5,
              zIndex: 1
            }}
          >
            {[...Array(20)].map((_, i) => {
              const height = 15 + Math.abs(Math.sin((titleHash + i) * 0.5)) * 30;
              return (
                <Box
                  key={i}
                  sx={{
                    flex: 1,
                    height: `${height}px`,
                    bgcolor: 'rgba(255,255,255,0.8)',
                    borderRadius: 0.5,
                    transition: 'height 0.3s ease',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,1)',
                      height: `${height + 5}px`
                    }
                  }}
                />
              );
            })}
          </Box>

          {/* Duration badge */}
          {item.duration && (
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                bgcolor: 'rgba(0,0,0,0.7)',
                color: 'white',
                px: 1.5,
                py: 0.5,
                borderRadius: 2,
                fontSize: '0.75rem',
                fontWeight: 600
              }}
            >
              🎵 {formatDuration(item.duration)}
            </Box>
          )}
        </Box>
      );
    }

    // For text content, show elegant text preview
    if (item.content_type === ContentType.TEXT) {
      const textContent = item.title || item.description || 'Text Content';
      const previewText = textContent.length > 120 ? textContent.substring(0, 120) + '...' : textContent;

      return (
        <Box
          sx={{
            height: 180,
            background: 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3
          }}
        >
          {/* Background pattern */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: 0.1,
              background: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.3'%3E%3Cpath d='m36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }}
          />

          {/* Text icon */}
          <TextIcon sx={{ fontSize: 32, color: 'white', mb: 2, opacity: 0.9 }} />

          {/* Text preview */}
          <Typography
            variant="body2"
            sx={{
              color: 'white',
              textAlign: 'center',
              lineHeight: 1.4,
              fontSize: '0.85rem',
              fontFamily: 'monospace',
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical',
              textShadow: '0 1px 2px rgba(0,0,0,0.5)',
              zIndex: 1
            }}
          >
            "{previewText}"
          </Typography>

          {/* Word count badge */}
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              bgcolor: 'rgba(255,255,255,0.2)',
              color: 'white',
              px: 1.5,
              py: 0.5,
              borderRadius: 2,
              fontSize: '0.7rem',
              fontWeight: 600,
              backdropFilter: 'blur(4px)'
            }}
          >
            📄 {textContent.split(' ').length} words
          </Box>
        </Box>
      );
    }

    // Fallback for other content types or missing thumbnails
    if (item.thumbnail_url) {
      return (
        <CardMedia
          component="img"
          height="180"
          image={item.thumbnail_url}
          alt={item.title || 'Content thumbnail'}
          sx={{ objectFit: 'cover' }}
        />
      );
    }

    // Default fallback
    return (
      <Box
        sx={{
          height: 180,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'grey.50'
        }}
      >
        <Avatar
          sx={{
            width: 64,
            height: 64,
            bgcolor: `${typeDisplay.color}.light`
          }}
        >
          {typeDisplay.icon}
        </Avatar>
      </Box>
    );
  };

  // Content type configuration
  const contentTypeConfig = {
    [ContentType.ALL]: { label: 'All Content', icon: <FilterIcon />, color: 'default' as const },
    [ContentType.VIDEO]: { label: 'Videos', icon: <VideoIcon />, color: 'primary' as const },
    [ContentType.AUDIO]: { label: 'Audio', icon: <AudioIcon />, color: 'secondary' as const },
    [ContentType.IMAGE]: { label: 'Images', icon: <ImageIcon />, color: 'success' as const },
    [ContentType.TEXT]: { label: 'Text', icon: <TextIcon />, color: 'info' as const },
  };

  // Fetch library content
  const fetchLibraryContent = async (
    page: number = 1,
    contentType: ContentType = ContentType.ALL,
    search: string = ''
  ) => {
    try {
      setLoading(true);
      setError(null);

      const offset = (page - 1) * itemsPerPage;
      const params = new URLSearchParams({
        limit: itemsPerPage.toString(),
        offset: offset.toString(),
        content_type: contentType
      });

      if (search.trim()) {
        params.append('search', search.trim());
      }

      const response = await directApi.get(`/library/content?${params}`);
      const data: LibraryResponse = response.data;

      setContent(data.content);
      setTotalItems(data.total_count);
      setTotalPages((data.pagination as any)?.total_pages || Math.ceil(data.total_count / itemsPerPage));

    } catch (err) {
      console.error('Error fetching library content:', err);
      setError('Failed to load library content');
      setContent([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch library stats
  const fetchLibraryStats = async () => {
    try {
      const response = await directApi.get('/library/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching library stats:', err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLibraryContent(currentPage, contentTypeFilter, searchQuery);
    fetchLibraryStats();
  }, [currentPage, contentTypeFilter, searchQuery]);

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
    fetchLibraryContent(1, contentTypeFilter, query);
  };

  // Handle content type filter
  const handleContentTypeFilter = (type: ContentType) => {
    setContentTypeFilter(type);
    setCurrentPage(1);
    fetchLibraryContent(1, type, searchQuery);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchLibraryContent(page, contentTypeFilter, searchQuery);
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchLibraryContent(currentPage, contentTypeFilter, searchQuery);
    fetchLibraryStats();
  };

  // Handle favorite toggle
  const handleFavoriteToggle = async (item: ContentItem, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    try {
      await directApi.post(`/library/favorite/${item.job_id}`, {});
      // Update the item in the content array
      setContent(prevContent =>
        prevContent.map(contentItem =>
          contentItem.job_id === item.job_id
            ? { ...contentItem, metadata: { ...contentItem.metadata, is_favorite: !isFavorite(contentItem) } }
            : contentItem
        )
      );
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  // Handle delete
  const handleDelete = (item: ContentItem, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setItemToDelete(item.job_id);
    setDeleteDialogOpen(true);
  };

  // Confirm delete
  const confirmDelete = async () => {
    if (!itemToDelete) return;

    try {
      await directApi.delete(`/library/content/${itemToDelete}`);
      // Remove the item from the content array
      setContent(prevContent => prevContent.filter(item => item.job_id !== itemToDelete));
      setTotalItems(prev => prev - 1);
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  // Cancel delete
  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  // Format file size
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
  };

  // Format duration
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get content type icon and color
  const getContentTypeDisplay = (type: ContentType) => {
    const config = contentTypeConfig[type];
    return {
      icon: config.icon,
      label: config.label,
      color: config.color
    };
  };

  // Handle item click
  const handleItemClick = (item: ContentItem) => {
    setSelectedItem(item);
    setPreviewOpen(true);
  };

  // Close preview
  const closePreview = () => {
    setPreviewOpen(false);
    setSelectedItem(null);
  };

  // Generate dynamic tags based on content
  const generateTags = (item: ContentItem): string[] => {
    const tags = [];

    // Content type tag
    tags.push(`#${item.content_type}`);

    // AI/automation tags
    tags.push('#AI', '#automation');

    // Content-specific tags
    if (item.content_type === 'video') {
      tags.push('#video', '#content', '#viral');
    } else if (item.content_type === 'image') {
      tags.push('#image', '#design', '#creative');
    } else if (item.content_type === 'audio') {
      tags.push('#audio', '#podcast', '#voice');
    }

    // Extract keywords from title/description for tags
    const text = (item.title || item.description || '').toLowerCase();
    if (text.includes('jesus') || text.includes('faith') || text.includes('savior')) {
      tags.push('#faith', '#inspiration');
    }
    if (text.includes('music') || text.includes('song')) {
      tags.push('#music');
    }
    if (text.includes('tutorial') || text.includes('how')) {
      tags.push('#tutorial', '#howto');
    }
    if (text.includes('business') || text.includes('entrepreneur')) {
      tags.push('#business', '#entrepreneur');
    }

    return tags;
  };

  // Generate suggested social media content
  const generateSuggestedContent = (item: ContentItem): string => {
    const title = item.title || item.description || 'Generated Content';
    const tags = generateTags(item).join(' ');

    // Add emoji based on content type
    let emoji = '✨';
    if (item.content_type === 'video') {
      emoji = '🎬';
    } else if (item.content_type === 'image') {
      emoji = '🖼️';
    } else if (item.content_type === 'audio') {
      emoji = '🎵';
    }

    return `${emoji} ${title} ${tags}`;
  };

  /* handleDownload - reserved for future use
  const handleDownload = (item: ContentItem, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    if (item.file_url) {
      window.open(item.file_url, '_blank');
    }
  }; */

  // Handle schedule
  const handleSchedule = (item: ContentItem, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setItemToSchedule(item);
    setScheduleDialogOpen(true);
  };

  // Handle schedule submission
  const handleScheduleSubmit = async (data: {
    jobId: string;
    content: string;
    integrations: string[];
    postType: 'now' | 'schedule' | 'draft';
    scheduleDate?: Date;
    tags: string[];
  }) => {
    if (!itemToSchedule) return;

    try {
      const apiKey = localStorage.getItem('griot_api_key');
      if (!apiKey) {
        throw new Error('API key not found');
      }

      const payload = {
        content: data.content,
        integrations: data.integrations,
        post_type: data.postType,
        schedule_date: data.scheduleDate?.toISOString(),
        tags: data.tags
      };

      const response = await directApi.post(
        `/library/content/${itemToSchedule.job_id}/schedule`,
        payload
      );

      if (response.status === 200) {
        // Content scheduled successfully - could add a success toast here
      }
    } catch (error) {
      console.error('Failed to schedule content:', error);
      throw error;
    }
  };

  // Close schedule dialog
  const closeScheduleDialog = () => {
    setScheduleDialogOpen(false);
    setItemToSchedule(null);
  };

  // Render content grid
  const renderContentGrid = () => (
    <Grid container spacing={{ xs: 2, sm: 3, md: 3 }}>
      {content.map((item) => {
        const typeDisplay = getContentTypeDisplay(item.content_type);
        return (
          <Grid item xs={12} sm={6} md={4} lg={3} xl={2} key={item.job_id}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <Box sx={{ position: 'relative' }}>
                {/* Delete button overlay - positioned outside CardActionArea to avoid nested buttons */}
                <Tooltip title="Delete">
                  <IconButton
                    onClick={(e) => handleDelete(item, e)}
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      bgcolor: 'error.main',
                      color: 'white',
                      border: '2px solid white',
                      width: 32,
                      height: 32,
                      transition: 'all 0.2s ease-in-out',
                      zIndex: 2, // Ensure it's above other elements
                      '&:hover': {
                        bgcolor: 'error.dark',
                        transform: 'scale(1.1)',
                        boxShadow: 3
                      },
                      '& .MuiSvgIcon-root': {
                        fontSize: '1rem'
                      }
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>

                <CardActionArea onClick={() => handleItemClick(item)} sx={{ height: '100%' }}>
                  {/* Thumbnail */}
                  <Box sx={{ position: 'relative', height: 180, bgcolor: 'grey.100' }}>
                    {renderMediaPreview(item)}

                    {/* Content type badge */}
                    <Chip
                      size="small"
                      label={typeDisplay.label}
                      color={typeDisplay.color}
                      sx={{ position: 'absolute', top: 8, right: 8 }}
                    />

                    {/* Favorite indicator */}
                    {isFavorite(item) && (
                      <FavoriteIcon
                        sx={{
                          position: 'absolute',
                          top: 48, // Moved down to avoid overlap with delete button
                          left: 8,
                          color: 'error.main',
                          bgcolor: 'rgba(255,255,255,0.9)',
                          borderRadius: '50%',
                          p: 0.5
                        }}
                      />
                    )}

                    {/* Duration badge for video/audio */}
                    {item.duration && (
                      <Chip
                        size="small"
                        label={formatDuration(item.duration)}
                        sx={{
                          position: 'absolute',
                          bottom: 8,
                          right: 8,
                          bgcolor: 'rgba(0,0,0,0.7)',
                          color: 'white'
                        }}
                      />
                    )}
                  </Box>

                  <CardContent sx={{ flexGrow: 1, pb: '16px !important' }}>
                    <Typography
                      variant="h6"
                      noWrap
                      gutterBottom
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' }
                      }}
                    >
                      {item.title || generateTitleFromJobType(item.job_type)}
                    </Typography>

                    {item.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: '-webkit-box',
                          WebkitLineClamp: { xs: 3, sm: 2 },
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          fontSize: { xs: '0.8rem', sm: '0.875rem' }
                        }}
                      >
                        {item.description}
                      </Typography>
                    )}

                    <Stack
                      direction="row"
                      spacing={1}
                      sx={{
                        mt: 2,
                        flexWrap: 'wrap',
                        gap: 0.5
                      }}
                    >
                      {item.file_size && (
                        <Chip
                          size="small"
                          label={formatFileSize(item.file_size)}
                          sx={{
                            fontSize: { xs: '0.65rem', sm: '0.75rem' },
                            height: { xs: 20, sm: 24 }
                          }}
                        />
                      )}
                      {item.dimensions && (
                        <Chip
                          size="small"
                          label={`${item.dimensions.width}×${item.dimensions.height}`}
                          sx={{
                            fontSize: { xs: '0.65rem', sm: '0.75rem' },
                            height: { xs: 20, sm: 24 }
                          }}
                        />
                      )}
                    </Stack>

                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Box>

              <CardActions
                sx={{
                  justifyContent: 'space-between',
                  px: 2,
                  pb: 2,
                  flexWrap: 'wrap',
                  gap: 1
                }}
              >
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Tooltip title={isFavorite(item) ? "Remove from favorites" : "Add to favorites"}>
                    <IconButton
                      size="small"
                      onClick={(e) => handleFavoriteToggle(item, e)}
                      color={isFavorite(item) ? "error" : "default"}
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.25rem' },
                        '& .MuiSvgIcon-root': {
                          fontSize: { xs: '1rem', sm: '1.25rem' }
                        }
                      }}
                    >
                      {isFavorite(item) ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Schedule to Social Media">
                    <IconButton
                      size="small"
                      onClick={(e) => handleSchedule(item, e)}
                      color="primary"
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.25rem' },
                        '& .MuiSvgIcon-root': {
                          fontSize: { xs: '1rem', sm: '1.25rem' }
                        }
                      }}
                    >
                      <ScheduleIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Tooltip title="Quick Preview">
                    <IconButton
                      size="small"
                      onClick={() => handleItemClick(item)}
                      color="primary"
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.25rem' },
                        '& .MuiSvgIcon-root': {
                          fontSize: { xs: '1rem', sm: '1.25rem' }
                        }
                      }}
                    >
                      <PreviewIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleItemClick(item)}
                      color="secondary"
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.25rem' },
                        '& .MuiSvgIcon-root': {
                          fontSize: { xs: '1rem', sm: '1.25rem' }
                        }
                      }}
                    >
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardActions>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );

  // Render content list
  const renderContentList = () => (
    <Stack spacing={2}>
      {content.map((item) => {
        const typeDisplay = getContentTypeDisplay(item.content_type);
        return (
          <Card key={item.job_id} sx={{ cursor: 'pointer' }}>
            <CardActionArea onClick={() => handleItemClick(item)}>
              <CardContent>
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={2}
                  alignItems={{ xs: 'flex-start', sm: 'center' }}
                  sx={{
                    width: '100%',
                    gap: { xs: 1, sm: 2 }
                  }}
                >
                  {/* Delete button - positioned on the left for visibility */}
                  <Box sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    order: { xs: 3, sm: 0 }, // On mobile, show after content; on desktop, show first
                    alignSelf: { xs: 'center', sm: 'flex-start' },
                    pt: { xs: 0, sm: 1 }
                  }}>
                    <Tooltip title="Delete">
                      <IconButton
                        onClick={(e) => handleDelete(item, e)}
                        size="small"
                        color="error"
                        sx={{
                          fontSize: { xs: '1.1rem', sm: '1.25rem' },
                          '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1.1rem', sm: '1.25rem' }
                          },
                          minWidth: { xs: '36px', sm: '40px' },
                          minHeight: { xs: '36px', sm: '40px' },
                          bgcolor: 'error.main',
                          color: 'white',
                          border: '2px solid',
                          borderColor: 'error.main',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            bgcolor: 'error.dark',
                            borderColor: 'error.dark',
                            transform: 'scale(1.1)',
                            boxShadow: 3
                          }
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>

                  {/* Thumbnail or icon */}
                  {item.content_type === ContentType.IMAGE && item.file_url ? (
                    <Box
                      sx={{
                        width: { xs: '100%', sm: 80 },
                        height: { xs: 120, sm: 80 },
                        borderRadius: 1,
                        overflow: 'hidden',
                        flexShrink: 0,
                        alignSelf: { xs: 'center', sm: 'auto' }
                      }}
                    >
                      <img
                        src={item.file_url}
                        alt={item.title || 'Image'}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                      />
                    </Box>
                  ) : item.thumbnail_url ? (
                    <Box
                      sx={{
                        width: { xs: '100%', sm: 80 },
                        height: { xs: 120, sm: 80 },
                        borderRadius: 1,
                        overflow: 'hidden',
                        flexShrink: 0,
                        position: 'relative',
                        alignSelf: { xs: 'center', sm: 'auto' }
                      }}
                    >
                      <img
                        src={item.thumbnail_url}
                        alt={item.title || 'Thumbnail'}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                      />
                      {item.content_type === ContentType.VIDEO && (
                        <Box
                          sx={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            bgcolor: 'rgba(0,0,0,0.7)',
                            borderRadius: '50%',
                            width: 24,
                            height: 24,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <PlayIcon sx={{ fontSize: 14, color: 'white' }} />
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Avatar
                      sx={{
                        bgcolor: `${typeDisplay.color}.light`,
                        width: { xs: '100%', sm: 80 },
                        height: { xs: 120, sm: 80 },
                        alignSelf: { xs: 'center', sm: 'auto' }
                      }}
                    >
                      {typeDisplay.icon}
                    </Avatar>
                  )}

                  <Box
                    sx={{
                      flexGrow: 1,
                      width: { xs: '100%', sm: 'auto' }
                    }}
                  >
                    <Typography
                      variant="h6"
                      sx={{
                        fontSize: { xs: '1.1rem', sm: '1.25rem' }
                      }}
                    >
                      {item.title || generateTitleFromJobType(item.job_type)}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        fontSize: { xs: '0.85rem', sm: '0.875rem' }
                      }}
                    >
                      {item.description || `${typeDisplay.label} • ${new Date(item.created_at).toLocaleDateString()}`}
                    </Typography>
                  </Box>

                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{
                      width: { xs: '100%', sm: 'auto' },
                      justifyContent: { xs: 'space-between', sm: 'flex-end' },
                      pt: { xs: 1, sm: 0 }
                    }}
                  >
                    {item.duration && (
                      <Chip
                        size="small"
                        label={formatDuration(item.duration)}
                        sx={{
                          fontSize: { xs: '0.7rem', sm: '0.75rem' },
                          height: { xs: 20, sm: 24 }
                        }}
                      />
                    )}
                    {item.file_size && (
                      <Chip
                        size="small"
                        label={formatFileSize(item.file_size)}
                        sx={{
                          fontSize: { xs: '0.7rem', sm: '0.75rem' },
                          height: { xs: 20, sm: 24 }
                        }}
                      />
                    )}
                    <Tooltip title={isFavorite(item) ? "Remove from favorites" : "Add to favorites"}>
                      <IconButton
                        onClick={(e) => handleFavoriteToggle(item, e)}
                        size="small"
                        color={isFavorite(item) ? "error" : "default"}
                        sx={{
                          fontSize: { xs: '1rem', sm: '1.25rem' },
                          '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1rem', sm: '1.25rem' }
                          },
                          minWidth: '40px',
                          minHeight: '40px'
                        }}
                      >
                        {isFavorite(item) ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Schedule to Social Media">
                      <IconButton
                        onClick={(e) => handleSchedule(item, e)}
                        size="small"
                        color="primary"
                        sx={{
                          fontSize: { xs: '1rem', sm: '1.25rem' },
                          '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1rem', sm: '1.25rem' }
                          },
                          minWidth: '40px',
                          minHeight: '40px'
                        }}
                      >
                        <ScheduleIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Quick Preview">
                      <IconButton
                        onClick={() => handleItemClick(item)}
                        size="small"
                        color="primary"
                        sx={{
                          fontSize: { xs: '1rem', sm: '1.25rem' },
                          '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1rem', sm: '1.25rem' }
                          },
                          minWidth: '40px',
                          minHeight: '40px'
                        }}
                      >
                        <PreviewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="View Details">
                      <IconButton
                        onClick={() => handleItemClick(item)}
                        size="small"
                        color="secondary"
                        sx={{
                          fontSize: { xs: '1rem', sm: '1.25rem' },
                          '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1rem', sm: '1.25rem' }
                          },
                          minWidth: '40px',
                          minHeight: '40px'
                        }}
                      >
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        );
      })}
    </Stack>
  );

  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 3, sm: 4 } }}>
        <Typography
          variant="h4"
          gutterBottom
          sx={{
            fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' }
          }}
        >
          Content Library
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '0.9rem', sm: '1rem' }
          }}
        >
          Browse and manage all your generated content
        </Typography>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={{ xs: 1, sm: 2 }} sx={{ mb: 4 }}>
          {Object.entries(contentTypeConfig).filter(([key]) => key !== ContentType.ALL).map(([type, config]) => (
            <Grid item xs={6} sm={3} key={type}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': { transform: 'translateY(-2px)', boxShadow: 2 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onClick={() => handleContentTypeFilter(type as ContentType)}
              >
                <CardContent
                  sx={{
                    textAlign: 'center',
                    py: { xs: 1.5, sm: 2 },
                    px: { xs: 1, sm: 2 },
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: `${config.color}.light`,
                      mx: 'auto',
                      mb: { xs: 0.5, sm: 1 },
                      width: { xs: 40, sm: 48 },
                      height: { xs: 40, sm: 48 }
                    }}
                  >
                    {config.icon}
                  </Avatar>
                  <Typography
                    variant="h5"
                    sx={{
                      fontSize: { xs: '1.2rem', sm: '1.5rem' }
                    }}
                  >
                    {stats.stats[type as keyof typeof stats.stats] || 0}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      fontSize: { xs: '0.75rem', sm: '0.875rem' }
                    }}
                  >
                    {config.label}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Filters and Search */}
      <Box sx={{ mb: 3 }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          alignItems={{ xs: 'stretch', sm: 'center' }}
          sx={{ mb: 2 }}
        >
          <TextField
            placeholder="Search content..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            size="small"
            sx={{
              minWidth: { xs: '100%', sm: 300 }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 120 } }}>
            <InputLabel>Content Type</InputLabel>
            <Select
              value={contentTypeFilter}
              onChange={(e) => handleContentTypeFilter(e.target.value as ContentType)}
              label="Content Type"
            >
              {Object.entries(contentTypeConfig).map(([type, config]) => (
                <MenuItem key={type} value={type}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    {config.icon}
                    <span>{config.label}</span>
                  </Stack>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{
            display: 'flex',
            justifyContent: { xs: 'space-between', sm: 'flex-end' },
            width: { xs: '100%', sm: 'auto' },
            gap: 1
          }}>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>

            <Tooltip title="View Mode">
              <IconButton onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
                {viewMode === 'grid' ? <ListViewIcon /> : <GridViewIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        </Stack>

        {/* Content type tabs */}
        <Tabs
          value={contentTypeFilter}
          onChange={(_, newValue) => handleContentTypeFilter(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTabs-scrollButtons': {
              '&.Mui-disabled': { opacity: 0.3 }
            }
          }}
        >
          {Object.entries(contentTypeConfig).map(([type, config]) => (
            <Tab
              key={type}
              value={type}
              label={config.label}
              icon={config.icon}
              iconPosition="start"
              sx={{
                minHeight: { xs: 40, sm: 48 },
                fontSize: { xs: '0.8rem', sm: '0.875rem' }
              }}
            />
          ))}
        </Tabs>
      </Box>

      {/* Content */}
      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            fontSize: { xs: '0.8rem', sm: '0.875rem' }
          }}
        >
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : content.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: { xs: 4, sm: 8 } }}>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{
              fontSize: { xs: '1.1rem', sm: '1.25rem' }
            }}
          >
            No content found
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              fontSize: { xs: '0.9rem', sm: '1rem' },
              mt: 1
            }}
          >
            {searchQuery ? 'Try adjusting your search or filters' : 'Start creating content to see it here'}
          </Typography>
        </Box>
      ) : (
        <>
          {/* Content Header */}
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
            px: { xs: 0.5, sm: 0 }
          }}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                fontSize: { xs: '0.8rem', sm: '0.875rem' }
              }}
            >
              {totalItems} {totalItems === 1 ? 'item' : 'items'} found
            </Typography>
          </Box>

          {viewMode === 'grid' ? renderContentGrid() : renderContentList()}

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={(_, page) => handlePageChange(page)}
                color="primary"
                sx={{
                  '& .MuiPaginationItem-root': {
                    minWidth: { xs: 32, sm: 40 },
                    height: { xs: 32, sm: 40 },
                    fontSize: { xs: '0.8rem', sm: '0.875rem' }
                  }
                }}
              />
            </Box>
          )}
        </>
      )}

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={closePreview}
        maxWidth="lg"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            borderRadius: { xs: 0, sm: 2 },
            maxHeight: { xs: '100vh', sm: '90vh' },
            bgcolor: 'background.paper',
            backgroundImage: 'none',
            width: { xs: '100vw', sm: 'auto' },
            height: { xs: '100vh', sm: 'auto' },
            maxWidth: { xs: 'none', sm: 'lg' },
            margin: { xs: 0, sm: '32px' }
          }
        }}
      >
        {selectedItem && (
          <>
            <DialogTitle
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                pb: 2,
                pt: { xs: 2, sm: 3 },
                px: { xs: 2, sm: 3 },
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.default',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: { xs: 1, sm: 0 }
              }}
            >
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                flex: 1,
                minWidth: 0,
                width: '100%',
                mb: { xs: 1, sm: 0 }
              }}>
                <Chip
                  size="small"
                  label={selectedItem.content_type.toUpperCase()}
                  color="primary"
                  variant="filled"
                  sx={{
                    fontSize: { xs: '0.65rem', sm: '0.75rem' },
                    height: { xs: 20, sm: 24 }
                  }}
                />
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 600,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: 1,
                    fontSize: { xs: '1.1rem', sm: '1.5rem' }
                  }}
                >
                  {selectedItem.title || generateTitleFromJobType(selectedItem.job_type)}
                </Typography>
              </Box>
              <IconButton
                onClick={closePreview}
                size="large"
                sx={{
                  bgcolor: 'action.hover',
                  '&:hover': { bgcolor: 'action.selected' },
                  ml: { xs: 0, sm: 2 },
                  flexShrink: 0,
                  alignSelf: { xs: 'flex-end', sm: 'auto' }
                }}
              >
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent
              dividers
              sx={{
                p: { xs: 2, sm: 3 },
                bgcolor: 'background.paper',
                overflow: 'auto'
              }}
            >
              <Stack spacing={3}>
                {/* Content preview */}
                {selectedItem.content_type === ContentType.IMAGE && (
                  <Box sx={{ textAlign: 'center', position: 'relative' }}>
                    <img
                      src={selectedItem.file_url}
                      alt="Content"
                      style={{
                        maxWidth: '100%',
                        maxHeight: '500px',
                        objectFit: 'contain',
                        borderRadius: '8px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                    />
                    <Box
                      sx={{
                        mt: 3,
                        display: 'flex',
                        justifyContent: 'center',
                        gap: 2,
                        flexDirection: { xs: 'column', sm: 'row' }
                      }}
                    >
                      <Button
                        variant="outlined"
                        onClick={() => window.open(selectedItem.file_url, '_blank')}
                        startIcon={<GetAppIcon />}
                        sx={{
                          minWidth: { xs: '100px', sm: '140px' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          height: { xs: 32, sm: 40 }
                        }}
                      >
                        View Full Size
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => navigator.clipboard.writeText(selectedItem.file_url)}
                        startIcon={<ContentCopyIcon />}
                        sx={{
                          minWidth: { xs: '100px', sm: '140px' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          height: { xs: 32, sm: 40 }
                        }}
                      >
                        Copy URL
                      </Button>
                    </Box>
                  </Box>
                )}
                {selectedItem.content_type === ContentType.VIDEO && (
                  <Box sx={{ textAlign: 'center' }}>
                    <video
                      controls
                      style={{
                        maxWidth: '100%',
                        maxHeight: '500px',
                        borderRadius: '8px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                      preload="metadata"
                    >
                      <source src={selectedItem.file_url} type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                    <Box
                      sx={{
                        mt: 3,
                        display: 'flex',
                        justifyContent: 'center',
                        gap: 2,
                        flexDirection: { xs: 'column', sm: 'row' }
                      }}
                    >
                      <Button
                        variant="outlined"
                        onClick={() => window.open(selectedItem.file_url, '_blank')}
                        startIcon={<GetAppIcon />}
                        sx={{
                          minWidth: { xs: '100px', sm: '140px' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          height: { xs: 32, sm: 40 }
                        }}
                      >
                        Open in New Tab
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => navigator.clipboard.writeText(selectedItem.file_url)}
                        startIcon={<ContentCopyIcon />}
                        sx={{
                          minWidth: { xs: '100px', sm: '140px' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          height: { xs: 32, sm: 40 }
                        }}
                      >
                        Copy URL
                      </Button>
                    </Box>
                  </Box>
                )}
                {selectedItem.content_type === ContentType.AUDIO && (
                  <Box sx={{ textAlign: 'center' }}>
                    <Box
                      sx={{
                        p: 4,
                        bgcolor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: 2,
                        mb: 2
                      }}
                    >
                      <AudioIcon sx={{ fontSize: 64, color: 'white', mb: 2 }} />
                      <audio controls style={{ width: '100%', maxWidth: '400px' }}>
                        <source src={selectedItem.file_url} />
                        Your browser does not support the audio tag.
                      </audio>
                    </Box>
                    <Box sx={{
                      display: 'flex',
                      justifyContent: 'center',
                      gap: 1,
                      flexDirection: { xs: 'column', sm: 'row' }
                    }}>
                      <Button
                        variant="outlined"
                        onClick={() => window.open(selectedItem.file_url, '_blank')}
                        startIcon={<GetAppIcon />}
                        sx={{
                          fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                          minWidth: { xs: '100%', sm: 'auto' },
                          height: { xs: 28, sm: 32 }
                        }}
                      >
                        Open in New Tab
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={() => navigator.clipboard.writeText(selectedItem.file_url)}
                        startIcon={<ContentCopyIcon />}
                        sx={{
                          fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                          minWidth: { xs: '100%', sm: 'auto' },
                          height: { xs: 28, sm: 32 }
                        }}
                      >
                        Copy URL
                      </Button>
                    </Box>
                  </Box>
                )}
                {selectedItem.content_type === ContentType.TEXT && (
                  <Box>
                    <Box
                      sx={{
                        p: 3,
                        bgcolor: 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: 2,
                        mb: 2,
                        position: 'relative',
                        overflow: 'hidden'
                      }}
                    >
                      {/* Background pattern */}
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          opacity: 0.1,
                          background: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.3'%3E%3Cpath d='m36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
                        }}
                      />
                      <TextIcon sx={{ fontSize: 48, color: 'white', mb: 1 }} />
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'white',
                          opacity: 0.9,
                          position: 'relative',
                          zIndex: 1
                        }}
                      >
                        Text Content
                      </Typography>
                    </Box>

                    {/* Text content display */}
                    <Box
                      sx={{
                        p: 3,
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        maxHeight: '400px',
                        overflow: 'auto'
                      }}
                    >
                      {/* Display title if available */}
                      {selectedItem.title && (
                        <Typography
                          variant="h6"
                          gutterBottom
                          sx={{
                            fontWeight: 600,
                            mb: 2,
                            color: 'primary.main'
                          }}
                        >
                          {selectedItem.title}
                        </Typography>
                      )}

                      {/* Display description/text content */}
                      {(selectedItem.description || selectedItem.title) && (
                        <Typography
                          variant="body1"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            lineHeight: 1.8,
                            fontSize: '1rem',
                            color: 'text.primary'
                          }}
                        >
                          {selectedItem.description || selectedItem.title}
                        </Typography>
                      )}

                      {/* If neither title nor description, show placeholder */}
                      {!selectedItem.title && !selectedItem.description && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ fontStyle: 'italic' }}
                        >
                          No text content available
                        </Typography>
                      )}
                    </Box>

                    {/* Word count badge if available in metadata */}
                    {!!selectedItem.metadata?.word_count && (
                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                        <Chip
                          icon={<TextIcon />}
                          label={`${selectedItem.metadata.word_count as number} words`}
                          color="info"
                          variant="outlined"
                          size="small"
                        />
                      </Box>
                    )}

                    {/* Action buttons */}
                    <Box sx={{
                      display: 'flex',
                      justifyContent: 'center',
                      gap: 1,
                      flexDirection: { xs: 'column', sm: 'row' },
                      mt: 2
                    }}>
                      {selectedItem.file_url && (
                        <Button
                          variant="outlined"
                          onClick={() => window.open(selectedItem.file_url, '_blank')}
                          startIcon={<GetAppIcon />}
                          sx={{
                            fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                            minWidth: { xs: '100%', sm: 'auto' },
                            height: { xs: 28, sm: 32 }
                          }}
                        >
                          Open File
                        </Button>
                      )}
                      <Button
                        variant="outlined"
                        onClick={() => {
                          // Copy text to clipboard
                          const textToCopy = selectedItem.description || selectedItem.title || '';
                          if (textToCopy) {
                            navigator.clipboard.writeText(textToCopy);
                          }
                        }}
                        startIcon={<ContentCopyIcon />}
                        sx={{
                          fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                          minWidth: { xs: '100%', sm: 'auto' },
                          height: { xs: 28, sm: 32 }
                        }}
                      >
                        Copy Text
                      </Button>
                    </Box>
                  </Box>
                )}

                {/* Metadata */}
                <Box>
                  <Typography variant="h6" gutterBottom>Details</Typography>
                  <Stack spacing={1}>
                    <Typography><strong>Type:</strong> {getContentTypeDisplay(selectedItem.content_type).label}</Typography>
                    <Typography><strong>Created:</strong> {new Date(selectedItem.created_at).toLocaleString()}</Typography>
                    {selectedItem.file_size && (
                      <Typography><strong>File Size:</strong> {formatFileSize(selectedItem.file_size)}</Typography>
                    )}
                    {selectedItem.duration && (
                      <Typography><strong>Duration:</strong> {formatDuration(selectedItem.duration)}</Typography>
                    )}
                    {selectedItem.dimensions && (
                      <Typography><strong>Dimensions:</strong> {selectedItem.dimensions.width}×{selectedItem.dimensions.height}px</Typography>
                    )}
                    {selectedItem.description && selectedItem.content_type !== ContentType.TEXT && (
                      <Typography><strong>Description:</strong> {selectedItem.description}</Typography>
                    )}
                  </Stack>
                </Box>
              </Stack>
            </DialogContent>
            <DialogActions
              sx={{
                p: { xs: 2, sm: 3 },
                gap: 2,
                bgcolor: 'background.default',
                borderTop: 1,
                borderColor: 'divider',
                justifyContent: 'space-between',
                flexDirection: { xs: 'column', sm: 'row' },
                '& > *': {
                  width: { xs: '100%', sm: 'auto' }
                }
              }}
            >
              <Button
                onClick={closePreview}
                variant="outlined"
                sx={{
                  order: { xs: 2, sm: 1 },
                  minWidth: { xs: '100%', sm: '100px' },
                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                  height: { xs: 32, sm: 40 }
                }}
              >
                Close
              </Button>
              <Button
                startIcon={<ScheduleIcon />}
                onClick={() => handleSchedule(selectedItem)}
                variant="contained"
                color="primary"
                sx={{
                  order: { xs: 1, sm: 2 },
                  minWidth: { xs: '100%', sm: '140px' },
                  fontWeight: 600,
                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                  height: { xs: 32, sm: 40 }
                }}
              >
                Schedule Post
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={cancelDelete}
        maxWidth="sm"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            margin: { xs: 0, sm: '32px' },
            width: { xs: '100%', sm: 'auto' }
          }
        }}
      >
        <DialogTitle
          sx={{
            pb: 2,
            pt: { xs: 2, sm: 3 },
            px: { xs: 2, sm: 3 }
          }}
        >
          Delete Content
        </DialogTitle>
        <DialogContent
          sx={{
            px: { xs: 2, sm: 3 },
            pb: { xs: 2, sm: 3 }
          }}
        >
          <Typography
            sx={{
              fontSize: { xs: '0.9rem', sm: '1rem' }
            }}
          >
            Are you sure you want to delete this content item? This action cannot be undone.
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 1,
              fontSize: { xs: '0.8rem', sm: '0.875rem' }
            }}
          >
            Note: The file will remain in S3 storage, only the library entry will be removed.
          </Typography>
        </DialogContent>
        <DialogActions
          sx={{
            px: { xs: 2, sm: 3 },
            pb: { xs: 2, sm: 3 },
            pt: 2,
            gap: 1
          }}
        >
          <Button
            onClick={cancelDelete}
            variant="outlined"
            sx={{
              fontSize: { xs: '0.8rem', sm: '0.875rem' },
              minWidth: { xs: 80, sm: 64 },
              height: { xs: 32, sm: 36 }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
            sx={{
              fontSize: { xs: '0.8rem', sm: '0.875rem' },
              minWidth: { xs: 80, sm: 64 },
              height: { xs: 32, sm: 36 }
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Dialog */}
      {itemToSchedule && (
        <PostizScheduleDialog
          open={scheduleDialogOpen}
          onClose={closeScheduleDialog}
          job={{
            id: itemToSchedule.job_id,
            job_id: itemToSchedule.job_id,
            operation: itemToSchedule.job_type,
            status: JobStatus.COMPLETED,
            result: {
              scheduling: {
                suggested_content: generateSuggestedContent(itemToSchedule)
              },
              final_video_url: itemToSchedule.content_type === 'video' ? itemToSchedule.file_url : undefined,
              video_url: itemToSchedule.content_type === 'video' ? itemToSchedule.file_url : undefined,
              image_url: itemToSchedule.content_type === 'image' ? itemToSchedule.file_url : undefined,
              audio_url: itemToSchedule.content_type === 'audio' ? itemToSchedule.file_url : undefined,
              file_url: itemToSchedule.file_url
            }
          }}
          onSchedule={handleScheduleSubmit}
        />
      )}
    </Box>
  );
};

export default Library;