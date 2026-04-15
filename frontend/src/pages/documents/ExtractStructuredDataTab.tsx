import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Paper,
  LinearProgress,
  FormControlLabel,
  Switch,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Psychology as ExtractIcon,
  Schema as SchemaIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabContext } from './types';

interface ExtractStructuredDataTabProps {
  ctx: TabContext;
}

const ExtractStructuredDataTab: React.FC<ExtractStructuredDataTabProps> = ({ ctx }) => {
  const {
    extractLoading, setExtractLoading,
    extractResult, setExtractResult,
    extractError, setExtractError,
    extractJobStatus, setExtractJobStatus,
    extractJobProgress,
    extractPollingJobId, setExtractPollingJobId,
    pollExtractJobStatus,
    copyToClipboard,
    getFileIcon,
  } = ctx;

  // Local form state
  const [extractForm, setExtractForm] = useState({
    inputText: '',
    inputUrl: '',
    inputFile: null as File | null,
    extractionSchema: '{"entities": ["person", "organization", "location"], "relationships": ["works_for", "located_in"]}',
    extractionPrompt: 'Extract all people, organizations, and locations from the text. Also identify relationships between entities.',
    useCustomPrompt: false,
    model: 'gemini'
  });

  const handleExtractSubmit = async () => {
    if (!extractForm.inputText.trim() && !extractForm.inputUrl.trim() && !extractForm.inputFile) {
      setExtractError('Please provide text, URL, or file for data extraction');
      return;
    }

    setExtractLoading(true);
    setExtractError(null);
    setExtractResult(null);

    try {
      const response = await directApi.extractStructuredData({
        inputText: extractForm.inputText,
        inputUrl: extractForm.inputUrl,
        inputFile: extractForm.inputFile || undefined,
        extractionSchema: extractForm.extractionSchema,
        extractionPrompt: extractForm.extractionPrompt,
        useCustomPrompt: extractForm.useCustomPrompt,
        model: extractForm.model
      });

      if (response.success && response.data) {
        setExtractResult({ job_id: response.data.job_id, status: 'pending' });
        setExtractPollingJobId(response.data.job_id);
        setExtractJobStatus('pending');
        pollExtractJobStatus(response.data.job_id);
      } else {
        setExtractError(response.error || 'Failed to start data extraction');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setExtractError(errorMessage);
    } finally {
      setExtractLoading(false);
    }
  };

  const renderExtractionJobResult = () => {
    if (!extractResult && !extractError && !extractJobStatus) return null;

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          AI Data Extraction
          {extractJobStatus && extractJobStatus !== 'completed' && (
            <CircularProgress size={16} sx={{ ml: 1 }} />
          )}
        </Typography>

        {extractJobStatus && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Job ID: {extractPollingJobId}
            </Typography>
            <LinearProgress
              variant={extractJobStatus === 'completed' ? 'determinate' : 'indeterminate'}
              value={extractJobStatus === 'completed' ? 100 : undefined}
              sx={{ mb: 1, height: 4, borderRadius: 2 }}
            />
            <Typography variant="body2" sx={{
              color: extractJobStatus === 'completed' ? 'success.main' :
                extractJobStatus === 'failed' ? 'error.main' : 'info.main',
              fontSize: '0.75rem'
            }}>
              {extractJobProgress}
            </Typography>
          </Box>
        )}

        {extractError && (
          <Alert severity="error" sx={{ mb: 2, fontSize: '0.75rem' }}>
            {extractError}
          </Alert>
        )}

        {extractResult && extractJobStatus === 'completed' && extractResult.result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2, fontSize: '0.75rem' }}>
              Data extracted successfully!
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Extraction Summary:
              </Typography>
              <Paper sx={{ p: 1.5, bgcolor: '#f8fafc' }}>
                <Grid container spacing={1} sx={{ fontSize: '0.7rem' }}>
                  <Grid item xs={6}>
                    <strong>Entities:</strong> {extractResult.result.total_extractions}
                  </Grid>
                  <Grid item xs={6}>
                    <strong>Model:</strong> {extractResult.result.model_used}
                  </Grid>
                  <Grid item xs={6}>
                    <strong>Time:</strong> {extractResult.result.processing_time.toFixed(1)}s
                  </Grid>
                  <Grid item xs={6}>
                    <strong>Types:</strong> {Object.keys(extractResult.result.extracted_data).length}
                  </Grid>
                </Grid>
              </Paper>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                Extracted Data:
              </Typography>
              <Paper sx={{
                p: 1.5,
                bgcolor: '#f0f9ff',
                maxHeight: 150,
                overflow: 'auto',
                fontSize: '0.75rem'
              }}>
                <Typography variant="body2">
                  {Object.entries(extractResult.result.extracted_data).map(([category, entities]) => (
                    <Box key={category} sx={{ mb: 1 }}>
                      <strong>{category.toUpperCase()} ({entities.length}):</strong>
                      <Box sx={{ ml: 1 }}>
                        {entities.slice(0, 3).map((entity, idx) => (
                          <Box key={idx}>
                            - {entity.text || entity.value}
                          </Box>
                        ))}
                        {entities.length > 3 && `... and ${entities.length - 3} more`}
                      </Box>
                    </Box>
                  ))}
                </Typography>
              </Paper>
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => copyToClipboard(JSON.stringify(extractResult.result?.extracted_data, null, 2) || '')}
                  sx={{ fontSize: '0.7rem', px: 1 }}
                >
                  Copy JSON
                </Button>
              </Box>
            </Box>
          </Box>
        )}

        {extractResult && !extractResult.result && extractJobStatus !== 'completed' && (
          <Box>
            <Alert severity="info" sx={{ mb: 2, fontSize: '0.75rem' }}>
              Data extraction job created successfully!
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              Job ID: <code style={{ padding: '1px 3px', backgroundColor: '#f1f3f4', borderRadius: '2px', fontSize: '0.7rem' }}>
                {extractResult.job_id}
              </code>
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Grid container spacing={{ xs: 2, sm: 3 }}>
      <Grid item xs={12} lg={8}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0' }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <ExtractIcon />
              Extract Structured Data with AI
            </Typography>

            <Grid container spacing={3}>
              {/* Text Input */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Input Text (Optional)"
                  placeholder="Paste your text here to extract structured information..."
                  value={extractForm.inputText}
                  onChange={(e) => setExtractForm(prev => ({ ...prev, inputText: e.target.value }))}
                  helperText="Enter text directly for immediate processing"
                />
              </Grid>

              {/* Divider */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, my: 1 }}>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                    OR
                  </Typography>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                </Box>
              </Grid>

              {/* URL Input */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Document URL (Optional)"
                  placeholder="https://example.com/document.pdf"
                  value={extractForm.inputUrl}
                  onChange={(e) => setExtractForm(prev => ({ ...prev, inputUrl: e.target.value }))}
                  helperText="Extract data from a web document"
                />
              </Grid>

              {/* Divider */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, my: 1 }}>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                    OR
                  </Typography>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                </Box>
              </Grid>

              {/* File Upload */}
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  component="label"
                  fullWidth
                  startIcon={<UploadIcon />}
                  sx={{ mb: 2, py: 2 }}
                >
                  {extractForm.inputFile ? extractForm.inputFile.name : 'Choose File for Data Extraction'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf,.docx,.doc,.txt,.html,.htm"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setExtractForm(prev => ({ ...prev, inputFile: file }));
                      }
                    }}
                  />
                </Button>
                {extractForm.inputFile && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    {getFileIcon(extractForm.inputFile.name)}
                    <Typography variant="body2">
                      {extractForm.inputFile.name} ({(extractForm.inputFile.size / 1024 / 1024).toFixed(2)} MB)
                    </Typography>
                  </Box>
                )}
              </Grid>

              {/* Extraction Configuration */}
              <Grid item xs={12}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SchemaIcon />
                      Extraction Configuration
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={extractForm.useCustomPrompt}
                              onChange={(e) => setExtractForm(prev => ({ ...prev, useCustomPrompt: e.target.checked }))}
                            />
                          }
                          label="Use Custom Extraction Prompt"
                        />
                      </Grid>

                      {extractForm.useCustomPrompt ? (
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            multiline
                            rows={3}
                            label="Custom Extraction Prompt"
                            value={extractForm.extractionPrompt}
                            onChange={(e) => setExtractForm(prev => ({ ...prev, extractionPrompt: e.target.value }))}
                            helperText="Describe what specific information you want to extract"
                          />
                        </Grid>
                      ) : (
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            multiline
                            rows={3}
                            label="JSON Schema (Optional)"
                            value={extractForm.extractionSchema}
                            onChange={(e) => setExtractForm(prev => ({ ...prev, extractionSchema: e.target.value }))}
                            helperText='Define structure like: {"entities": ["person", "organization"], "attributes": ["name", "title"]}'
                          />
                        </Grid>
                      )}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>

              {/* Extract Button */}
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={extractLoading ? <CircularProgress size={20} /> : <ExtractIcon />}
                  onClick={handleExtractSubmit}
                  disabled={extractLoading || (!extractForm.inputText.trim() && !extractForm.inputUrl.trim() && !extractForm.inputFile)}
                  sx={{ px: 4 }}
                >
                  {extractLoading ? 'Extracting...' : 'Extract Structured Data'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} lg={4}>
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', height: 'fit-content' }}>
          <CardContent>
            {renderExtractionJobResult() || (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  What is Langextract?
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Google's Langextract extracts structured information from unstructured text using AI:
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Chip label="Named Entities" size="small" color="primary" sx={{ m: 0.5 }} />
                  <Chip label="Relationships" size="small" color="secondary" sx={{ m: 0.5 }} />
                  <Chip label="Attributes" size="small" color="success" sx={{ m: 0.5 }} />
                  <Chip label="Source Grounding" size="small" color="info" sx={{ m: 0.5 }} />
                </Box>

                <Typography variant="h6" sx={{ mb: 2 }}>
                  Example Use Cases
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setExtractForm(prev => ({
                      ...prev,
                      inputText: 'John Smith works as a Senior Engineer at Google Inc. in Mountain View, California. He previously worked at Apple Inc.',
                      extractionSchema: '{"entities": ["person", "organization", "location", "job_title"], "relationships": ["works_at", "previously_worked_at"]}'
                    }))}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Resume Analysis
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setExtractForm(prev => ({
                      ...prev,
                      inputText: 'Apple Inc. reported Q4 revenue of $94.9B, up 6% YoY. iPhone sales were $39.3B, while Services reached $22.3B.',
                      extractionSchema: '{"entities": ["company", "financial_metrics", "products"], "attributes": ["revenue", "growth_rate", "time_period"]}'
                    }))}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Financial Reports
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setExtractForm(prev => ({
                      ...prev,
                      inputText: 'Dr. Sarah Johnson published a paper on machine learning in Nature journal. She collaborated with researchers from Stanford University and MIT.',
                      extractionSchema: '{"entities": ["person", "publication", "institution"], "relationships": ["published", "collaborated_with"]}'
                    }))}
                    sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    Research Papers
                  </Button>
                </Box>

                <Typography variant="h6" sx={{ mb: 2 }}>
                  AI Models
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip icon={<ExtractIcon />} label="Gemini (Primary)" color="primary" variant="outlined" size="small" />
                  <Chip icon={<ExtractIcon />} label="OpenAI (Fallback)" color="secondary" variant="outlined" size="small" />
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default ExtractStructuredDataTab;
