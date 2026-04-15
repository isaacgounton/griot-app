import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, TextField, Button, IconButton, Tabs, Tab,
  Select, MenuItem, FormControl, InputLabel, Chip, Stack,
  CircularProgress, Dialog, DialogTitle, DialogContent, ImageList,
  ImageListItem, ImageListItemBar,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ImageIcon from '@mui/icons-material/Image';
import SearchIcon from '@mui/icons-material/Search';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { StudioScene } from '../types';
import { SCENE_STATUS_LABELS, SCENE_STATUS_COLORS } from '../types';
import { pollinationsApi } from '../../../utils/api';
import { studioApi } from '../api';

interface MediaResult {
  id: string | number;
  url: string;
  thumbnail: string;
  download_url: string;
  duration?: number;
  photographer?: string;
  provider: string;
  type: string;
}

interface SceneEditorProps {
  scene: StudioScene;
  projectId: string;
  onUpdate: (data: Partial<StudioScene>) => void;
  onDelete: () => void;
  onGenerateTTS: () => void;
  onGenerateMedia: () => void;
  onUploadMedia: (file: File) => void;
  isProcessing: boolean;
  projectMediaType?: string;
  footageProvider?: string;
  otherScenesText?: string[];
}

export default function SceneEditor({
  scene, projectId, onUpdate, onDelete, onGenerateTTS, onGenerateMedia, onUploadMedia, isProcessing,
  projectMediaType, footageProvider: _footageProvider, otherScenesText,
}: SceneEditorProps) {
  const [scriptText, setScriptText] = useState(scene.script_text);
  const [searchTerms, setSearchTerms] = useState(scene.media_search_terms?.join(', ') || '');
  const [mediaPrompt, setMediaPrompt] = useState(scene.media_prompt || '');
  const [tab, setTab] = useState(0);
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Media picker state
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerResults, setPickerResults] = useState<MediaResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setScriptText(scene.script_text);
    setSearchTerms(scene.media_search_terms?.join(', ') || '');
    setMediaPrompt(scene.media_prompt || '');
  }, [scene.id]);

  const debouncedUpdate = (field: string, value: unknown) => {
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      onUpdate({ [field]: value } as Partial<StudioScene>);
    }, 800);
  };

  const handleScriptChange = (text: string) => {
    setScriptText(text);
    debouncedUpdate('script_text', text);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUploadMedia(file);
  };

  const isStockMedia = !scene.media_source_type?.startsWith('ai') && scene.media_source_type !== 'user_upload';

  const handleSearchMedia = async () => {
    if (!isStockMedia) {
      // AI media — use existing async job flow
      onGenerateMedia();
      return;
    }
    setIsSearching(true);
    setPickerOpen(true);
    setPickerResults([]);
    try {
      const data = await studioApi.searchMedia(projectId, scene.id);
      setPickerResults(data.results);
      setSearchQuery(data.query);
    } catch (err) {
      console.error('Media search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectMedia = (result: MediaResult) => {
    onUpdate({
      media_url: result.download_url || result.url,
      media_provider: result.provider,
    });
    setPickerOpen(false);
  };

  const wordCount = scriptText.trim().split(/\s+/).filter(Boolean).length;
  const estDuration = Math.max(2, Math.round(wordCount / 2.5 * 10) / 10);
  const statusColor = SCENE_STATUS_COLORS[scene.status] || '#9e9e9e';

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2">Scene {scene.order_index + 1}</Typography>
          <Chip
            label={SCENE_STATUS_LABELS[scene.status]}
            size="small"
            sx={{ bgcolor: statusColor, color: '#fff', fontSize: '0.7rem', height: 20 }}
          />
        </Box>
        <IconButton size="small" color="error" onClick={onDelete}>
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 2, minHeight: 36 }}>
        <Tab label="Script" icon={<RecordVoiceOverIcon />} iconPosition="start" sx={{ minHeight: 36, fontSize: '0.75rem' }} />
        <Tab label="Media" icon={<ImageIcon />} iconPosition="start" sx={{ minHeight: 36, fontSize: '0.75rem' }} />
      </Tabs>

      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {/* Script Tab */}
        {tab === 0 && (
          <Stack spacing={2}>
            <TextField
              label="Narration Script"
              multiline
              rows={6}
              fullWidth
              value={scriptText}
              onChange={e => handleScriptChange(e.target.value)}
              placeholder="Type your script or enter a topic for AI to write..."
              size="small"
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {wordCount} words &middot; Est. {estDuration}s
              </Typography>
              {scene.tts_audio_duration && (
                <Typography variant="caption" color="primary">
                  Audio: {scene.tts_audio_duration.toFixed(1)}s
                </Typography>
              )}
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={isGeneratingScript ? <CircularProgress size={16} /> : <AutoFixHighIcon />}
                disabled={isProcessing || isGeneratingScript || !scriptText.trim()}
                size="small"
                sx={{ flex: 1 }}
                onClick={async () => {
                  setIsGeneratingScript(true);
                  try {
                    const context = otherScenesText?.filter(Boolean).length
                      ? `\n\nPrevious scenes in this video (for continuity):\n${otherScenesText.map((t, i) => `Scene ${i + 1}: "${t}"`).join('\n')}`
                      : '';
                    const prompt = `You are a professional video script writer. Write a SHORT narration script for a SINGLE scene in a video.

Topic/idea: "${scriptText.trim()}"
${context}

Rules:
- Write ONLY the narration text (no titles, no scene directions, no quotes)
- Keep it between 15-30 words (about 5-10 seconds of speech)
- Make it engaging and conversational
- If previous scenes exist, continue the narrative naturally
- Output ONLY the narration text, nothing else`;

                    const res = await pollinationsApi.generateTextSync({ prompt, temperature: 0.7 });
                    const generated = res?.data?.text?.trim()?.replace(/^["']|["']$/g, '') || '';
                    if (generated) {
                      setScriptText(generated);
                      onUpdate({ script_text: generated });
                    }
                  } catch (err) {
                    console.error('AI script generation failed:', err);
                  } finally {
                    setIsGeneratingScript(false);
                  }
                }}
              >
                {isGeneratingScript ? 'Writing...' : 'AI Write'}
              </Button>
              <Button
                variant="contained"
                startIcon={isProcessing ? <CircularProgress size={16} /> : <RecordVoiceOverIcon />}
                onClick={onGenerateTTS}
                disabled={isProcessing || !scriptText.trim()}
                size="small"
                sx={{ flex: 1 }}
              >
                Generate Voice
              </Button>
            </Box>

            {/* Audio preview */}
            {scene.tts_audio_url && (
              <Box>
                <Typography variant="caption" color="text.secondary" gutterBottom>Audio Preview</Typography>
                <audio controls src={scene.tts_audio_url} style={{ width: '100%', height: 32 }} />
                {scene.word_timestamps && (
                  <Typography variant="caption" color="success.main">
                    {scene.word_timestamps.length} word timestamps synced
                  </Typography>
                )}
              </Box>
            )}
          </Stack>
        )}

        {/* Media Tab */}
        {tab === 1 && (
          <Stack spacing={2}>
            <FormControl size="small" fullWidth>
              <InputLabel>Media Source</InputLabel>
              <Select
                value={scene.media_source_type || (projectMediaType === 'image' ? 'stock_image' : 'stock_video')}
                label="Media Source"
                onChange={e => onUpdate({ media_source_type: e.target.value })}
              >
                {(!projectMediaType || projectMediaType === 'video') && (
                  <MenuItem value="stock_video">Stock Video</MenuItem>
                )}
                {(!projectMediaType || projectMediaType === 'image') && (
                  <MenuItem value="stock_image">Stock Image</MenuItem>
                )}
                {(!projectMediaType || projectMediaType === 'video') && (
                  <MenuItem value="ai_video">AI Video</MenuItem>
                )}
                {(!projectMediaType || projectMediaType === 'image') && (
                  <MenuItem value="ai_image">AI Image</MenuItem>
                )}
                <MenuItem value="user_upload">Upload</MenuItem>
              </Select>
            </FormControl>

            {scene.media_source_type !== 'user_upload' && (
              <>
                <TextField
                  label="Search Terms"
                  fullWidth
                  size="small"
                  value={searchTerms}
                  onChange={e => {
                    setSearchTerms(e.target.value);
                    debouncedUpdate('media_search_terms', e.target.value.split(',').map(s => s.trim()).filter(Boolean));
                  }}
                  placeholder="sunset, ocean, waves"
                  helperText="Comma-separated search terms for stock footage"
                />

                {(scene.media_source_type === 'ai_video' || scene.media_source_type === 'ai_image') && (
                  <>
                    <TextField
                      label="AI Prompt"
                      fullWidth
                      size="small"
                      multiline
                      rows={2}
                      value={mediaPrompt}
                      onChange={e => {
                        setMediaPrompt(e.target.value);
                        debouncedUpdate('media_prompt', e.target.value);
                      }}
                      placeholder="Leave empty to auto-generate from script text, or describe the visual..."
                      helperText={!mediaPrompt && scriptText ? 'Will use script text as prompt' : undefined}
                    />
                    {scriptText && (
                      <Button
                        size="small"
                        variant="text"
                        startIcon={isGeneratingPrompt ? <CircularProgress size={14} /> : <AutoFixHighIcon />}
                        disabled={isGeneratingPrompt}
                        onClick={async () => {
                          setIsGeneratingPrompt(true);
                          try {
                            const mediaType = scene.media_source_type === 'ai_video' ? 'video' : 'image';
                            const response = await pollinationsApi.generateTextSync({
                              prompt: `You are an expert at creating visual prompts for AI ${mediaType} generation. Given this narration script, create a single compelling ${mediaType} generation prompt that visually represents the content. Focus on visual elements, composition, lighting, mood, and style. Keep it under 200 characters. No quotes. Just the prompt.\n\nScript: "${scriptText.slice(0, 300)}"`,
                              temperature: 0.7,
                            });
                            const generated = response?.data?.text?.trim()?.replace(/^["']|["']$/g, '') || '';
                            if (generated) {
                              setMediaPrompt(generated);
                              onUpdate({ media_prompt: generated });
                            }
                          } catch (err) {
                            console.error('Failed to generate prompt:', err);
                            const fallback = `cinematic, high quality, ${scriptText.slice(0, 200)}`;
                            setMediaPrompt(fallback);
                            onUpdate({ media_prompt: fallback });
                          } finally {
                            setIsGeneratingPrompt(false);
                          }
                        }}
                      >
                        {isGeneratingPrompt ? 'Generating...' : 'Generate from script'}
                      </Button>
                    )}
                  </>
                )}
              </>
            )}

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={isSearching ? <CircularProgress size={16} /> : (isStockMedia ? <SearchIcon /> : <AutoFixHighIcon />)}
                onClick={handleSearchMedia}
                disabled={isProcessing || isSearching}
                size="small"
                sx={{ flex: 1 }}
              >
                {isSearching ? 'Searching...' : scene.media_source_type?.startsWith('ai') ? 'Generate' : 'Search'}
              </Button>

              <Button
                variant="outlined"
                startIcon={<CloudUploadIcon />}
                onClick={() => fileInputRef.current?.click()}
                size="small"
              >
                Upload
              </Button>
              <input ref={fileInputRef} type="file" hidden accept="video/*,image/*" onChange={handleFileUpload} />
            </Box>

            {/* Media preview */}
            {scene.media_url && (
              <Box>
                <Typography variant="caption" color="text.secondary" gutterBottom>Media Preview</Typography>
                {scene.media_source_type?.includes('video') || scene.media_url.match(/\.(mp4|webm|mov)/) ? (
                  <video src={scene.media_url} controls style={{ width: '100%', maxHeight: 200, borderRadius: 4 }} />
                ) : (
                  <Box
                    component="img"
                    src={scene.media_url}
                    sx={{ width: '100%', maxHeight: 200, objectFit: 'contain', borderRadius: 1 }}
                  />
                )}
                <Typography variant="caption" color="text.secondary">
                  Provider: {scene.media_provider || 'unknown'}
                </Typography>
              </Box>
            )}
          </Stack>
        )}
      </Box>

      {/* Media Picker Dialog */}
      <Dialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ fontSize: '1rem' }}>
              {searchQuery ? `Results for "${searchQuery}"` : 'Stock Media'}
            </Typography>
            <Chip label={`${pickerResults.length} results`} size="small" />
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 1, maxHeight: '70vh' }}>
          {isSearching ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          ) : pickerResults.length === 0 ? (
            <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
              No results found. Try different search terms.
            </Typography>
          ) : (
            <ImageList cols={3} gap={8} sx={{ mt: 0 }}>
              {pickerResults.map((result) => {
                const isSelected = scene.media_url === (result.download_url || result.url);
                return (
                  <ImageListItem
                    key={result.id}
                    onClick={() => handleSelectMedia(result)}
                    sx={{
                      cursor: 'pointer',
                      borderRadius: 1,
                      overflow: 'hidden',
                      border: isSelected ? '2px solid' : '2px solid transparent',
                      borderColor: isSelected ? 'primary.main' : 'transparent',
                      position: 'relative',
                      '&:hover': { opacity: 0.85 },
                    }}
                  >
                    {result.type === 'video' ? (
                      <video
                        src={result.download_url || result.url}
                        poster={result.thumbnail}
                        muted
                        preload="none"
                        style={{ width: '100%', height: 140, objectFit: 'cover' }}
                        onMouseEnter={e => (e.target as HTMLVideoElement).play().catch(() => {})}
                        onMouseLeave={e => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }}
                      />
                    ) : (
                      <img
                        src={result.thumbnail || result.url}
                        alt=""
                        loading="lazy"
                        style={{ width: '100%', height: 140, objectFit: 'cover' }}
                      />
                    )}
                    {isSelected && (
                      <CheckCircleIcon
                        sx={{ position: 'absolute', top: 6, right: 6, color: 'primary.main', bgcolor: 'white', borderRadius: '50%' }}
                      />
                    )}
                    <ImageListItemBar
                      subtitle={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem' }}>
                          <span>{result.photographer || result.provider}</span>
                          {result.duration && <span>{result.duration}s</span>}
                        </Box>
                      }
                      sx={{ '& .MuiImageListItemBar-subtitle': { fontSize: '0.7rem' } }}
                    />
                  </ImageListItem>
                );
              })}
            </ImageList>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
