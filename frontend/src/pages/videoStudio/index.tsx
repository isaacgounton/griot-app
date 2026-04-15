import { useState, useEffect } from 'react';
import {
  Box, Typography, Button, IconButton, TextField, Chip, Stack, Grid,
  CircularProgress, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, Tooltip, Snackbar, Paper, Skeleton, Card, CardContent,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SettingsIcon from '@mui/icons-material/Settings';
import MovieIcon from '@mui/icons-material/Movie';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ImageIcon from '@mui/icons-material/Image';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studioApi } from './api';
import { useStudioProject } from './hooks/useStudioProject';
import Timeline from './components/Timeline';
import SceneEditor from './components/SceneEditor';
import ProjectSettingsDialog from './components/ProjectSettings';
import ExportDialog from './components/ExportDialog';
import type { ProjectListItem } from './types';
import { QuickCreateView, SceneBuilderView } from './views';
import BoltIcon from '@mui/icons-material/Bolt';
import ScienceIcon from '@mui/icons-material/Science';
import EditNoteIcon from '@mui/icons-material/EditNote';

// ── Project List View ─────────────────────────────────────────────────
function ProjectList({ onSelect, onQuickCreate, onSceneBuilder }: {
  onSelect: (id: string) => void;
  onQuickCreate: () => void;
  onSceneBuilder: () => void;
}) {
  const queryClient = useQueryClient();

  const { data: projects, isLoading } = useQuery({
    queryKey: ['studio-projects'],
    queryFn: studioApi.listProjects,
  });

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');

  const createMutation = useMutation({
    mutationFn: (name: string) => studioApi.createProject({ name }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['studio-projects'] });
      setCreateOpen(false);
      setNewName('');
      onSelect(project.id);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => studioApi.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio-projects'] });
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Stack spacing={2}>
          {[1, 2, 3].map(i => <Skeleton key={i} variant="rectangular" height={100} sx={{ borderRadius: 2 }} />)}
        </Stack>
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 3, sm: 4 } }}>
        <Typography
          variant="h4"
          sx={{ fontWeight: 700, mb: 0.5, fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}
        >
          Video Studio
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
          Create and manage your video projects
        </Typography>
      </Box>

      {/* Workflow cards */}
      <Grid container spacing={{ xs: 1.5, sm: 2 }} sx={{ mb: { xs: 3, sm: 4 } }}>
        {([
          { label: 'Quick Create', desc: 'Topic to video in one click', icon: <BoltIcon />, color: 'warning.main', onClick: onQuickCreate },
          { label: 'AI Scene Builder', desc: 'Research, generate scenes, create', icon: <ScienceIcon />, color: 'info.main', onClick: onSceneBuilder },
          { label: 'New Project', desc: 'Timeline editor with full control', icon: <EditNoteIcon />, color: 'success.main', onClick: () => setCreateOpen(true) },
        ] as const).map((card) => (
          <Grid item xs={12} sm={4} key={card.label}>
            <Card
              elevation={0}
              onClick={card.onClick}
              sx={{
                cursor: 'pointer', textAlign: 'center', height: '100%',
                border: '1px solid', borderColor: 'divider',
                transition: 'all 0.3s ease',
                '&:hover': { transform: 'translateY(-4px)', boxShadow: 3, borderColor: 'primary.main' },
              }}
            >
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{
                  width: 56, height: 56, borderRadius: '16px',
                  bgcolor: 'action.hover', color: card.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  mx: 'auto', mb: 2, fontSize: 28,
                }}>
                  {card.icon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, fontSize: '1rem' }}>{card.label}</Typography>
                <Typography variant="body2" color="text.secondary">{card.desc}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Projects section */}
      <Paper elevation={0} sx={{ p: { xs: 2, sm: 3 }, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <MovieIcon sx={{ color: 'primary.main' }} />
          Your Projects
        </Typography>

        {(!projects || projects.length === 0) ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <MovieIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>No projects yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create your first video project to get started.
            </Typography>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
              Create Project
            </Button>
          </Box>
        ) : (
          <Stack spacing={1.5}>
            {projects.map((p: ProjectListItem) => (
              <Paper
                key={p.id}
                elevation={0}
                sx={{
                  p: 2, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 2,
                  border: '1px solid', borderColor: 'divider', borderRadius: 2,
                  transition: 'all 0.2s ease',
                  '&:hover': { bgcolor: 'action.hover', transform: 'translateY(-1px)', boxShadow: 1 },
                }}
                onClick={() => onSelect(p.id)}
              >
                {p.thumbnail_url ? (
                  <Box component="img" src={p.thumbnail_url} sx={{ width: 80, height: 50, objectFit: 'cover', borderRadius: 1 }} />
                ) : (
                  <Box sx={{ width: 80, height: 50, bgcolor: 'grey.800', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <MovieIcon sx={{ color: 'grey.600' }} />
                  </Box>
                )}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle1" fontWeight={500} noWrap>{p.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {p.scene_count} scene{p.scene_count !== 1 ? 's' : ''} &middot;{' '}
                    {p.total_duration > 0 ? `${Math.round(p.total_duration)}s` : 'Empty'} &middot;{' '}
                    {new Date(p.updated_at).toLocaleDateString()}
                  </Typography>
                </Box>
                <Chip
                  label={p.status}
                  size="small"
                  color={p.status === 'completed' ? 'success' : p.status === 'failed' ? 'error' : 'default'}
                  variant="outlined"
                />
                <IconButton
                  size="small"
                  color="error"
                  onClick={e => { e.stopPropagation(); deleteMutation.mutate(p.id); }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Paper>
            ))}
          </Stack>
        )}
      </Paper>

      {/* Create dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Project Name"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            sx={{ mt: 1 }}
            onKeyDown={e => { if (e.key === 'Enter' && newName.trim()) createMutation.mutate(newName.trim()); }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createMutation.mutate(newName.trim())}
            disabled={!newName.trim() || createMutation.isPending}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ── AI Scene Generator Dialog ─────────────────────────────────────────
function AISceneDialog({
  open, onClose, onGenerate, isProcessing,
}: {
  open: boolean;
  onClose: () => void;
  onGenerate: (data: { topic?: string; script?: string; scene_count?: number }) => void;
  isProcessing: boolean;
}) {
  const [topic, setTopic] = useState('');
  const [script, setScript] = useState('');
  const [sceneCount, setSceneCount] = useState(5);
  const [mode, setMode] = useState<'topic' | 'script'>('topic');

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Generate Scenes with AI</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant={mode === 'topic' ? 'contained' : 'outlined'} size="small" onClick={() => setMode('topic')}>
              From Topic
            </Button>
            <Button variant={mode === 'script' ? 'contained' : 'outlined'} size="small" onClick={() => setMode('script')}>
              From Script
            </Button>
          </Box>

          {mode === 'topic' ? (
            <TextField
              label="Topic"
              fullWidth
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="e.g. Benefits of meditation for productivity"
            />
          ) : (
            <TextField
              label="Full Script"
              fullWidth
              multiline
              rows={6}
              value={script}
              onChange={e => setScript(e.target.value)}
              placeholder="Paste your full video script here. It will be split into scenes automatically."
            />
          )}

          <TextField
            label="Number of Scenes"
            type="number"
            value={sceneCount}
            onChange={e => setSceneCount(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
            inputProps={{ min: 1, max: 20 }}
            size="small"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          startIcon={isProcessing ? <CircularProgress size={16} /> : <AutoFixHighIcon />}
          disabled={isProcessing || (mode === 'topic' ? !topic.trim() : !script.trim())}
          onClick={() => onGenerate({
            topic: mode === 'topic' ? topic.trim() : undefined,
            script: mode === 'script' ? script.trim() : undefined,
            scene_count: sceneCount,
          })}
        >
          Generate
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ── Project Editor View ───────────────────────────────────────────────
function ProjectEditor({ projectId, onBack }: { projectId: string; onBack: () => void }) {
  const {
    project, isLoading, error,
    selectedScene, selectedSceneId, setSelectedSceneId,
    addScene, updateScene, deleteScene,
    generateTTS, generateMedia, generateAIScenes, exportVideo, uploadMedia, updateSettings,
    activeJobType, jobStatus, isProcessing,
  } = useStudioProject(projectId);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [aiScenesOpen, setAiScenesOpen] = useState(false);
  const [snackMsg, setSnackMsg] = useState<string | null>(null);

  // Show feedback when jobs complete or fail
  useEffect(() => {
    if (!jobStatus) return;
    if (jobStatus.status === 'completed') {
      const messages: Record<string, string> = {
        tts: 'Voice generation completed',
        media: 'Media sourced successfully',
        ai_scenes: 'AI scenes generated',
        export: 'Video exported',
      };
      setSnackMsg(messages[activeJobType || ''] || 'Job completed');
    } else if (jobStatus.status === 'failed') {
      setSnackMsg(`Failed: ${jobStatus.error || 'Unknown error'}`);
    }
  }, [jobStatus?.status]);

  // Auto-select first scene
  useEffect(() => {
    if (project && project.scenes.length > 0 && !selectedSceneId) {
      setSelectedSceneId(project.scenes[0].id);
    }
  }, [project, selectedSceneId, setSelectedSceneId]);

  if (isLoading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" action={<Button onClick={onBack}>Go Back</Button>}>
          Failed to load project: {(error as Error)?.message || 'Not found'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <Box sx={{
        px: 2, py: 1, display: 'flex', alignItems: 'center', gap: 1,
        borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper',
      }}>
        <IconButton size="small" onClick={onBack}><ArrowBackIcon /></IconButton>
        <Typography variant="h6" sx={{ flex: 1, fontSize: '1rem' }} noWrap>{project.name}</Typography>

        <Chip
          label={project.status}
          size="small"
          color={project.status === 'completed' ? 'success' : project.status === 'failed' ? 'error' : 'default'}
          variant="outlined"
        />

        {isProcessing && activeJobType && (
          <Chip
            icon={<CircularProgress size={12} />}
            label={activeJobType === 'tts' ? 'Generating voice...' : activeJobType === 'media' ? 'Sourcing media...' : activeJobType === 'export' ? 'Exporting...' : activeJobType === 'ai_scenes' ? 'AI generating...' : 'Processing...'}
            size="small"
            color="primary"
          />
        )}

        <Tooltip title="Generate All Voice"><span>
          <IconButton
            size="small"
            onClick={() => { generateTTS(); setSnackMsg('TTS generation started'); }}
            disabled={isProcessing || project.scenes.length === 0}
          >
            <RecordVoiceOverIcon fontSize="small" />
          </IconButton>
        </span></Tooltip>

        <Tooltip title="Source All Media"><span>
          <IconButton
            size="small"
            onClick={() => { generateMedia(); setSnackMsg('Media generation started'); }}
            disabled={isProcessing || project.scenes.length === 0}
          >
            <ImageIcon fontSize="small" />
          </IconButton>
        </span></Tooltip>

        <Tooltip title="AI Generate Scenes">
          <IconButton size="small" onClick={() => setAiScenesOpen(true)} disabled={isProcessing}>
            <AutoFixHighIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        <Tooltip title="Settings">
          <IconButton size="small" onClick={() => setSettingsOpen(true)}>
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        <Button
          variant="contained"
          size="small"
          startIcon={<FileDownloadIcon />}
          onClick={() => setExportOpen(true)}
          disabled={isProcessing || project.scenes.length === 0}
        >
          Export
        </Button>
      </Box>

      {/* ── Main workspace ─────────────────────────────────────────────── */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Timeline + Preview area */}
        <Box sx={{ flex: 3, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', minWidth: 0 }}>
          {/* Preview area */}
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.900', minHeight: 200, overflow: 'hidden' }}>
            {selectedScene?.media_url ? (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', p: 1 }}>
                {selectedScene.media_url.match(/\.(mp4|webm|mov)/) || selectedScene.media_source_type?.includes('video') ? (
                  <video
                    key={selectedScene.media_url}
                    src={selectedScene.media_url}
                    controls
                    style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: 8 }}
                  />
                ) : (
                  <Box
                    component="img"
                    src={selectedScene.media_url}
                    sx={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: 1 }}
                  />
                )}
              </Box>
            ) : selectedScene ? (
              <Stack alignItems="center" spacing={1}>
                <MovieIcon sx={{ fontSize: 48, color: 'grey.700' }} />
                <Typography color="grey.600" variant="body2">No media for this scene</Typography>
                <Typography color="grey.700" variant="caption">
                  Use the Media tab in the editor to add footage
                </Typography>
              </Stack>
            ) : (
              <Stack alignItems="center" spacing={1}>
                <MovieIcon sx={{ fontSize: 48, color: 'grey.700' }} />
                <Typography color="grey.600" variant="body2">Select a scene to preview</Typography>
              </Stack>
            )}
          </Box>

          {/* Timeline */}
          <Box sx={{ borderTop: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
            <Timeline
              scenes={project.scenes}
              selectedSceneId={selectedSceneId}
              onSelectScene={setSelectedSceneId}
              onAddScene={() => addScene({ script_text: '', after_index: project.scenes.length })}
              totalDuration={project.total_duration}
            />
          </Box>
        </Box>

        {/* Right: Scene Editor */}
        <Box sx={{ flex: 2, minWidth: 280, maxWidth: 450, overflow: 'hidden' }}>
          {selectedScene ? (
            <SceneEditor
              scene={selectedScene}
              projectId={project.id}
              onUpdate={data => updateScene({ sceneId: selectedScene.id, data })}
              onDelete={() => {
                deleteScene(selectedScene.id);
                setSelectedSceneId(null);
              }}
              onGenerateTTS={() => {
                generateTTS([selectedScene.id]);
                setSnackMsg('Generating voice for scene...');
              }}
              onGenerateMedia={() => {
                generateMedia([selectedScene.id]);
                setSnackMsg('Sourcing media for scene...');
              }}
              onUploadMedia={file => uploadMedia(selectedScene.id, file)}
              isProcessing={isProcessing}
              projectMediaType={project.settings.media_type}
              footageProvider={project.settings.footage_provider}
              otherScenesText={project.scenes.filter(s => s.id !== selectedScene.id).map(s => s.script_text)}
            />
          ) : (
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 3 }}>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                {project.scenes.length === 0 ? 'No scenes yet' : 'Select a scene to edit'}
              </Typography>
              {project.scenes.length === 0 && (
                <Stack spacing={1} sx={{ mt: 2, width: '100%' }}>
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    fullWidth
                    onClick={() => addScene({ script_text: '' })}
                  >
                    Add Empty Scene
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<AutoFixHighIcon />}
                    fullWidth
                    onClick={() => setAiScenesOpen(true)}
                  >
                    Generate with AI
                  </Button>
                </Stack>
              )}
            </Box>
          )}
        </Box>
      </Box>

      {/* ── Dialogs ────────────────────────────────────────────────────── */}
      <ProjectSettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={project.settings}
        onSave={updateSettings}
      />

      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        onExport={exportVideo}
        jobStatus={activeJobType === 'export' ? jobStatus : null}
        isProcessing={isProcessing && activeJobType === 'export'}
        finalVideoUrl={project.final_video_url}
      />

      <AISceneDialog
        open={aiScenesOpen}
        onClose={() => setAiScenesOpen(false)}
        onGenerate={data => {
          generateAIScenes(data);
          setAiScenesOpen(false);
          setSnackMsg('AI scene generation started');
        }}
        isProcessing={isProcessing && activeJobType === 'ai_scenes'}
      />

      <Snackbar
        open={!!snackMsg}
        autoHideDuration={3000}
        onClose={() => setSnackMsg(null)}
        message={snackMsg}
      />
    </Box>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────
export default function VideoStudio() {
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'home' | 'quick-create' | 'scene-builder'>('home');

  if (activeView === 'quick-create') {
    return <QuickCreateView onBack={() => setActiveView('home')} />;
  }

  if (activeView === 'scene-builder') {
    return <SceneBuilderView onBack={() => setActiveView('home')} />;
  }

  if (activeProjectId) {
    return <ProjectEditor projectId={activeProjectId} onBack={() => setActiveProjectId(null)} />;
  }

  return (
    <ProjectList
      onSelect={setActiveProjectId}
      onQuickCreate={() => setActiveView('quick-create')}
      onSceneBuilder={() => setActiveView('scene-builder')}
    />
  );
}
