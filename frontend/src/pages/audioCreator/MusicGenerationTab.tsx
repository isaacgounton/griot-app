import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  MusicNote as MusicIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface Props {
  ctx: TabContext;
}

const MusicGenerationTab: React.FC<Props> = ({ ctx }) => {
  const {
    loading, setLoading, setError, setResult,
    setJobStatus, setJobProgress, setPollingJobId,
    pollJobStatus, renderJobResult
  } = ctx;

  const [musicForm, setMusicForm] = useState({
    description: '',
    duration: 8,
    model_size: 'small',
    output_format: 'wav'
  });

  const modelSizeOptions = ['small'];
  const musicFormatOptions = ['wav', 'mp3'];

  const handleMusicSubmit = async () => {
    if (!musicForm.description.trim()) {
      setError('Music description is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await directApi.post('/audio/music', musicForm);
      if (response.data && response.data.job_id) {
        setResult(response.data);
        setPollingJobId(response.data.job_id);
        setJobStatus('pending');
        setJobProgress('Job created, starting music generation...');
        pollJobStatus(response.data.job_id);
      } else {
        setError('Failed to generate music');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <MusicIcon color="primary" />
              Music Generation Configuration
            </Typography>

            <Grid container spacing={{ xs: 2, sm: 3 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Music Description"
                  placeholder="Describe the music you want to generate..."
                  value={musicForm.description}
                  onChange={(e) => setMusicForm({ ...musicForm, description: e.target.value })}
                  helperText={`${musicForm.description.length}/500 characters. Be specific about genre, instruments, mood, and style.`}
                  error={musicForm.description.length > 500}
                  inputProps={{ maxLength: 500 }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <Typography gutterBottom>Duration: {musicForm.duration}s</Typography>
                <Slider
                  value={musicForm.duration}
                  onChange={(_, value) => setMusicForm({ ...musicForm, duration: value as number })}
                  min={1}
                  max={30}
                  step={1}
                  marks={[
                    { value: 5, label: '5s' },
                    { value: 15, label: '15s' },
                    { value: 30, label: '30s' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Model Size</InputLabel>
                  <Select
                    value={musicForm.model_size}
                    label="Model Size"
                    onChange={(e) => setMusicForm({ ...musicForm, model_size: e.target.value })}
                  >
                    {modelSizeOptions.map((size) => (
                      <MenuItem key={size} value={size}>
                        {size.charAt(0).toUpperCase() + size.slice(1)} - Meta MusicGen Stereo
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Output Format</InputLabel>
                  <Select
                    value={musicForm.output_format}
                    label="Output Format"
                    onChange={(e) => setMusicForm({ ...musicForm, output_format: e.target.value })}
                  >
                    {musicFormatOptions.map((format) => (
                      <MenuItem key={format} value={format}>
                        {format.toUpperCase()} {format === 'wav' ? '(High quality, 32kHz stereo)' : '(Compressed, smaller file size)'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleMusicSubmit}
              disabled={loading || !musicForm.description.trim()}
              fullWidth
              sx={{
                mt: 3,
                px: 4,
                maxWidth: { sm: '300px' },
                alignSelf: { sm: 'flex-start' }
              }}
            >
              {loading ? 'Generating...' : 'Generate Music'}
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            {renderJobResult(1) || (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Music Examples
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Click any example to use it. Be specific about genre, instruments, mood, and tempo for best results.
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {[
                    'lo-fi hip hop with mellow beats and vinyl crackle',
                    'upbeat electronic dance music with synthesizers and bass drops',
                    'acoustic guitar melody in major key with gentle strumming',
                    'orchestral music with strings and piano, romantic style',
                    'smooth jazz with saxophone solo and walking bassline',
                    'calming music with soft piano and gentle strings, peaceful atmosphere',
                    'high-energy music with fast tempo and driving rhythm',
                    'solo piano piece with expressive dynamics and emotional phrasing'
                  ].map((example, index) => (
                    <Chip
                      key={index}
                      label={example}
                      variant="outlined"
                      onClick={() => setMusicForm({ ...musicForm, description: example })}
                      sx={{
                        cursor: 'pointer',
                        justifyContent: 'flex-start',
                        height: 'auto',
                        '& .MuiChip-label': {
                          whiteSpace: 'normal',
                          textAlign: 'left'
                        }
                      }}
                    />
                  ))}
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default MusicGenerationTab;
