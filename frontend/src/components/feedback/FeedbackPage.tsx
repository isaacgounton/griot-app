import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Button,
  TextField,
  Slider,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  VolumeUp as VolumeIcon,
  Fullscreen as FullscreenIcon,
  AddComment as CommentIcon,
  Send as SendIcon,
  Timeline as TimelineIcon,
  Feedback as FeedbackIcon,
} from '@mui/icons-material';

interface FeedbackComment {
  id: string;
  timestamp: number;
  x: number;
  y: number;
  comment: string;
  author: string;
  createdAt: Date;
}

interface FeedbackPageProps {
  videoUrl?: string;
  projectTitle?: string;
  onFeedbackSubmit?: (feedbackComments: FeedbackComment[]) => void; // eslint-disable-line no-unused-vars
}

const FeedbackPage: React.FC<FeedbackPageProps> = ({
  videoUrl = '',
  projectTitle = 'Video Project',
  onFeedbackSubmit
}) => {
  // Video player state
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  
  // Feedback state
  const [comments, setComments] = useState<FeedbackComment[]>([]);
  const [isAddingComment, setIsAddingComment] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<{x: number, y: number} | null>(null);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [authorName, setAuthorName] = useState('User');

  // Load video metadata
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [videoUrl]);

  // Canvas click handler for adding comments
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isAddingComment) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    setSelectedPosition({ x, y });
    setCommentDialogOpen(true);
    setIsAddingComment(false);
  };

  // Add comment
  const handleAddComment = () => {
    if (!newComment.trim() || !selectedPosition) return;

    const comment: FeedbackComment = {
      id: Date.now().toString(),
      timestamp: currentTime,
      x: selectedPosition.x,
      y: selectedPosition.y,
      comment: newComment.trim(),
      author: authorName,
      createdAt: new Date()
    };

    setComments(prev => [...prev, comment]);
    setNewComment('');
    setCommentDialogOpen(false);
    setSelectedPosition(null);
  };

  // Delete comment
  const handleDeleteComment = (commentId: string) => {
    setComments(prev => prev.filter(c => c.id !== commentId));
  };

  // Video controls
  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
  };

  const handleSeek = (value: number) => {
    const video = videoRef.current;
    if (!video) return;
    
    video.currentTime = value;
    setCurrentTime(value);
  };

  const handleVolumeChange = (value: number) => {
    const video = videoRef.current;
    if (!video) return;
    
    video.volume = value;
    setVolume(value);
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen();
    }
  };

  // Jump to comment timestamp
  const jumpToComment = (timestamp: number) => {
    const video = videoRef.current;
    if (!video) return;
    
    video.currentTime = timestamp;
    setCurrentTime(timestamp);
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Submit all feedback
  const handleSubmitFeedback = () => {
    if (onFeedbackSubmit) {
      onFeedbackSubmit(comments);
    }
  };

  return (
    <Box sx={{ 
      p: { xs: 2, sm: 3 }, 
      maxWidth: '100%', 
      height: { xs: 'auto', lg: '100vh' }, 
      overflow: { xs: 'visible', lg: 'hidden' }
    }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 3 } }}>
        <Typography variant="h4" sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1, 
          mb: 1,
          fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
        }}>
          <FeedbackIcon color="primary" />
          Feedback Magic v2.0
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{
          fontSize: { xs: '1rem', sm: '1.25rem' }
        }}>
          {projectTitle}
        </Typography>
      </Box>

      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ 
        height: { xs: 'auto', lg: 'calc(100vh - 150px)' },
        minHeight: { xs: '600px', lg: 'auto' }
      }}>
        {/* Video Player Section */}
        <Grid item xs={12} lg={8}>
          <Paper 
            elevation={3} 
            sx={{ 
              position: 'relative', 
              height: '100%', 
              minHeight: { xs: '300px', sm: '400px' },
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {/* Video Container */}
            <Box sx={{ position: 'relative', flex: 1, backgroundColor: '#000' }}>
              {videoUrl ? (
                <>
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain'
                    }}
                    playsInline
                    controls={false}
                  />
                  <canvas
                    ref={canvasRef}
                    onClick={handleCanvasClick}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      cursor: isAddingComment ? 'crosshair' : 'default',
                      zIndex: 1
                    }}
                  />
                  
                  {/* Comment markers */}
                  {comments
                    .filter(comment => Math.abs(comment.timestamp - currentTime) < 1)
                    .map(comment => (
                      <Box
                        key={comment.id}
                        sx={{
                          position: 'absolute',
                          left: `${comment.x}%`,
                          top: `${comment.y}%`,
                          transform: 'translate(-50%, -50%)',
                          zIndex: 2
                        }}
                      >
                        <IconButton
                          size="small"
                          sx={{
                            backgroundColor: 'error.main',
                            color: 'white',
                            '&:hover': { backgroundColor: 'error.dark' }
                          }}
                        >
                          <CommentIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    ))}
                </>
              ) : (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    height: '100%',
                    color: 'text.secondary'
                  }}
                >
                  <Typography variant="h6">No video loaded</Typography>
                </Box>
              )}
            </Box>

            {/* Video Controls */}
            <Box sx={{ p: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <IconButton onClick={togglePlayPause} disabled={!videoUrl}>
                  {isPlaying ? <PauseIcon /> : <PlayIcon />}
                </IconButton>
                
                <Typography variant="body2" sx={{ minWidth: '60px' }}>
                  {formatTime(currentTime)}
                </Typography>
                
                <Slider
                  value={currentTime}
                  max={duration}
                  onChange={(_, value) => handleSeek(value as number)}
                  disabled={!videoUrl}
                  sx={{ flex: 1 }}
                />
                
                <Typography variant="body2" sx={{ minWidth: '60px' }}>
                  {formatTime(duration)}
                </Typography>
                
                <VolumeIcon />
                <Slider
                  value={volume}
                  max={1}
                  step={0.1}
                  onChange={(_, value) => handleVolumeChange(value as number)}
                  sx={{ width: 100 }}
                />
                
                <IconButton onClick={toggleFullscreen} disabled={!videoUrl}>
                  <FullscreenIcon />
                </IconButton>
              </Box>

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  variant={isAddingComment ? "contained" : "outlined"}
                  startIcon={<CommentIcon />}
                  onClick={() => setIsAddingComment(!isAddingComment)}
                  disabled={!videoUrl}
                >
                  {isAddingComment ? 'Click on video to add comment' : 'Add Comment'}
                </Button>
                
                <Chip 
                  label={`${comments.length} Comments`} 
                  color="primary"
                  variant="outlined"
                />
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Comments Panel */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon />
                  Comments ({comments.length})
                </Typography>
                
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<SendIcon />}
                  onClick={handleSubmitFeedback}
                  disabled={comments.length === 0}
                >
                  Submit Feedback
                </Button>
              </Box>

              <TextField
                label="Your Name"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                size="small"
                sx={{ mb: 2 }}
              />

              {comments.length === 0 ? (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No comments yet. Click "Add Comment" and then click on the video to leave feedback.
                </Alert>
              ) : (
                <List sx={{ flex: 1, overflow: 'auto' }}>
                  {comments
                    .sort((a, b) => a.timestamp - b.timestamp)
                    .map((comment) => (
                      <ListItem
                        key={comment.id}
                        sx={{
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1,
                          flexDirection: 'column',
                          alignItems: 'stretch'
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1 }}>
                          <Typography variant="caption" color="primary">
                            {formatTime(comment.timestamp)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            by {comment.author}
                          </Typography>
                        </Box>
                        
                        <ListItemText
                          primary={comment.comment}
                          sx={{ cursor: 'pointer' }}
                          onClick={() => jumpToComment(comment.timestamp)}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                          <Button
                            size="small"
                            onClick={() => jumpToComment(comment.timestamp)}
                          >
                            Jump to
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            onClick={() => handleDeleteComment(comment.id)}
                          >
                            Delete
                          </Button>
                        </Box>
                      </ListItem>
                    ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Comment at {formatTime(currentTime)}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            multiline
            rows={3}
            fullWidth
            label="Your comment"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Enter your feedback here..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddComment} variant="contained" disabled={!newComment.trim()}>
            Add Comment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for quick comment */}
      {videoUrl && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => setIsAddingComment(!isAddingComment)}
        >
          <CommentIcon />
        </Fab>
      )}
    </Box>
  );
};

export default FeedbackPage;