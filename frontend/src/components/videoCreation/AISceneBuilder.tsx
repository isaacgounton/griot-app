/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  DragIndicator as DragIcon,
  AutoAwesome as AIIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as ResearchIcon,
  Build as ManualIcon,
  Movie as MovieIcon,
} from '@mui/icons-material';

import { VideoScene, ContentCreationJobResult } from '../../types/contentCreation';
import { directApi, pollinationsApi } from '../../utils/api';
import VideoResultPreview from './VideoResultPreview';

// Use ContentCreationJobResult type from shared types
type VideoJobResult = ContentCreationJobResult;

interface AISceneBuilderProps {
  scenes: VideoScene[];
  onChange: (scenes: VideoScene[]) => void;
  voiceProvider?: string;
  voiceName?: string;
  resolution?: string;
  onVoiceProviderChange?: (provider: string) => void;
  onVoiceNameChange?: (name: string) => void;
  onResolutionChange?: (resolution: string) => void;
  onAiImageModelChange?: (model: string) => void;
  onAiVideoModelChange?: (model: string) => void;
  // Additional settings from VideoCreation parent
  footageProvider?: string;
  footageQuality?: string;
  searchSafety?: string;
  mediaType?: string;
  aiVideoProvider?: string;
  aiVideoModel?: string;
  aiImageProvider?: string;
  aiImageModel?: string;
  backgroundMusic?: string;
  backgroundMusicVolume?: number;
  enableCaptions?: boolean;
  captionStyle?: string;
  captionColor?: string;
  highlightColor?: string;
  captionPosition?: string;
  fontSize?: number;
  fontFamily?: string;
  wordsPerLine?: number;
  marginV?: number;
  outlineWidth?: number;
  allCaps?: boolean;
  ttsSpeed?: number;
  enableVoiceOver?: boolean;
  enableBuiltInAudio?: boolean;
  // Image-to-video motion settings
  effectType?: string;
  zoomSpeed?: number;
  panDirection?: string;
  kenBurnsKeypoints?: Array<{ time: number; x: number; y: number; zoom: number }>;
  // Job status callbacks to parent
  onJobStatusChange?: (status: {
    isCreating: boolean;
    jobId: string | null;
    status: string;
    progress: number;
    error: string | null;
    result: VideoJobResult | null;
  }) => void;
}

interface ResearchResult {
  title: string;
  content: string;
  sources: string[];
  summary?: string;
  articles?: Array<{
    title: string;
    description: string;
    url: string;
    source: string;
  }>;
}

interface AIGeneratedScene {
  text: string;
  searchTerms: string[];
  duration: number;
}

