import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Box,
    Typography,
    List,
    ListItem,
    Card,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Alert,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    LinearProgress,
    Stack,
    Divider
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    Pause as PauseIcon,
    Download as DownloadIcon,
    MusicNote as MusicIcon,
    CloudUpload as UploadIcon,
    Search as SearchIcon,
    FilterList as FilterIcon
} from '@mui/icons-material';
import { apiClient } from '../../utils/api';

// Music track interface
interface MusicTrack {
    file: string;
    title: string;
    mood: string;
    duration: number;
    start: number;
    end: number;
    url: string;
}

// Paginated response interface
interface TracksResponse {
    success: boolean;
    tracks: MusicTrack[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    moods: string[];
}

interface MusicTracksPanelProps {
    onTrackSelect?: (track: MusicTrack) => void;
    selectedTrackFile?: string;
}

export const MusicTracksPanel: React.FC<MusicTracksPanelProps> = ({
    onTrackSelect,
    selectedTrackFile
}) => {
    // State for tracks and pagination
    const [musicTracks, setMusicTracks] = useState<MusicTrack[]>([]);
    const [musicMoods, setMusicMoods] = useState<string[]>([]);
    const [selectedMood, setSelectedMood] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');

    // Pagination state
    const [page, setPage] = useState(1);
    const [perPage] = useState(12);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);

