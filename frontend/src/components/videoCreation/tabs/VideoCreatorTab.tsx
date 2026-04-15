import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Paper,
  Card,
  CardContent,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Movie as MovieIcon,
} from '@mui/icons-material';

import { useVideoCreation } from '../../../hooks/useContentCreation';
import { directApi } from '../../../utils/api';
import {
  VideoCreationRequest,
  ContentCreationJobResult,
} from '../../../types/contentCreation';

import ScriptEditor from '../ScriptEditor';
import VideoResultPreview from '../VideoResultPreview';
import type { FormState } from '../../../pages/videoStudio/types';

// Use ContentCreationJobResult type from shared types
type VideoJobResult = ContentCreationJobResult;

interface VideoCreatorTabProps {
  formState: FormState;
  onFormChange: <K extends keyof FormState>(
    // eslint-disable-next-line no-unused-vars
    field: K,
    // eslint-disable-next-line no-unused-vars
    value: FormState[K]
  ) => void;
  // eslint-disable-next-line no-unused-vars
  onJobStatusChange?: (statusUpdate: {
    isCreating: boolean;
    jobId: string | null;
    status: string;
    progress: number;
    error: string | null;
    result: VideoJobResult | null;
  }) => void;
}

const VideoCreatorTab: React.FC<VideoCreatorTabProps> = ({
  formState,
  onFormChange,
  onJobStatusChange
}) => {
  const {
    result,
    jobStatus,
    jobProgress,
    pollingJobId,
    loading,
    error,
    isResumedJob,
    createVideo,
    resetState,
    setError
  } = useVideoCreation();

  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [isResearchingTopic, setIsResearchingTopic] = useState(false);
  const [researchResults, setResearchResults] = useState<{ title: string, content: string, sources: string[], language: string } | null>(null);

  // Notify parent of job status changes for sidebar display
  useEffect(() => {
    if (onJobStatusChange) {
      onJobStatusChange({
        isCreating: loading,
        jobId: pollingJobId,
        status: jobProgress || jobStatus || (loading ? 'processing' : ''),
        progress: 0,
        error: error,
        result: result ? (result as unknown as VideoJobResult) : null
      });
    }
  }, [loading, jobStatus, jobProgress, pollingJobId, error, result, onJobStatusChange]);

  const handleFormChange = <K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) => {
    // Clear research results when topic changes
    if (field === 'topic') {
      setResearchResults(null);
    }
    onFormChange(field, value);
  };

  const handleGenerateScript = async () => {
    if (!formState.topic.trim()) {
      setError('Please enter a topic for script generation.');
      return;
    }

    setIsGeneratingScript(true);
    setError(null);

    try {
      const response = await directApi.generateScriptSync({
        topic: formState.topic,
        script_type: formState.scriptType,
        language: formState.language,
        max_duration: formState.maxDuration,
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to generate script');
      }

      const generatedScript = response.data?.script || '';

      if (!generatedScript?.trim()) {
        throw new Error('No script content received from API');
      }

      handleFormChange('script', generatedScript);
    } catch (err: unknown) {
      // Handle different types of errors
      let errorMsg = 'Failed to generate script';
      if (err instanceof Error) {
        errorMsg = err.message;
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { error?: string; detail?: string; message?: string } } };
        if (axiosError.response?.data?.error) {
          errorMsg = axiosError.response.data.error;
        } else if (axiosError.response?.data?.detail) {
          errorMsg = axiosError.response.data.detail;
        } else if (axiosError.response?.data?.message) {
          errorMsg = axiosError.response.data.message;
        }
      } else if (err && typeof err === 'object' && 'message' in err) {
        errorMsg = (err as { message: string }).message;
      }
      setError(`Script generation failed: ${errorMsg}`);
    } finally {
      setIsGeneratingScript(false);
    }
  };

  const handleGenerateFromResearch = async () => {
    if (!researchResults) {
      setError('No research results available. Please research the topic first.');
      return;
    }

    setIsGeneratingScript(true);
    setError(null);

    try {
      // Create an enhanced topic that includes research insights
      const enhancedTopic = `${formState.topic}\n\nResearch insights: ${researchResults.content.substring(0, 500)}...`;

      // Generate script using enhanced topic
      const response = await directApi.generateScriptSync({
        topic: enhancedTopic,
        script_type: formState.scriptType,
        language: formState.language,
        max_duration: formState.maxDuration,
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to generate script from research');
      }

      const generatedScript = response.data?.script || '';

      if (!generatedScript?.trim()) {
        throw new Error('No script content received from API');
      }

      handleFormChange('script', generatedScript);
      // Clear research results after successful script generation
      setResearchResults(null);
    } catch (err: unknown) {
      // Handle different types of errors
      let errorMsg = 'Failed to generate script from research';
      if (err instanceof Error) {
        errorMsg = err.message;
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { error?: string; detail?: string; message?: string } } };
        if (axiosError.response?.data?.error) {
          errorMsg = axiosError.response.data.error;
        } else if (axiosError.response?.data?.detail) {
          errorMsg = axiosError.response.data.detail;
        } else if (axiosError.response?.data?.message) {
          errorMsg = axiosError.response.data.message;
        }
      } else if (err && typeof err === 'object' && 'message' in err) {
        errorMsg = (err as { message: string }).message;
      }
      setError(`Script generation from research failed: ${errorMsg}`);
    } finally {
      setIsGeneratingScript(false);
    }
  };

  const handleResearchTopic = async () => {
    if (!formState.topic.trim()) {
      setError('Please enter a topic for research.');
      return;
    }

    setIsResearchingTopic(true);
    setError(null);
    setResearchResults(null); // Clear previous research

    try {
      // Use the topic research API endpoint
      const response = await directApi.researchTopic(formState.topic, formState.language);

      if (!response.success) {
        throw new Error(response.error || 'Failed to research topic');
      }

      const researchData = response.data;

      if (!researchData?.content?.trim()) {
        throw new Error('No content received from research');
      }

      // Store research results instead of directly setting script
      setResearchResults(researchData);
    } catch (err: unknown) {
      let errorMsg = 'Failed to research topic';
      if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(`Topic research failed: ${errorMsg}`);
    } finally {
      setIsResearchingTopic(false);
    }
  };

  const handleCreateVideo = async () => {
    // Validate input based on mode
    if (formState.autoDiscovery) {
      // Auto discovery mode - no script validation needed, pipeline will handle everything
      // Just ensure we have basic settings
    } else if (formState.mediaType === 'image') {
      // Image mode - script is required but topic can be optional 
      // (images can be used for content generation)
      if (!formState.script.trim()) {
        setError('Please enter or generate a script for your video.');
        return;
      }
    } else {
      // Video mode - requires script
      if (!formState.script.trim()) {
        setError('Please enter or generate a script for your video.');
        return;
      }
    }

    const request: VideoCreationRequest = {
      // Core content - handle different modes
      ...(formState.autoDiscovery ? {
        auto_topic: true,
        language: formState.language, // Include language for auto topic mode
      } : {
        // For image mode, we always need a script but topic is optional
        // The pipeline will extract image search terms from the script content automatically
        ...(formState.topic.trim() && { topic: formState.topic }),
        custom_script: formState.script || undefined,
        auto_topic: false,
        language: formState.language, // Include language for manual mode
      }),

      // Script generation options
      script_type: formState.scriptType,
      max_duration: formState.maxDuration,

      // Voice/TTS options
      enable_voice_over: formState.enableVoiceOver,
      enable_built_in_audio: formState.enableBuiltInAudio,
      voice: formState.voiceName,
      tts_provider: formState.voiceProvider,
      tts_speed: formState.ttsSpeed,

      // Media type selection (IMPORTANT: this parameter was missing!)
      media_type: formState.mediaType as 'video' | 'image', // 'video' or 'image' - tells backend what media to fetch

      // Image generation options (for AI images)
      image_provider: formState.mediaType === 'image' && formState.footageProvider === 'ai_generated' ? formState.aiImageProvider : 'together',
      image_width: formState.imageWidth,
      image_height: formState.imageHeight,
      image_steps: formState.inferenceSteps,
      guidance_scale: formState.guidanceScale,

      // Video options
      video_effect: formState.videoEffect,
      resolution: `${formState.imageWidth}x${formState.imageHeight}`,
      aspect_ratio: formState.aspectRatio,

      // Image-to-video motion settings (only when mediaType is 'image')
      ...(formState.mediaType === 'image' && {
        effect_type: formState.effectType,
        zoom_speed: formState.zoomSpeed,
        pan_direction: formState.panDirection,
        ken_burns_keypoints: formState.kenBurnsKeypoints,
      }),

      // Video orientation mapping (for footage-to-video mode)
      orientation: formState.aspectRatio === '16:9' ? 'landscape' :
        formState.aspectRatio === '1:1' ? 'square' : 'portrait',

      // Audio options - fix background music mapping
      generate_background_music: formState.backgroundMusic === 'ai_generate',
      background_music: formState.backgroundMusic,
      background_music_volume: formState.backgroundMusicVolume,

      // Caption options
      add_captions: formState.enableCaptions,
      caption_style: formState.captionStyle,
      caption_color: formState.captionColor,
      highlight_color: formState.highlightColor,
      caption_position: formState.captionPosition,
      font_size: formState.fontSize,
      font_family: formState.fontFamily,
      words_per_line: formState.wordsPerLine,
      margin_v: formState.marginV,
      outline_width: formState.outlineWidth,
      all_caps: formState.allCaps,

      // Advanced video settings
      frame_rate: formState.frameRate,
      crossfade_duration: formState.crossfadeDuration,
      search_terms_per_scene: formState.searchTermsPerScene,

      // Footage provider settings
      footage_provider: formState.footageProvider,
      ...(formState.footageProvider === 'ai_generated' && {
        ai_video_provider: formState.aiVideoProvider,
        ...(formState.aiVideoModel && { ai_video_model: formState.aiVideoModel }),
      }),
      search_safety: formState.searchSafety,
      footage_quality: formState.footageQuality,
      music_duration: formState.musicDuration,
    };

    try {
      await createVideo(request);
    } catch (err) {
      console.error('Failed to create video:', err);
    }
  };

  const handleReset = () => {
    resetState();
    // Reset form state through parent component
    onFormChange('topic', '');
    onFormChange('script', '');
    onFormChange('useCustomScript', true);
    onFormChange('voiceProvider', 'kokoro');
    onFormChange('voiceName', 'af_bella');
    onFormChange('language', 'en');
    onFormChange('imageWidth', 1080);
    onFormChange('imageHeight', 1920);
    onFormChange('aspectRatio', '9:16');
    onFormChange('captionStyle', 'viral_bounce');
    onFormChange('captionColor', '#FFFFFF');
    onFormChange('captionPosition', 'bottom_center');
    onFormChange('fontSize', 35);
    onFormChange('fontFamily', 'Arial-Bold');
    onFormChange('wordsPerLine', 4);
    onFormChange('marginV', 100);
    onFormChange('outlineWidth', 4);
    onFormChange('allCaps', false);
    onFormChange('footageProvider', 'pexels');
    onFormChange('aiVideoProvider', 'wavespeed');
    onFormChange('searchSafety', 'moderate');
    onFormChange('enableCaptions', true);
    onFormChange('backgroundMusic', 'chill');
    onFormChange('backgroundMusicVolume', 0.3);
    onFormChange('musicDuration', 60);
    onFormChange('footageQuality', 'high');
    onFormChange('scriptType', 'facts');
    onFormChange('maxDuration', 60);
    onFormChange('ttsSpeed', 1.0);
    onFormChange('videoEffect', 'ken_burns');
    onFormChange('generateBackgroundMusic', false);
    onFormChange('frameRate', 30);
    onFormChange('crossfadeDuration', 0.3);
    onFormChange('searchTermsPerScene', 3);
    onFormChange('mediaType', 'video');
    onFormChange('aiImageProvider', 'together');
    onFormChange('guidanceScale', 3.5);
    onFormChange('inferenceSteps', 4);
    onFormChange('effectType', 'ken_burns');
    onFormChange('zoomSpeed', 10);
    onFormChange('panDirection', 'right');
    onFormChange('kenBurnsKeypoints', [
      { time: 0, x: 0.2, y: 0.2, zoom: 1.2 },
      { time: 3, x: 0.8, y: 0.8, zoom: 1.0 }
    ]);
    onFormChange('autoDiscovery', false);
    onFormChange('researchDepth', 'basic');
    onFormChange('targetAudience', 'general');
    onFormChange('contentStyle', 'entertaining');
  };

  return (
    <Box sx={{
      p: { xs: 2, sm: 3 },
      height: '100%',
      overflow: 'auto',
      maxWidth: '100%'
    }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 600,
            mb: 1,
            display: 'flex',
            alignItems: 'center',
            fontSize: { xs: '1.25rem', sm: '1.5rem' },
            flexWrap: 'wrap',
            gap: 1
          }}
        >
          <PlayIcon sx={{ color: '#3b82f6', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
          Complete Video Creator
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontSize: { xs: '0.875rem', sm: '0.875rem' },
            lineHeight: 1.5
          }}
        >
          Create custom videos from scripts using stock footage, stock images, or AI-generated content.
          Choose videos for traditional stock footage, or choose images to automatically convert stock photos
          into video clips with motion effects (Ken Burns, zoom, pan). The system automatically finds relevant
          visuals based on your script content.
        </Typography>
      </Box>
      {/* Error Display */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Form Content - Always visible, status shown in sidebar */}
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: { xs: 2.5, sm: 3 },
        maxWidth: '100%'
      }}>
        {/* Script Editor */}
        <Paper elevation={0} sx={{
          border: '1px solid #e2e8f0',
          borderRadius: 2,
          overflow: 'hidden'
        }}>
          <ScriptEditor
            script={formState.script}
            scriptType={formState.scriptType}
            maxDuration={formState.maxDuration}
            topic={formState.topic}
            language={formState.language}
            isGeneratingScript={isGeneratingScript}
            isResearchingTopic={isResearchingTopic}
            hasResearchResults={!!researchResults}
            error={error}
            autoDiscovery={formState.autoDiscovery}
            // Callbacks
            onScriptChange={(script) => handleFormChange('script', script)}
            onScriptTypeChange={(type) => handleFormChange('scriptType', type)}
            onMaxDurationChange={(duration) => handleFormChange('maxDuration', duration)}
            onTopicChange={(topic) => handleFormChange('topic', topic)}
            onLanguageChange={(language) => handleFormChange('language', language)}
            onAutoDiscoveryChange={(enabled) => handleFormChange('autoDiscovery', enabled)}
            // Generation callbacks
            onGenerateScript={handleGenerateScript}
            onResearchTopic={handleResearchTopic}
            onGenerateFromResearch={handleGenerateFromResearch}
            onClearError={() => setError(null)}
          />
        </Paper>

        {/* Create Button */}
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
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayIcon />}
            onClick={handleCreateVideo}
            disabled={loading || (!formState.autoDiscovery && !formState.script.trim())}
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
            {loading ? 'Creating Video...' : 'Create Video'}
          </Button>
        </Box>

        {/* Processing status — only while actively polling */}
        {loading && !result && (
          <Card elevation={2} sx={{ mt: 3, border: '2px solid #2196f3' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <MovieIcon color="primary" />
                Video Creation
                <CircularProgress size={16} sx={{ ml: 1 }} />
                {isResumedJob && (
                  <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
                    (Resumed)
                  </Typography>
                )}
              </Typography>
              {pollingJobId && (
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontSize: '0.75rem' }}>
                    Job ID: {pollingJobId}
                  </Typography>
                  <LinearProgress variant="indeterminate" sx={{ mb: 1, height: 4, borderRadius: 2 }} />
                  <Typography variant="body2" sx={{ color: 'info.main', fontSize: '0.75rem' }}>
                    {jobProgress || 'Starting...'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Error — only if no result */}
        {error && !result && (
          <Card elevation={2} sx={{ mt: 3, border: '2px solid #f44336' }}>
            <CardContent>
              <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>{error}</Alert>
              <Button variant="outlined" size="small" onClick={handleReset}>Try Again</Button>
            </CardContent>
          </Card>
        )}

        {/* Completed result */}
        {result && jobStatus === 'completed' && result.result && (
          <Card elevation={2} sx={{ mt: 3, border: '2px solid #4caf50' }}>
            <CardContent>
              <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
                Video created successfully!
              </Alert>

              {/* Video Preview */}
              {(() => {
                const res = result.result as Record<string, unknown>;
                const videoUrl = res?.final_video_url || res?.video_url || res?.url;
                return typeof videoUrl === 'string' && videoUrl ? (
                  <Box sx={{ mb: 2 }}>
                    <VideoResultPreview url={videoUrl} />
                  </Box>
                ) : null;
              })()}

              {/* Create Another */}
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button variant="outlined" size="small" onClick={handleReset}>
                  Create Another
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
};

export default VideoCreatorTab;