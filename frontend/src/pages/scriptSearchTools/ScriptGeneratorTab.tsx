import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  AutoMode as AutoTopicIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const ScriptGeneratorTab: React.FC<Props> = ({ ctx }) => {
  const { loading, setLoading, setErrors, results, setResults, pollJobStatus, renderJobResult } = ctx;

  const [scriptGenForm, setScriptGenForm] = useState({
    topic: '',
    script_type: 'facts',
    language: 'en',
    target_duration: 60,
    auto_topic: false,
    style: 'engaging'
  });

  const handleScriptGeneration = async () => {
    if (!scriptGenForm.auto_topic && !scriptGenForm.topic.trim()) {
      setErrors(prev => ({ ...prev, scriptgen: 'Topic is required (or enable auto-topic discovery)' }));
      return;
    }

    setLoading(prev => ({ ...prev, scriptgen: true }));
    setErrors(prev => ({ ...prev, scriptgen: null }));
    setResults(prev => ({ ...prev, scriptgen: null }));

    try {
      const response = await directApi.post('/ai/script/generate', scriptGenForm);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id, 'scriptgen');
      } else {
        setErrors(prev => ({ ...prev, scriptgen: 'Failed to create script generation job' }));
        setLoading(prev => ({ ...prev, scriptgen: false }));
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setErrors(prev => ({ ...prev, scriptgen: errorMessage }));
      setLoading(prev => ({ ...prev, scriptgen: false }));
    }
  };

  return (
    <>
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <AIIcon color="primary" />
                AI Script Generator
              </Typography>

              <Grid container spacing={{ xs: 2, sm: 3 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Topic"
                    placeholder="Enter your video topic or concept..."
                    value={scriptGenForm.topic}
                    onChange={(e) => setScriptGenForm({ ...scriptGenForm, topic: e.target.value })}
                    helperText={scriptGenForm.auto_topic ? "Optional when auto-topic is enabled" : "Describe what you want your video to be about"}
                  />
                </Grid>

                <Grid item xs={12} sm={6} lg={4}>
                  <FormControl fullWidth>
                    <InputLabel>Script Type</InputLabel>
                    <Select
                      value={scriptGenForm.script_type}
                      label="Script Type"
                      onChange={(e) => setScriptGenForm({ ...scriptGenForm, script_type: e.target.value })}
                    >
                      <MenuItem value="facts">Interesting Facts</MenuItem>
                      <MenuItem value="story">Storytelling</MenuItem>
                      <MenuItem value="educational">Educational</MenuItem>
                      <MenuItem value="motivation">Motivational</MenuItem>
                      <MenuItem value="pov">Point of View (POV)</MenuItem>
                      <MenuItem value="conspiracy">Mystery/Conspiracy</MenuItem>
                      <MenuItem value="life_hacks">Life Hacks</MenuItem>
                      <MenuItem value="would_you_rather">Would You Rather</MenuItem>
                      <MenuItem value="before_you_die">Before You Die</MenuItem>
                      <MenuItem value="life_wisdom">Life Wisdom</MenuItem>
                      <MenuItem value="dark_psychology">Psychology Insights</MenuItem>
                      <MenuItem value="reddit_stories">Personal Stories</MenuItem>
                      <MenuItem value="shower_thoughts">Shower Thoughts</MenuItem>
                      <MenuItem value="daily_news">Daily News</MenuItem>
                      <MenuItem value="prayer">Spiritual/Prayer</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6} lg={4}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={scriptGenForm.language}
                      label="Language"
                      onChange={(e) => setScriptGenForm({ ...scriptGenForm, language: e.target.value })}
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="es">Spanish</MenuItem>
                      <MenuItem value="fr">French</MenuItem>
                      <MenuItem value="de">German</MenuItem>
                      <MenuItem value="it">Italian</MenuItem>
                      <MenuItem value="pt">Portuguese</MenuItem>
                      <MenuItem value="ru">Russian</MenuItem>
                      <MenuItem value="zh">Chinese</MenuItem>
                      <MenuItem value="ja">Japanese</MenuItem>
                      <MenuItem value="ko">Korean</MenuItem>
                      <MenuItem value="ar">Arabic</MenuItem>
                      <MenuItem value="hi">Hindi</MenuItem>
                      <MenuItem value="tr">Turkish</MenuItem>
                      <MenuItem value="pl">Polish</MenuItem>
                      <MenuItem value="nl">Dutch</MenuItem>
                      <MenuItem value="sv">Swedish</MenuItem>
                      <MenuItem value="da">Danish</MenuItem>
                      <MenuItem value="no">Norwegian</MenuItem>
                      <MenuItem value="fi">Finnish</MenuItem>
                      <MenuItem value="cs">Czech</MenuItem>
                      <MenuItem value="hu">Hungarian</MenuItem>
                      <MenuItem value="ro">Romanian</MenuItem>
                      <MenuItem value="bg">Bulgarian</MenuItem>
                      <MenuItem value="hr">Croatian</MenuItem>
                      <MenuItem value="sk">Slovak</MenuItem>
                      <MenuItem value="sl">Slovenian</MenuItem>
                      <MenuItem value="et">Estonian</MenuItem>
                      <MenuItem value="lv">Latvian</MenuItem>
                      <MenuItem value="lt">Lithuanian</MenuItem>
                      <MenuItem value="mt">Maltese</MenuItem>
                      <MenuItem value="cy">Welsh</MenuItem>
                      <MenuItem value="ga">Irish</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6} lg={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Target Duration (seconds)"
                    value={scriptGenForm.target_duration}
                    onChange={(e) => setScriptGenForm({ ...scriptGenForm, target_duration: parseInt(e.target.value) })}
                    inputProps={{ min: 15, max: 300 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scriptGenForm.auto_topic}
                          onChange={(e) => setScriptGenForm({ ...scriptGenForm, auto_topic: e.target.checked })}
                          color="primary"
                        />
                      }
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <AutoTopicIcon fontSize="small" />
                          <Typography variant="body2">
                            Auto-Topic Discovery
                          </Typography>
                        </Box>
                      }
                    />
                    <Typography variant="caption" color="text.secondary">
                      Automatically find trending topics based on script type
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Button
                variant="contained"
                size="large"
                startIcon={loading.scriptgen ? <CircularProgress size={20} /> : <AIIcon />}
                onClick={handleScriptGeneration}
                disabled={loading.scriptgen || (!scriptGenForm.auto_topic && !scriptGenForm.topic.trim())}
                sx={{ mt: 3, px: 4 }}
              >
                {loading.scriptgen ? 'Generating...' : 'Generate Script'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Script Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label="AI-Powered Content" variant="outlined" size="small" />
                <Chip label="15 Script Types" variant="outlined" size="small" />
                <Chip label="Optimized for TTS" variant="outlined" size="small" />
                <Chip label="Viral Content Focus" variant="outlined" size="small" />
                <Chip label="Duration Targeting" variant="outlined" size="small" />
                <Chip label="POV & Psychology Content" variant="outlined" size="small" />
                <Chip label="30+ Languages" variant="outlined" size="small" />
                <Chip label="Auto-Topic Discovery" variant="outlined" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {renderJobResult('scriptgen', results.scriptgen, <AIIcon />)}
    </>
  );
};

export default ScriptGeneratorTab;
