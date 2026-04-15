import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  CircularProgress,
  Alert,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  VideoLibrary as VideoIcon,
  Feedback as FeedbackIcon,
} from '@mui/icons-material';

import FeedbackPage from './FeedbackPage';

interface FeedbackProject {
  id: string;
  title: string;
  videoUrl: string;
  createdAt: Date;
  commentsCount: number;
}

interface FeedbackComment {
  id: string;
  timestamp: number;
  x: number;
  y: number;
  comment: string;
  author: string;
  createdAt: Date;
}

const FeedbackManager: React.FC = () => {
  const [projects, setProjects] = useState<FeedbackProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<FeedbackProject | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Create project dialog
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectVideoUrl, setNewProjectVideoUrl] = useState('');

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      // For now, use mock data since the API doesn't have project management
      // In a real implementation, you'd call the API here
      const mockProjects: FeedbackProject[] = [
        {
          id: '1',
          title: 'Marketing Video Draft',
          videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
          createdAt: new Date('2024-01-15'),
          commentsCount: 3
        },
        {
          id: '2',
          title: 'Product Demo V2',
          videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4',
          createdAt: new Date('2024-01-18'),
          commentsCount: 7
        }
      ];
      
      setProjects(mockProjects);
    } catch (err) {
      setError('Failed to load projects');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    if (!newProjectTitle.trim() || !newProjectVideoUrl.trim()) return;

    try {
      const newProject: FeedbackProject = {
        id: Date.now().toString(),
        title: newProjectTitle.trim(),
        videoUrl: newProjectVideoUrl.trim(),
        createdAt: new Date(),
        commentsCount: 0
      };

      setProjects(prev => [...prev, newProject]);
      setNewProjectTitle('');
      setNewProjectVideoUrl('');
      setCreateDialogOpen(false);
    } catch (err) {
      setError('Failed to create project');
      console.error('Error creating project:', err);
    }
  };

  const deleteProject = async (projectId: string) => {
    try {
      setProjects(prev => prev.filter(p => p.id !== projectId));
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
      }
    } catch (err) {
      setError('Failed to delete project');
      console.error('Error deleting project:', err);
    }
  };

  const handleFeedbackSubmit = async (comments: FeedbackComment[]) => {
    if (!selectedProject) return;

    try {
      // In a real implementation, you'd save the comments to the API
      // Log feedback submission for debugging
      // console.log('Submitting feedback for project:', selectedProject.id, comments);
      
      // Update project comment count
      setProjects(prev => 
        prev.map(p => 
          p.id === selectedProject.id 
            ? { ...p, commentsCount: comments.length }
            : p
        )
      );

      alert(`Feedback submitted successfully! ${comments.length} comments saved.`);
    } catch (err) {
      setError('Failed to submit feedback');
      console.error('Error submitting feedback:', err);
    }
  };

  // If a project is selected, show the feedback page
  if (selectedProject) {
    return (
      <Box>
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', backgroundColor: 'background.paper' }}>
          <Button
            onClick={() => setSelectedProject(null)}
            sx={{ mb: 1 }}
          >
            ← Back to Projects
          </Button>
        </Box>
        <FeedbackPage
          videoUrl={selectedProject.videoUrl}
          projectTitle={selectedProject.title}
          onFeedbackSubmit={handleFeedbackSubmit}
        />
      </Box>
    );
  }

  return (
    <Box sx={{ 
      p: { xs: 2, sm: 3 },
      pb: { xs: 4, sm: 6 }
    }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', sm: 'center' },
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 2, sm: 0 },
        mb: { xs: 3, sm: 4 }
      }}>
        <Box>
          <Typography variant="h4" sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1, 
            mb: 1,
            fontSize: { xs: '1.75rem', sm: '2rem', md: '2.125rem' }
          }}>
            <FeedbackIcon color="primary" />
            Feedback Manager
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{
            fontSize: { xs: '1rem', sm: '1.1rem' },
            lineHeight: 1.5
          }}>
            Manage video feedback projects and collaborate with your team
          </Typography>
        </Box>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          size="large"
          fullWidth
          sx={{
            maxWidth: { xs: 'none', sm: 'auto' },
            minWidth: { sm: '160px' }
          }}
        >
          New Project
        </Button>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Projects Grid */}
      {!loading && projects.length === 0 && (
        <Card sx={{ textAlign: 'center', py: 6 }}>
          <CardContent>
            <VideoIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No feedback projects yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create your first feedback project to start collecting video feedback from your team.
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Create First Project
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && projects.length > 0 && (
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} lg={4} key={project.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4
                  }
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" sx={{ flex: 1, pr: 1 }}>
                      {project.title}
                    </Typography>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteProject(project.id);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Created: {project.createdAt.toLocaleDateString()}
                  </Typography>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Chip
                      label={`${project.commentsCount} comments`}
                      size="small"
                      color={project.commentsCount > 0 ? "primary" : "default"}
                    />
                  </Box>

                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<PlayIcon />}
                    onClick={() => setSelectedProject(project)}
                  >
                    Open Feedback Session
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            mx: { xs: 2, sm: 3 },
            width: { xs: 'calc(100% - 32px)', sm: 'auto' }
          }
        }}
      >
        <DialogTitle>Create New Feedback Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Project Title"
            value={newProjectTitle}
            onChange={(e) => setNewProjectTitle(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
            placeholder="e.g., Marketing Video Draft v1"
          />
          
          <TextField
            fullWidth
            label="Video URL"
            value={newProjectVideoUrl}
            onChange={(e) => setNewProjectVideoUrl(e.target.value)}
            placeholder="https://..."
            helperText="Paste the URL of the video you want to collect feedback on"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={createProject}
            variant="contained"
            disabled={!newProjectTitle.trim() || !newProjectVideoUrl.trim()}
          >
            Create Project
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FeedbackManager;