    // Playback state
    const [playingTrack, setPlayingTrack] = useState<string | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Upload dialog state
    const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadTitle, setUploadTitle] = useState('');
    const [uploadMood, setUploadMood] = useState('');
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState('');

    // Ref for infinite scroll observer
    const observerTarget = useRef<HTMLDivElement>(null);

    // Debounce search term
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchTerm);
            setPage(1); // Reset to first page on search
        }, 500);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    // Fetch tracks with pagination
    const fetchTracks = useCallback(async (pageNum: number, reset: boolean = false) => {
        if (loading) return;
        setLoading(true);

        try {
            const params = new URLSearchParams({
                page: pageNum.toString(),
                per_page: perPage.toString()
            });

            if (selectedMood) params.append('mood', selectedMood);
            if (debouncedSearch) params.append('search', debouncedSearch);

            const response = await apiClient.get<TracksResponse>(`/music/tracks?${params}`);

            if (response.data?.success) {
                const { tracks, total_pages, total: totalCount } = response.data;

                if (reset || pageNum === 1) {
                    setMusicTracks(tracks);
                } else {
                    setMusicTracks(prev => [...prev, ...tracks]);
                }

                setTotalPages(total_pages);
                setTotal(totalCount);
                setHasMore(pageNum < total_pages);
            }
        } catch (error) {
            console.error('Failed to fetch tracks:', error);
        } finally {
            setLoading(false);
        }
    }, [loading, perPage, selectedMood, debouncedSearch]);

    // Fetch moods once on mount
    useEffect(() => {
        const fetchMoods = async () => {
            try {
                const response = await apiClient.get('/music/moods');
                if (response.data?.success) {
                    setMusicMoods(response.data.moods || []);
                }
            } catch (error) {
                console.error('Failed to fetch moods:', error);
            }
        };
        fetchMoods();
    }, []);

    // Initial fetch and fetch on filter changes
    useEffect(() => {
        fetchTracks(1, true);
    }, [selectedMood, debouncedSearch]);

    // Infinite scroll observer
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && hasMore && !loading) {
                    const nextPage = page + 1;
                    setPage(nextPage);
                    fetchTracks(nextPage, false);
                }
            },
            { threshold: 0.1 }
        );

        const currentTarget = observerTarget.current;
        if (currentTarget) {
            observer.observe(currentTarget);
        }

        return () => {
            if (currentTarget) {
                observer.unobserve(currentTarget);
            }
        };
    }, [hasMore, loading, page, fetchTracks]);

    // Handle mood change
    const handleMoodChange = (mood: string) => {
        setSelectedMood(mood);
    };

    // Handle track playback
    const handlePlayPause = (trackFile: string, trackUrl: string) => {
        if (playingTrack === trackFile) {
            // Pause current
            if (audioRef.current) {
                audioRef.current.pause();
            }
            setPlayingTrack(null);
        } else {
            // Play new track
            if (audioRef.current) {
                audioRef.current.src = trackUrl;
                audioRef.current.play();
            }
            setPlayingTrack(trackFile);
        }
    };

    // Handle track selection
    const handleTrackClick = (track: MusicTrack) => {
        if (onTrackSelect) {
            onTrackSelect(track);
        }
    };

    // Handle file upload
    const handleUpload = async () => {
        if (!uploadFile || !uploadTitle || !uploadMood) {
            setUploadError('Please fill in all required fields');
            return;
        }

        setUploading(true);
        setUploadError('');

        try {
            const formData = new FormData();
            formData.append('file', uploadFile);
            formData.append('title', uploadTitle);
            formData.append('mood', uploadMood);

            const response = await apiClient.post('/music/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.data?.success) {
                // Refresh tracks
                fetchTracks(1, true);
                setUploadDialogOpen(false);
                setUploadFile(null);
                setUploadTitle('');
                setUploadMood('');
            }
        } catch (error: any) {
            setUploadError(error.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    // Format duration
    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <Box>
            {/* Hidden audio element */}
            <audio ref={audioRef} onEnded={() => setPlayingTrack(null)} />

            {/* Header with Upload Button */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        Music Library
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {total} tracks • {totalPages} pages
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    size="small"
                    startIcon={<UploadIcon />}
                    onClick={() => setUploadDialogOpen(true)}
                >
                    Add Track
                </Button>
            </Box>

            {/* Compact Filters */}
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                <TextField
                    placeholder="Search..."
                    size="small"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                        startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary', fontSize: 18 }} />
                    }}
                    sx={{ flexGrow: 1, maxWidth: 200 }}
                />
                <FormControl size="small" sx={{ minWidth: 140 }}>
                    <Select
                        value={selectedMood}
                        onChange={(e) => handleMoodChange(e.target.value)}
                        displayEmpty
                        startAdornment={<FilterIcon sx={{ mr: 1, color: 'text.secondary', fontSize: 18 }} />}
                    >
                        <MenuItem value="">All Moods</MenuItem>
                        {musicMoods.map((mood) => (
                            <MenuItem key={mood} value={mood}>
                                {mood.charAt(0).toUpperCase() + mood.slice(1)}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Stack>

            {/* Compact List View */}
            <Card variant="outlined" sx={{ maxHeight: 500, overflow: 'auto' }}>
                <List disablePadding>
                    {musicTracks.map((track, index) => (
                        <React.Fragment key={track.file}>
                            <ListItem
                                disablePadding
                                secondaryAction={
                                    <Stack direction="row" spacing={0.5}>
                                        <IconButton
                                            size="small"
                                            onClick={() => handlePlayPause(track.file, track.url)}
                                            color={playingTrack === track.file ? 'primary' : 'default'}
                                        >
                                            {playingTrack === track.file ? <PauseIcon /> : <PlayIcon />}
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            href={track.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            <DownloadIcon fontSize="small" />
                                        </IconButton>
                                    </Stack>
                                }
                                sx={{
                                    px: 2,
                                    py: 1.5,
                                    cursor: 'pointer',
                                    bgcolor: selectedTrackFile === track.file ? 'action.selected' : 'transparent',
                                    '&:hover': { bgcolor: 'action.hover' }
                                }}
                                onClick={() => handleTrackClick(track)}
                            >
                                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.25 }}>
                                        <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                                            {track.title}
                                        </Typography>
                                        <Chip
                                            label={track.mood}
                                            size="small"
                                            variant="outlined"
                                            sx={{ height: 18, fontSize: '0.65rem', '& .MuiChip-label': { px: 0.5 } }}
                                        />
                                    </Stack>
                                    <Stack direction="row" spacing={2} alignItems="center">
                                        <Typography variant="caption" color="text.secondary">
                                            {formatDuration(track.duration)}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                            {track.start}s - {track.end}s
                                        </Typography>
                                    </Stack>
                                </Box>
                            </ListItem>
                            {index < musicTracks.length - 1 && <Divider />}
                        </React.Fragment>
                    ))}
                </List>

                {/* Loading indicator for infinite scroll */}
                {loading && musicTracks.length > 0 && (
                    <Box sx={{ p: 2 }}>
                        <LinearProgress />
                    </Box>
                )}

                {/* Observer target for infinite scroll */}
                <div ref={observerTarget} style={{ height: 10 }} />

                {/* Initial loading state */}
                {loading && musicTracks.length === 0 && (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                        <LinearProgress sx={{ maxWidth: 200, mx: 'auto' }} />
                    </Box>
                )}

                {/* Empty state */}
                {!loading && musicTracks.length === 0 && (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                        <MusicIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                            No tracks found
                        </Typography>
                    </Box>
                )}
            </Card>

            {/* Upload Dialog */}
            <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Add New Music Track</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        {/* File Upload */}
                        <Button
                            variant="outlined"
                            component="label"
                            fullWidth
                            startIcon={<UploadIcon />}
                        >
                            {uploadFile?.name || 'Select MP3 File'}
                            <input
                                type="file"
                                accept=".mp3,audio/mpeg"
                                hidden
                                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                            />
                        </Button>

                        {/* Title */}
                        <TextField
                            fullWidth
                            label="Title"
                            value={uploadTitle}
                            onChange={(e) => setUploadTitle(e.target.value)}
                            size="small"
                        />

                        {/* Mood */}
                        <FormControl fullWidth size="small">
                            <InputLabel>Mood</InputLabel>
                            <Select
                                value={uploadMood}
                                label="Mood"
                                onChange={(e) => setUploadMood(e.target.value)}
                            >
                                {musicMoods.map((mood) => (
                                    <MenuItem key={mood} value={mood}>
                                        {mood.charAt(0).toUpperCase() + mood.slice(1)}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        {/* Error Message */}
                        {uploadError && (
                            <Alert severity="error">{uploadError}</Alert>
                        )}
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleUpload}
                        variant="contained"
                        disabled={uploading || !uploadFile || !uploadTitle || !uploadMood}
                    >
                        {uploading ? 'Uploading...' : 'Upload'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default MusicTracksPanel;
