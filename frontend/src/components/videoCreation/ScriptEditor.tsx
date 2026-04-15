import React, { useCallback, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Grid,
  Chip,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Card,
  CardContent,
  LinearProgress,
  CircularProgress,
  Alert,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  Timer as TimerIcon,
  TextFields as TextIcon,
  Lightbulb as IdeaIcon,
  Clear as ClearIcon,
  Help as HelpIcon,
  Language as LanguageIcon,
  Search as ResearchIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';

import { getSupportedLanguages } from '../../utils/languageDetection';

interface ScriptEditorProps {
  script: string;
  scriptType: string;
  maxDuration: number;
  topic?: string;
  language?: string;
  isGeneratingScript?: boolean;
  isResearchingTopic?: boolean;
  hasResearchResults?: boolean;
  error?: string | null;
  autoDiscovery?: boolean;
  // Callbacks
  // eslint-disable-next-line no-unused-vars
  onScriptChange: (value: string) => void;
  // eslint-disable-next-line no-unused-vars
  onScriptTypeChange: (value: string) => void;
  // eslint-disable-next-line no-unused-vars
  onMaxDurationChange: (value: number) => void;
  // eslint-disable-next-line no-unused-vars
  onTopicChange?: (value: string) => void;
  // eslint-disable-next-line no-unused-vars
  onLanguageChange?: (value: string) => void;
  // eslint-disable-next-line no-unused-vars
  onAutoDiscoveryChange?: (value: boolean) => void;
  // Generation callbacks
  onGenerateScript?: () => void;
  onResearchTopic?: () => void;
  onGenerateFromResearch?: () => void;
  onClearError?: () => void;
}

const SCRIPT_TYPES = [
  { value: 'facts', label: 'Amazing Facts', icon: '🔍', description: 'Interesting and surprising facts' },
  { value: 'story', label: 'Storytelling', icon: '📚', description: 'Engaging narratives and stories' },
  { value: 'educational', label: 'Educational', icon: '🎓', description: 'Learning and how-to content' },
  { value: 'motivation', label: 'Motivational', icon: '💪', description: 'Inspiring and uplifting content' },
  { value: 'prayer', label: 'Prayer', icon: '🙏', description: 'Spiritual and prayer content' },
  { value: 'life_hacks', label: 'Life Hacks', icon: '💡', description: 'Useful tips and tricks' },
  { value: 'conspiracy', label: 'Mystery', icon: '🕵️', description: 'Mysterious and intriguing topics' },
  { value: 'shower_thoughts', label: 'Deep Thoughts', icon: '🤔', description: 'Philosophical and thought-provoking' },
  { value: 'reddit_stories', label: 'Real Stories', icon: '📖', description: 'Real-life experiences and stories' },
  { value: 'pov', label: 'POV Content', icon: '👤', description: 'Point of view scenarios' },
  { value: 'would_you_rather', label: 'Would You Rather', icon: '🤷', description: 'Choice-based content' },
  { value: 'before_you_die', label: 'Before You Die', icon: '⏳', description: 'Things to do before you die' },
  { value: 'dark_psychology', label: 'Psychology', icon: '🧠', description: 'Psychology insights' },
  { value: 'daily_news', label: 'Daily News', icon: '📰', description: 'Current news and events' },
];

const TOPIC_SUGGESTIONS = [
  'Climate Change Impact',
  'AI in Healthcare',
  'Space Exploration 2024',
  'Sustainable Technology',
  'Mental Health Awareness',
  'Cryptocurrency Trends',
  'Remote Work Future',
  'Renewable Energy Solutions'
];

// Helper function to estimate script duration
const estimateScriptDuration = (script: string): number => {
  if (!script.trim()) return 0;
  // Average speaking rate: ~2.5 words per second (150 words per minute)
  const words = script.trim().split(/\s+/).length;
  return Math.ceil(words / 2.5);
};

// Helper function to get word count
const getWordCount = (script: string): number => {
  if (!script.trim()) return 0;
  return script.trim().split(/\s+/).length;
};

const ScriptEditor: React.FC<ScriptEditorProps> = ({
  script,
  scriptType,
  maxDuration,
  topic = '',
  language = 'en',
  isGeneratingScript = false,
  isResearchingTopic = false,
  hasResearchResults = false,
  error = null,
  autoDiscovery = false,
  // Callbacks
  onScriptChange,
  onScriptTypeChange,
  onMaxDurationChange,
  onTopicChange,
  onLanguageChange,
  onAutoDiscoveryChange,
  onGenerateScript,
  onResearchTopic,
  onGenerateFromResearch,
  onClearError,
}) => {
  const estimatedDuration = estimateScriptDuration(script);
  const wordCount = getWordCount(script);
  const isOverDuration = estimatedDuration > maxDuration;

  // Auto-adjust maxDuration when script changes to match estimated duration
  useEffect(() => {
    if (script.trim() && estimatedDuration > 0) {
      const bufferDuration = Math.ceil(estimatedDuration * 1.1);
      const roundedDuration = Math.ceil(bufferDuration / 15) * 15;

      const shouldAdjust = (
        maxDuration < estimatedDuration ||
        maxDuration > roundedDuration
      );

      if (shouldAdjust) {
        const newDuration = Math.max(15, Math.min(900, roundedDuration));
        onMaxDurationChange(newDuration);
      }
    }
  }, [script, estimatedDuration, maxDuration, onMaxDurationChange]);

  const handleClearScript = useCallback(() => {
    onScriptChange('');
  }, [onScriptChange]);

  const handleTopicSuggestionClick = useCallback((suggestion: string) => {
    if (onTopicChange) {
      onTopicChange(suggestion);
    }
  }, [onTopicChange]);

  // Get language name for display
  const getLanguageName = (langCode: string) => {
    const supportedLanguages = getSupportedLanguages();
    const lang = supportedLanguages.find(l => l.code === langCode);
    return lang ? lang.name : 'English';
  };

  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }}>
      {/* Header */}
      <Box sx={{
        display: 'flex',
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        mb: 3,
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 2, sm: 0 }
      }}>
        <Typography
          variant="h6"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            fontSize: { xs: '1.1rem', sm: '1.25rem' }
          }}
        >
          <TextIcon color="primary" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
          Script Editor
        </Typography>
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          gap: { xs: 1, sm: 2 },
          flexWrap: 'wrap'
        }}>
          <Chip
            label={`${wordCount} words`}
            size="small"
            variant="outlined"
            color="primary"
            sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
          />
          <Chip
            label={`~${estimatedDuration}s`}
            size="small"
            variant="outlined"
            color={isOverDuration ? "error" : "success"}
            sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
          />
          {language && language !== 'en' && (
            <Tooltip title={`Script language: ${getLanguageName(language)}`}>
              <Chip
                label={getLanguageName(language)}
                size="small"
                variant="outlined"
                color="info"
                icon={<LanguageIcon sx={{ fontSize: { xs: '0.8rem', sm: '1rem' } }} />}
                sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
              />
            </Tooltip>
          )}
          {script && (
            <Tooltip title="Clear script">
              <IconButton
                onClick={handleClearScript}
                size="small"
                color="error"
                sx={{
                  p: { xs: 0.5, sm: 1 },
                  '& .MuiSvgIcon-root': { fontSize: { xs: '1rem', sm: '1.25rem' } }
                }}
              >
                <ClearIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={onClearError}
        >
          {error}
        </Alert>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* Auto Discovery Toggle */}
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={autoDiscovery}
                onChange={(e) => onAutoDiscoveryChange && onAutoDiscoveryChange(e.target.checked)}
                disabled={isGeneratingScript || isResearchingTopic}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingIcon fontSize="small" />
                <Typography
                  variant="body1"
                  sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                >
                  Auto-Discover Trending Topics
                </Typography>
              </Box>
            }
            sx={{ mb: 1 }}
          />
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              ml: { xs: 2, sm: 4 },
              mb: 2,
              fontSize: { xs: '0.8rem', sm: '0.875rem' },
              lineHeight: 1.4
            }}
          >
            AI will automatically find trending topics and generate scripts. You can still customize script type and duration below.
          </Typography>
        </Grid>

        {/* Topic Input (only if not auto-discovery) */}
        {!autoDiscovery && (
          <Grid item xs={12}>
            <TextField
              label="Topic"
              fullWidth
              variant="outlined"
              value={topic}
              onChange={(e) => onTopicChange && onTopicChange(e.target.value)}
              placeholder="Enter your topic (e.g., 'Amazing ocean facts', 'Climate change solutions')"
              helperText="Describe what you want your video to be about"
              disabled={isGeneratingScript || isResearchingTopic}
              InputProps={{
                startAdornment: <IdeaIcon sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />

            {/* Topic Suggestions */}
            <Box sx={{ mt: 2 }}>
              <Typography
                variant="body2"
                sx={{
                  mb: 1,
                  color: 'text.secondary',
                  fontSize: { xs: '0.8rem', sm: '0.875rem' }
                }}
              >
                Popular Topics:
              </Typography>
              <Box sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: { xs: 0.75, sm: 1 }
              }}>
                {TOPIC_SUGGESTIONS.map((suggestion) => (
                  <Chip
                    key={suggestion}
                    label={suggestion}
                    onClick={() => handleTopicSuggestionClick(suggestion)}
                    variant="outlined"
                    size="small"
                    sx={{
                      cursor: 'pointer',
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      height: { xs: '24px', sm: '28px' },
                      '&:hover': { backgroundColor: 'primary.light', color: 'white' },
                      '& .MuiChip-label': {
                        px: { xs: 1, sm: 1.5 }
                      }
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Grid>
        )}

        {/* Script Type Selection - Always available for customization */}
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Script Type</InputLabel>
            <Select
              value={scriptType}
              label="Script Type"
              onChange={(e) => onScriptTypeChange(e.target.value)}
              disabled={isGeneratingScript || isResearchingTopic}
              renderValue={(value) => (
                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  fontSize: { xs: '0.9rem', sm: '1rem' }
                }}>
                  <span style={{ fontSize: '1rem' }}>
                    {SCRIPT_TYPES.find(type => type.value === value)?.icon}
                  </span>
                  <Typography sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                    {SCRIPT_TYPES.find(type => type.value === value)?.label}
                  </Typography>
                </Box>
              )}
            >
              {SCRIPT_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <span style={{ fontSize: '1rem' }}>{type.icon}</span>
                    <Box>
                      <Typography
                        variant="body1"
                        sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                      >
                        {type.label}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                      >
                        {type.description}
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {autoDiscovery && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{
                mt: 0.5,
                display: 'block',
                fontSize: { xs: '0.7rem', sm: '0.75rem' }
              }}
            >
              This setting will be applied to the auto-generated script
            </Typography>
          )}
        </Grid>

        {/* Script Language */}
        {!autoDiscovery && (
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Script Language</InputLabel>
              <Select
                value={language || 'en'}
                label="Script Language"
                onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
                disabled={isGeneratingScript || isResearchingTopic}
                renderValue={(value) => (
                  <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    fontSize: { xs: '0.9rem', sm: '1rem' }
                  }}>
                    <LanguageIcon fontSize="small" />
                    <Typography sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                      {getLanguageName(value)}
                    </Typography>
                  </Box>
                )}
              >
                {getSupportedLanguages().map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                      <LanguageIcon fontSize="small" />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography
                          variant="body1"
                          sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                        >
                          {lang.name}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                        >
                          {lang.code.toUpperCase()}
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        )}

        {/* Max Duration Slider - Always available for customization */}
        <Grid item xs={12}>
          <Box sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimerIcon fontSize="small" />
              <Typography variant="body2">
                Max Video Duration: {maxDuration}s
              </Typography>
              <Tooltip title={autoDiscovery
                ? `This limits how long the auto-generated video should be.`
                : `This limits how long the video should be. ${script.trim() ? 'Auto-adjusted based on script length.' : 'This limits how long the AI-generated script should be.'}`
              }>
                <HelpIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
            {script.trim() && !isOverDuration && !autoDiscovery && (
              <Chip
                label="Auto-adjusted"
                size="small"
                color="success"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: '20px' }}
              />
            )}
            {autoDiscovery && (
              <Chip
                label="Applied to auto-topic"
                size="small"
                color="info"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: '20px' }}
              />
            )}
          </Box>
          <Slider
            value={maxDuration}
            onChange={(_, value) => onMaxDurationChange(Array.isArray(value) ? value[0] : value)}
            min={15}
            max={900}
            step={15}
            marks={[
              { value: 15, label: '15s' },
              { value: 60, label: '1m' },
              { value: 180, label: '3m' },
              { value: 300, label: '5m' },
              { value: 600, label: '10m' },
              { value: 900, label: '15m' },
            ]}
            sx={{ mt: 1 }}
            disabled={isGeneratingScript || isResearchingTopic}
          />
          {autoDiscovery && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              The auto-generated content will be tailored to fit within this duration
            </Typography>
          )}
        </Grid>

        {/* Action Buttons */}
        {!autoDiscovery && (
          <Grid item xs={12}>
            <Box sx={{
              display: 'flex',
              justifyContent: 'center',
              gap: { xs: 1.5, sm: 2 },
              my: 2,
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: 'center'
            }}>
              <Button
                variant="outlined"
                onClick={onGenerateScript}
                disabled={!topic.trim() || isGeneratingScript || isResearchingTopic}
                startIcon={isGeneratingScript && !hasResearchResults ? <CircularProgress size={20} /> : <AIIcon />}
                sx={{
                  minWidth: { xs: '100%', sm: 180 },
                  maxWidth: { xs: '300px', sm: 'none' },
                  fontSize: { xs: '0.9rem', sm: '1rem' },
                  py: { xs: 1, sm: 1.5 }
                }}
              >
                {isGeneratingScript && !hasResearchResults ? 'Generating...' : 'Generate Script'}
              </Button>

              {!hasResearchResults ? (
                <Button
                  variant="contained"
                  onClick={onResearchTopic}
                  disabled={!topic.trim() || isGeneratingScript || isResearchingTopic}
                  startIcon={isResearchingTopic ? <CircularProgress size={20} /> : <ResearchIcon />}
                  sx={{
                    minWidth: { xs: '100%', sm: 180 },
                    maxWidth: { xs: '300px', sm: 'none' },
                    backgroundColor: '#10b981',
                    '&:hover': { backgroundColor: '#059669' },
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                    py: { xs: 1, sm: 1.5 }
                  }}
                >
                  {isResearchingTopic ? 'Researching...' : 'Research Topic'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={onGenerateFromResearch}
                  disabled={isGeneratingScript || isResearchingTopic}
                  startIcon={isGeneratingScript && hasResearchResults ? <CircularProgress size={20} /> : <AIIcon />}
                  sx={{
                    minWidth: { xs: '100%', sm: 180 },
                    maxWidth: { xs: '300px', sm: 'none' },
                    backgroundColor: '#3b82f6',
                    '&:hover': { backgroundColor: '#2563eb' },
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                    py: { xs: 1, sm: 1.5 }
                  }}
                >
                  {isGeneratingScript && hasResearchResults ? 'Generating...' : 'Generate from Research'}
                </Button>
              )}
            </Box>

            {hasResearchResults && (
              <Box sx={{ textAlign: 'center', mt: 1 }}>
                <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                  <ResearchIcon fontSize="small" />
                  Research completed! Click "Generate from Research" to create your script.
                </Typography>
              </Box>
            )}
          </Grid>
        )}

        {/* Auto Discovery Message */}
        {autoDiscovery && (
          <Grid item xs={12}>
            <Card elevation={0} sx={{ backgroundColor: '#fef3c7', border: '1px solid #f59e0b', borderRadius: 2 }}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <TrendingIcon sx={{ fontSize: 48, color: '#f59e0b', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600, color: '#92400e', mb: 1 }}>
                  Auto-Discovery Mode Enabled
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  AI will automatically discover trending topics and generate the complete video when you click "Create Video" below.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  No manual script input required - the system will handle everything automatically.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Script Text Area */}
        {!autoDiscovery && (
          <Grid item xs={12}>
            <TextField
              label="Script"
              fullWidth
              multiline
              minRows={8}
              maxRows={20}
              variant="outlined"
              value={script}
              onChange={(e) => onScriptChange(e.target.value)}
              placeholder={autoDiscovery
                ? script
                  ? "Generated script (you can edit this if needed)"
                  : "Click 'Auto-Discover & Generate' above to create your script"
                : script
                  ? "Generated script (you can edit this if needed)"
                  : topic.trim()
                    ? "Click 'Generate Script' or 'Research & Generate' above"
                    : "Enter a topic above, or write your script manually here"
              }
              helperText={
                <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{script.length} characters • {wordCount} words</span>
                  <span style={{ color: isOverDuration ? '#ef4444' : 'inherit' }}>
                    Estimated duration: ~{estimatedDuration}s
                    {isOverDuration && " (exceeds max duration)"}
                  </span>
                </span>
              }
              disabled={isGeneratingScript || isResearchingTopic}
              error={isOverDuration}
              sx={{
                '& .MuiInputBase-root': {
                  fontFamily: 'monospace',
                  fontSize: '0.95rem',
                  lineHeight: 1.6,
                }
              }}
            />

            {/* Duration Progress Bar */}
            {script && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={Math.min((estimatedDuration / maxDuration) * 100, 100)}
                  color={isOverDuration ? "error" : "primary"}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}
          </Grid>
        )}

        {/* Script Tips */}
        {!autoDiscovery && (
          <Grid item xs={12}>
            <Card elevation={0} sx={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <IdeaIcon color="primary" fontSize="small" />
                  Script Writing Tips
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Keep sentences short and conversational • Use questions to engage viewers
                  • Include surprising facts or unexpected twists • End with a call-to-action
                  • Aim for {Math.round(maxDuration * 2.5)} words or less for {maxDuration}s duration
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ScriptEditor;