const AISceneBuilder: React.FC<AISceneBuilderProps> = ({
  scenes,
  onChange,
  voiceProvider = 'kokoro',
  voiceName = 'af_bella',
  resolution = '1080x1920',
  onVoiceProviderChange: _onVoiceProviderChange,
  onVoiceNameChange: _onVoiceNameChange,
  onResolutionChange: _onResolutionChange,
  onAiImageModelChange,
  onAiVideoModelChange,
  // Additional settings with defaults
  footageProvider = 'ai_generated',
  footageQuality = 'high',
  searchSafety = 'moderate',
  mediaType = 'video',
  aiVideoProvider = 'pollinations',
  aiVideoModel = 'veo',
  aiImageProvider = 'together',
  aiImageModel = 'modal-image',
  backgroundMusic = 'chill',
  backgroundMusicVolume = 0.3,
  enableCaptions = true,
  captionStyle = 'viral_bounce',
  captionColor = '#FFFFFF',
  highlightColor = '#FFFF00',
  captionPosition = 'bottom',
  fontSize = 48,
  fontFamily = 'Arial-Bold',
  wordsPerLine = 6,
  marginV = 100,
  outlineWidth = 4,
  allCaps = false,
  ttsSpeed = 1.0,
  enableVoiceOver = true,
  enableBuiltInAudio = false,
  effectType = 'ken_burns',
  zoomSpeed = 10,
  panDirection = 'left_to_right',
  kenBurnsKeypoints,
  onJobStatusChange,
}) => {
  // AI Research States
  const [researchMode, setResearchMode] = useState(true); // Toggle between AI research and manual
  const [researchTopic, setResearchTopic] = useState('');
  const [researchLanguage, setResearchLanguage] = useState('en');
  const [isResearching, setIsResearching] = useState(false);
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null);
  const [researchError, setResearchError] = useState<string | null>(null);
  
  // Scene Generation States
  const [isGeneratingScenes, setIsGeneratingScenes] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [autoGenerateEnabled, setAutoGenerateEnabled] = useState(false);
  
  // Image models state for background footage
  const [, setImageModels] = useState<string[]>([]);
  const [, setLoadingImageModels] = useState(false);

  // Video models state for background footage
  const [, setVideoModels] = useState<string[]>([]);
  const [, setLoadingVideoModels] = useState(false);

  // Load image models when using AI-generated images
  useEffect(() => {
    if (footageProvider === 'ai_generated' && mediaType === 'image') {
      const loadImageModels = async () => {
        try {
          setLoadingImageModels(true);
          const response = await pollinationsApi.listImageModels();
          if (response?.success && response?.data?.models) {
            const rawModels = response.data.models;
            const models = (Array.isArray(rawModels) ? rawModels : [])
              .map((m: unknown) => {
                if (typeof m === 'string') return m;
                if (m && typeof m === 'object' && 'name' in m) return String((m as { name: string }).name);
                return '';
              })
              .filter((m: string) => m.length > 0)
              .map((m: string) => m.toLowerCase().trim());
            const uniqueModels = Array.from(new Set(models));
            setImageModels(uniqueModels);
            // Auto-select first model
            if (uniqueModels.length > 0 && onAiImageModelChange) {
              onAiImageModelChange(uniqueModels[0]);
            }
          }
        } catch (error) {
          console.error('Failed to load image models:', error);
          setImageModels(['modal-image', 'flux-realism', 'flux-cablyai', 'flux-anime']);
        } finally {
          setLoadingImageModels(false);
        }
      };
      loadImageModels();
    } else {
      setImageModels([]);
    }
  }, [footageProvider, mediaType]);

  // Load video models when using Griot AI video generation
  useEffect(() => {
    if (footageProvider === 'ai_generated' && mediaType === 'video' && aiVideoProvider === 'pollinations') {
      const loadVideoModels = async () => {
        try {
          setLoadingVideoModels(true);
          const response = await pollinationsApi.listVideoModels();

          if (response?.success && response?.data?.models) {
            const rawModels = response.data.models;
            const models = (Array.isArray(rawModels) ? rawModels : [])
              .map((m: any) => {
                if (typeof m === 'string') return m;
                if (m && typeof m === 'object' && m.name) return String(m.name);
                return '';
              })
              .filter((m: string) => m.length > 0)
              .map((m: string) => m.toLowerCase().trim());
            const uniqueModels = Array.from(new Set(models));
            setVideoModels(uniqueModels);
            // Auto-select first model
            if (uniqueModels.length > 0 && onAiVideoModelChange) {
              onAiVideoModelChange(uniqueModels[0]);
            }
          }
        } catch (error) {
          console.error('Failed to load video models:', error);
          setVideoModels(['veo', 'seedance', 'seedance-pro']);
        } finally {
          setLoadingVideoModels(false);
        }
      };
      loadVideoModels();
    } else {
      setVideoModels([]);
    }
  }, [footageProvider, mediaType, aiVideoProvider]);
  
  // Job polling states
  const [_jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  
  // Video creation states
  const [isCreatingVideo, setIsCreatingVideo] = useState(false);
  const [videoCreationError, setVideoCreationError] = useState<string | null>(null);
  const [videoJobId, setVideoJobId] = useState<string | null>(null);
  const [videoJobStatus, setVideoJobStatus] = useState<string>('');
  const [videoJobProgress, setVideoJobProgress] = useState(0);
  const [videoResult, setVideoResult] = useState<VideoJobResult | null>(null);
  const [, setSnackbarOpen] = useState(false);
  const [, setSnackbarMessage] = useState('');

  // Manual scene editor functions (existing functionality)
  const handleSceneChange = (index: number, field: keyof VideoScene, value: VideoScene[keyof VideoScene]) => {
    const updatedScenes = scenes.map((scene, i) => 
      i === index ? { ...scene, [field]: value } : scene
    );
    onChange(updatedScenes);
  };

  const handleAddScene = () => {
    onChange([...scenes, { text: '', duration: 3, searchTerms: [] }]);
  };

  const handleRemoveScene = (index: number) => {
    if (scenes.length > 1) {
      onChange(scenes.filter((_, i) => i !== index));
    }
  };

  const addSearchTerm = (sceneIndex: number) => {
    const scene = scenes[sceneIndex];
    const newSearchTerms = [...(scene.searchTerms || []), ''];
    handleSceneChange(sceneIndex, 'searchTerms', newSearchTerms);
  };

  const updateSearchTerm = (sceneIndex: number, termIndex: number, value: string) => {
    const scene = scenes[sceneIndex];
    const newSearchTerms = [...(scene.searchTerms || [])];
    newSearchTerms[termIndex] = value;
    handleSceneChange(sceneIndex, 'searchTerms', newSearchTerms);
  };

  const removeSearchTerm = (sceneIndex: number, termIndex: number) => {
    const scene = scenes[sceneIndex];
    const newSearchTerms = (scene.searchTerms || []).filter((_, i) => i !== termIndex);
    handleSceneChange(sceneIndex, 'searchTerms', newSearchTerms.length > 0 ? newSearchTerms : ['']);
  };

  // AI Research functionality
  const handleTopicResearch = async () => {
    if (!researchTopic.trim()) {
      setResearchError('Please enter a research topic');
      return;
    }

    setIsResearching(true);
    setResearchError(null);
    setResearchResult(null);

    try {
      // Use the existing research endpoints
      const response = await directApi.post('/research/web', {
        query: researchTopic,
        engine: 'perplexity', // Use perplexity for comprehensive research
        max_results: 5
      });

      if (response.data && response.data.results) {
        const researchData: ResearchResult = {
          title: researchTopic,
          content: response.data.results.map((r: any) => r.content).join('\n\n'),
          sources: response.data.results.map((r: any) => r.source || r.url).filter(Boolean),
          articles: response.data.results.map((r: any) => ({
            title: r.title || '',
            description: r.description || r.content?.substring(0, 200) + '...' || '',
            url: r.url || '',
            source: r.source || 'Web'
          }))
        };
        
        setResearchResult(researchData);
        
        // Auto-generate scenes if enabled
        if (autoGenerateEnabled) {
          await handleAutoGenerateScenes(researchData);
        }
      } else {
        throw new Error('No research results found');
      }
    } catch (err: any) {
      console.error('Research error:', err);
      setResearchError(err.message || 'Failed to research topic');
    } finally {
      setIsResearching(false);
    }
  };

  // Poll job status for scene generation
  const pollJobStatus = async (jobId: string): Promise<any> => {
    const maxAttempts = 60;
    let attempts = 0;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const statusResponse = await directApi.get(`/jobs/${jobId}/status`);
          
          const status = statusResponse.data.data?.status || statusResponse.data.status;
          const result = statusResponse.data.data?.result || statusResponse.data.result;
          const error = statusResponse.data.data?.error || statusResponse.data.error;
          
          setJobStatus(`${status} (${attempts}/${maxAttempts})`);

          if (status === 'completed') {
            resolve(result);
            return;
          } else if (status === 'failed') {
            reject(new Error(error || 'Job failed'));
            return;
          }

          if (attempts < maxAttempts) {
            setTimeout(poll, 3000); // Poll every 3 seconds
          } else {
            reject(new Error('Job timeout'));
          }
        } catch (err) {
          if (attempts < maxAttempts) {
            setTimeout(poll, 3000);
          } else {
            reject(err);
          }
        }
      };

      poll();
    });
  };

  // Auto-generate scenes from research
  const handleAutoGenerateScenes = async (researchData?: ResearchResult) => {
    const dataToUse = researchData || researchResult;
    
    if (!dataToUse) {
      setGenerationError('Please conduct research first');
      return;
    }

    setIsGeneratingScenes(true);
    setGenerationError(null);
    setJobStatus('');

    try {
      // Use the script generation endpoint with research content
      const requestData = {
        topic: dataToUse.title,
        content: dataToUse.content,
        script_type: 'research_based',
        language: researchLanguage,
        target_duration: 60,
        style: 'educational',
        auto_scenes: true
      };

      const response = await directApi.post('/ai/script/generate', requestData);
      
      if (response.data?.job_id) {
        setJobId(response.data.job_id);
        const result = await pollJobStatus(response.data.job_id);
        
        if (result.scenes) {
          // Convert AI-generated scenes to VideoScene format
          const aiScenes: VideoScene[] = result.scenes.map((scene: AIGeneratedScene, _index: number) => ({
            text: scene.text,
            duration: scene.duration || 3,
            searchTerms: scene.searchTerms || []
          }));
          
          onChange(aiScenes);
        } else if (result.script) {
          // If we get script content, create scenes from it with AI search terms
          const scriptScenes = await parseScriptToScenes(result.script);
          onChange(scriptScenes);
        }
      }
    } catch (err: any) {
      console.error('Scene generation error:', err);
      setGenerationError(err.message || 'Failed to generate scenes');
    } finally {
      setIsGeneratingScenes(false);
      setJobId(null);
      setJobStatus('');
    }
  };

  // Parse script content into scenes, then use AI to generate search terms
  const parseScriptToScenes = async (script: string): Promise<VideoScene[]> => {
    const sentences = script.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const scenesData: VideoScene[] = [];

    for (let i = 0; i < sentences.length; i += 2) {
      const sceneText = sentences.slice(i, i + 2).join('. ').trim();
      if (sceneText) {
        scenesData.push({
          text: sceneText + (sceneText.endsWith('.') ? '' : '.'),
          duration: Math.min(Math.max(sceneText.split(' ').length * 0.4, 2), 8),
          searchTerms: []
        });
      }
    }

    const scenes = scenesData.length > 0 ? scenesData : [{
      text: script.substring(0, 200) + '...',
      duration: 5,
      searchTerms: [] as string[]
    }];

    // Use the AI video-search-queries endpoint to generate proper search terms
    try {
      const response = await directApi.post('/ai/video-search-queries', {
        script,
        segment_duration: 3.0,
        provider: 'auto',
      });

      if (response.data?.job_id) {
        const result = await pollJobStatus(response.data.job_id);
        const queries = result?.queries || [];
        if (queries.length > 0) {
          for (let i = 0; i < scenes.length && i < queries.length; i++) {
            const query = queries[i]?.query;
            if (query) {
              scenes[i].searchTerms = query.split(/\s+/).slice(0, 4);
            }
          }
        }
      }
    } catch (err) {
      console.warn('AI search term generation failed, using fallback:', err);
      // Fallback: extract keywords with Unicode support
      for (const scene of scenes) {
        const words = scene.text.toLowerCase().match(/[\p{L}]{4,}/gu) || [];
        scene.searchTerms = words.slice(0, 3);
      }
    }

    return scenes;
  };

  // Create video from scenes
  const handleCreateVideo = async () => {
    // Validate scenes
    const validScenes = scenes.filter(scene => scene.text.trim());
    if (validScenes.length === 0) {
      setVideoCreationError('At least one scene with text is required');
      return;
    }

    setIsCreatingVideo(true);
    setVideoCreationError(null);
    setVideoResult(null);
    setVideoJobProgress(0);

    // Determine orientation from resolution
    const [width, height] = resolution.split('x').map(Number);
    const orientation = height > width ? 'portrait' : (width > height ? 'landscape' : 'square');
    
    // Map volume to string for backend
    const volumeMap: Record<string, string> = { '0.1': 'low', '0.3': 'medium', '0.5': 'high' };
    const musicVolumeStr = volumeMap[backgroundMusicVolume.toString()] || 'medium';

    try {
      // Prepare request data with all settings
      const requestData = {
        scenes: validScenes.map(scene => ({
          text: scene.text,
          searchTerms: scene.searchTerms?.length ? scene.searchTerms : ['background', 'visual'],
          duration: scene.duration || 3
        })),
        config: {
          // Voice settings
          voice: voiceName,
          provider: voiceProvider,
          ttsSpeed: ttsSpeed,
          enable_voice_over: enableVoiceOver,
          enable_built_in_audio: enableBuiltInAudio,
          
          // Background footage settings - use props from sidebar
          footageProvider: footageProvider,
          footageQuality: footageQuality,
          searchSafety: searchSafety,
          mediaType: mediaType,
          aiVideoProvider: aiVideoProvider,
          aiVideoModel: aiVideoModel,  // Add video model to config
          aiImageProvider: aiImageProvider,
          aiImageModel: aiImageModel,  // Add image model to config
          
          // Music settings
          music: backgroundMusic,
          musicVolume: musicVolumeStr,
          
          // Caption settings
          enableCaptions: enableCaptions,
          captionStyle: captionStyle,
          captionColor: captionColor,
          highlightColor: highlightColor,
          captionPosition: captionPosition,
          fontSize: fontSize,
          fontFamily: fontFamily,
          wordsPerLine: wordsPerLine,
          marginV: marginV,
          outlineWidth: outlineWidth,
          allCaps: allCaps,

          // Image-to-video motion settings (only when mediaType is 'image')
          ...(mediaType === 'image' ? {
            effect_type: effectType,
            zoom_speed: zoomSpeed,
            pan_direction: panDirection,
            ken_burns_keypoints: kenBurnsKeypoints,
          } : {}),

          // Video settings
          orientation: orientation,
          resolution: resolution,
          language: researchLanguage,
        }
      };

      // Create video job
      const response = await directApi.post('/ai/scenes-to-video', requestData);
      
      if (response.data && response.data.job_id) {
        setVideoJobId(response.data.job_id);
        setVideoJobStatus('processing');
        
        // Poll for video job completion
        await pollVideoJobStatus(response.data.job_id);
      } else {
        throw new Error('Failed to create video job');
      }
    } catch (err: any) {
      console.error('Video creation error:', err);
      setVideoCreationError(err.response?.data?.detail || err.message || 'Failed to create video');
      setIsCreatingVideo(false);
    }
  };

  // Poll video job status
  const pollVideoJobStatus = async (jobId: string) => {
    const maxAttempts = 180; // 15 minutes max (5 second intervals)
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const response = await directApi.get(`/jobs/${jobId}/status`);
        const jobData = response.data?.data || response.data;
        const status = jobData?.status;

        if (status === 'completed') {
          setVideoJobStatus('completed');
          setVideoJobProgress(100);
          setVideoResult(jobData.result);
          setIsCreatingVideo(false);
          setSnackbarMessage('Video created successfully!');
          setSnackbarOpen(true);
          return;
        } else if (status === 'failed') {
          setVideoJobStatus('failed');
          setVideoCreationError(jobData.error || 'Video creation failed');
          setIsCreatingVideo(false);
          return;
        } else {
          setVideoJobProgress(jobData.progress || Math.min(attempts * 2, 90));
          setVideoJobStatus(`Processing video... (${attempts}/${maxAttempts})`);

          if (attempts < maxAttempts) {
            setTimeout(poll, 5000);
          } else {
            setVideoCreationError('Video creation timed out. Please check the Jobs page.');
            setIsCreatingVideo(false);
          }
        }
      } catch (err: any) {
        console.error('Error polling job status:', err);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setVideoCreationError('Failed to get job status');
          setIsCreatingVideo(false);
        }
      }
    };

    poll();
  };

  const getTotalDuration = () => {
    return scenes.reduce((total, scene) => total + (scene.duration || 0), 0);
  };

  // Notify parent of job status changes
  useEffect(() => {
    if (onJobStatusChange) {
      onJobStatusChange({
        isCreating: isCreatingVideo,
        jobId: videoJobId,
        status: videoJobStatus,
        progress: videoJobProgress,
        error: videoCreationError,
        result: videoResult
      });
    }
  }, [isCreatingVideo, videoJobId, videoJobStatus, videoJobProgress, videoCreationError, videoResult, onJobStatusChange]);

  return (
    <Box sx={{ p: 3 }}>
      {/* Mode Toggle */}
      <Box sx={{ mb: 3 }}>
        <FormControlLabel
          control={
            <Switch
              checked={researchMode}
              onChange={(e) => setResearchMode(e.target.checked)}
              color="primary"
            />
          }
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {researchMode ? <ResearchIcon color="primary" /> : <ManualIcon color="primary" />}
              <Typography variant="body2">
                {researchMode ? 'AI Research Mode' : 'Manual Scene Mode'}
              </Typography>
            </Box>
          }
        />
      </Box>

      {/* AI Research Mode */}
      {researchMode && (
        <Card elevation={2} sx={{ mb: 3, border: '2px solid #e3f2fd' }}>
          <CardContent>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AIIcon color="primary" />
              AI-Powered Scene Research
            </Typography>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Research Topic"
                  value={researchTopic}
                  onChange={(e) => setResearchTopic(e.target.value)}
                  placeholder="e.g., Climate change impacts, AI in healthcare, Space exploration"
                  helperText="Enter a topic for AI research and automatic scene generation"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={researchLanguage}
                    label="Language"
                    onChange={(e) => setResearchLanguage(e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                    <MenuItem value="de">German</MenuItem>
                    <MenuItem value="it">Italian</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoGenerateEnabled}
                      onChange={(e) => setAutoGenerateEnabled(e.target.checked)}
                    />
                  }
                  label="Auto-generate scenes"
                />
              </Grid>
            </Grid>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={isResearching ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleTopicResearch}
                disabled={isResearching || !researchTopic.trim()}
              >
                {isResearching ? 'Researching...' : 'Research Topic'}
              </Button>
              
              {researchResult && (
                <Button
                  variant="outlined"
                  startIcon={isGeneratingScenes ? <CircularProgress size={20} /> : <AIIcon />}
                  onClick={() => handleAutoGenerateScenes()}
                  disabled={isGeneratingScenes}
                >
                  {isGeneratingScenes ? 'Generating...' : 'Generate Scenes'}
                </Button>
              )}
            </Box>

            {/* Job Status */}
            {jobStatus && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress sx={{ mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Status: {jobStatus}
                </Typography>
              </Box>
            )}

            {/* Research Results */}
            {researchResult && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Research Results: {researchResult.title}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    {researchResult.articles && researchResult.articles.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Sources Found:</Typography>
                        {researchResult.articles.slice(0, 3).map((article, index) => (
                          <Chip
                            key={index}
                            label={article.source}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                    
                    <Typography variant="body2" sx={{ 
                      maxHeight: 200, 
                      overflow: 'auto',
                      bgcolor: '#f5f5f5',
                      p: 2,
                      borderRadius: 1
                    }}>
                      {researchResult.content.substring(0, 500)}...
                    </Typography>
                  </Box>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Errors */}
            {researchError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {researchError}
              </Alert>
            )}
            
            {generationError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {generationError}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Background Settings Section */}
      <Card elevation={2} sx={{ mb: 3, display: 'none' }}>
        {/* REMOVED: This section is now in the sidebar settings - no need to duplicate in canvas */}
      </Card>

      {/* Scene Editor Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DragIcon color="primary" />
          Video Scenes {researchMode ? '(AI Enhanced)' : '(Manual)'}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Total Duration: {getTotalDuration()}s
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddIcon />}
            onClick={handleAddScene}
          >
            Add Scene
          </Button>
        </Box>
      </Box>


      {/* Scenes List */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {scenes.length === 0 && (
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: '#f8f9fa' }}>
            <Typography variant="body1" color="text.secondary">
              {researchMode 
                ? '🧠 Research a topic above to automatically generate scenes with AI'
                : '📝 Click "Add Scene" to manually create your video scenes'
              }
            </Typography>
          </Paper>
        )}
        
        {scenes.map((scene, index) => (
          <Accordion key={index} sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', pr: 2 }}>
                <Typography variant="subtitle2">
                  Scene {index + 1} {scene.text && `- "${scene.text.slice(0, 40)}..."`}
                </Typography>
                {researchMode && (
                  <Chip
                    size="small"
                    icon={<AIIcon />}
                    label="AI"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                {/* Scene Text */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Scene Text"
                    placeholder="Enter the narration text for this scene..."
                    value={scene.text}
                    onChange={(e) => handleSceneChange(index, 'text', e.target.value)}
                    helperText={`${scene.text.length} characters • ~${Math.ceil(scene.text.split(' ').length / 3)} seconds reading time`}
                  />
                </Grid>

                {/* Search Terms for Background Video */}
                <Grid item xs={12} lg={8}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Search Terms for Background Video
                  </Typography>
                  {(scene.searchTerms || ['']).map((term, termIndex) => (
                    <Box key={termIndex} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="e.g., technology, innovation, nature"
                        value={term}
                        onChange={(e) => updateSearchTerm(index, termIndex, e.target.value)}
                      />
                      {(scene.searchTerms || []).length > 1 && (
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          onClick={() => removeSearchTerm(index, termIndex)}
                          sx={{ minWidth: 'auto', px: 1 }}
                        >
                          ✕
                        </Button>
                      )}
                    </Box>
                  ))}
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => addSearchTerm(index)}
                    sx={{ mt: 1 }}
                  >
                    + Add Search Term
                  </Button>
                </Grid>

                {/* Duration */}
                <Grid item xs={12} lg={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Duration (seconds)"
                    value={scene.duration}
                    onChange={(e) => handleSceneChange(index, 'duration', parseFloat(e.target.value))}
                    inputProps={{ min: 1, max: 30, step: 0.5 }}
                  />
                </Grid>

                {/* Remove Scene Button */}
                {scenes.length > 1 && (
                  <Grid item xs={12}>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() => handleRemoveScene(index)}
                    >
                      Remove Scene
                    </Button>
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>

      {/* Add Scene Button */}
      {scenes.length > 0 && (
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleAddScene}
            size="large"
          >
            Add Another Scene
          </Button>
        </Box>
      )}

      {/* Create Video Button - Exposed to parent via onJobStatusChange */}
      {scenes.length > 0 && (
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1,
          pt: { xs: 1, sm: 2 },
          px: { xs: 0, sm: 0 }
        }}>
          <Button
            variant="contained"
            size="large"
            startIcon={isCreatingVideo ? <CircularProgress size={20} color="inherit" /> : <MovieIcon />}
            onClick={handleCreateVideo}
            disabled={isCreatingVideo || scenes.some(scene => !scene.text || !scene.text.trim())}
            sx={{
              backgroundColor: '#3b82f6',
              '&:hover': { backgroundColor: '#2563eb' },
              '&:disabled': { 
                backgroundColor: '#cbd5e1',
                color: '#64748b'
              },
              borderRadius: 2,
              px: { xs: 3, sm: 4 },
              py: { xs: 1.25, sm: 1.5 },
              fontSize: { xs: '1rem', sm: '1.1rem' },
              fontWeight: 600,
              minWidth: { xs: '250px', sm: 'auto' },
              width: { xs: '100%', sm: 'auto' },
              maxWidth: { xs: '100%', sm: '300px' }
            }}
          >
            {isCreatingVideo ? 'Creating Video...' : 'Create Video'}
          </Button>
          {scenes.some(scene => !scene.text || !scene.text.trim()) && (
            <Typography variant="caption" color="error">
              All scenes must have narration text
            </Typography>
          )}
        </Box>
      )}

      {/* Job Status Panel - shown while processing or after completion */}
      {(isCreatingVideo || videoResult || videoCreationError) && (
        <Card elevation={2} sx={{ mt: 3, border: videoJobStatus === 'completed' ? '2px solid #4caf50' : videoJobStatus === 'failed' ? '2px solid #f44336' : '2px solid #2196f3' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <MovieIcon color={videoJobStatus === 'completed' ? 'success' : videoJobStatus === 'failed' ? 'error' : 'primary'} />
              Video Creation
              {isCreatingVideo && (
                <CircularProgress size={16} sx={{ ml: 1 }} />
              )}
            </Typography>

            {/* Job ID & Progress */}
            {videoJobId && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontSize: '0.75rem' }}>
                  Job ID: {videoJobId}
                </Typography>
                <LinearProgress
                  variant={videoJobStatus === 'completed' ? 'determinate' : 'indeterminate'}
                  value={videoJobStatus === 'completed' ? 100 : undefined}
                  sx={{ mb: 1, height: 4, borderRadius: 2 }}
                />
                <Typography variant="body2" sx={{
                  color: videoJobStatus === 'completed' ? 'success.main' :
                    videoJobStatus === 'failed' ? 'error.main' : 'info.main',
                  fontSize: '0.75rem'
                }}>
                  {videoJobStatus || 'Starting...'}
                </Typography>
              </Box>
            )}

            {/* Error */}
            {videoCreationError && (
              <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>
                {videoCreationError}
              </Alert>
            )}

            {/* Success Result */}
            {videoResult && videoJobStatus === 'completed' && (
              <Box>
                <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
                  Video created successfully!
                </Alert>

                {/* Video Preview */}
                {((videoResult as any).final_video_url || (videoResult as any).video_url) && (
                  <Box sx={{ mb: 2 }}>
                    <VideoResultPreview
                      url={(videoResult as any).final_video_url || (videoResult as any).video_url}
                    />
                  </Box>
                )}

                {/* Dismiss */}
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => {
                      setVideoResult(null);
                      setVideoJobId(null);
                      setVideoJobStatus('');
                      setVideoJobProgress(0);
                      setVideoCreationError(null);
                    }}
                  >
                    Dismiss
                  </Button>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Footer Info */}
      <Box sx={{ mt: 3, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {researchMode
            ? 'AI mode: Research any topic, auto-generate scenes, edit as needed. Perfect for educational content!'
            : 'Manual mode: Full control over each scene. Keep scenes 3-10 seconds for optimal pacing. Use specific search terms for better background visuals.'
          }
        </Typography>
      </Box>
    </Box>
  );
};

export default AISceneBuilder;