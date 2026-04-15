import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Description as DocumentIcon,
  PictureAsPdf as PdfIcon,
  Article as WordIcon,
  TableChart as ExcelIcon,
  Image as ImageIcon,
  Psychology as ExtractIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { directApi } from '../../utils/api';
import { TabPanelProps, TabContext, DocumentConversionResult, LangextractConversionResult } from './types';

import ConvertToMarkdownTab from './ConvertToMarkdownTab';
import ExtractStructuredDataTab from './ExtractStructuredDataTab';
import UrlToMarkdownTab from './UrlToMarkdownTab';

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Documents: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  // Document conversion shared state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DocumentConversionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<'pending' | 'processing' | 'completed' | 'failed' | null>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Langextract shared state
  const [extractLoading, setExtractLoading] = useState(false);
  const [extractResult, setExtractResult] = useState<LangextractConversionResult | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [extractJobStatus, setExtractJobStatus] = useState<'pending' | 'processing' | 'completed' | 'failed' | null>(null);
  const [extractJobProgress, setExtractJobProgress] = useState<string>('');
  const [extractPollingJobId, setExtractPollingJobId] = useState<string | null>(null);

  // Get file icon based on extension
  const getFileIcon = (filename?: string) => {
    if (!filename) return <DocumentIcon />;

    const ext = filename.toLowerCase().split('.').pop();
    switch (ext) {
      case 'pdf':
        return <PdfIcon color="error" />;
      case 'docx':
      case 'doc':
        return <WordIcon color="primary" />;
      case 'xlsx':
      case 'xls':
        return <ExcelIcon color="success" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
        return <ImageIcon color="secondary" />;
      default:
        return <DocumentIcon />;
    }
  };

  // Job status polling function
  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const statusResponse = await directApi.getJobStatus(jobId);

        if (!statusResponse.success || !statusResponse.data) {
          throw new Error(statusResponse.error || 'Failed to get job status');
        }

        const job = statusResponse.data;
        const status = job.status;
        const jobResult = job.result;
        const jobError = job.error;

        setJobStatus(status);

        if (status === 'completed') {
          setJobProgress('Document conversion completed successfully!');
          setResult({
            job_id: jobId,
            status: 'completed',
            result: jobResult,
            error: null
          });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Document conversion failed');
          setError(jobError || 'Document conversion failed');
          setLoading(false);
          return;
        } else if (status === 'processing') {
          setJobProgress(`Processing document... (${attempts}/${maxAttempts})`);
        } else {
          setJobProgress(`Queued... (${attempts}/${maxAttempts})`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setError('Job polling timeout. Please check status manually.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setError('Failed to check job status');
          setLoading(false);
        }
      }
    };

    poll();
  };

  // Langextract job status polling function
  const pollExtractJobStatus = async (jobId: string) => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const statusResponse = await directApi.getJobStatus(jobId);

        if (!statusResponse.success || !statusResponse.data) {
          throw new Error(statusResponse.error || 'Failed to get job status');
        }

        const job = statusResponse.data;
        const status = job.status;
        const jobResult = job.result;
        const jobError = job.error;

        setExtractJobStatus(status);

        if (status === 'completed') {
          setExtractJobProgress('Data extraction completed successfully!');
          setExtractResult({
            job_id: jobId,
            status: 'completed',
            result: jobResult,
            error: null
          });
          setExtractLoading(false);
          return;
        } else if (status === 'failed') {
          setExtractJobProgress('Data extraction failed');
          setExtractError(jobError || 'Data extraction failed');
          setExtractLoading(false);
          return;
        } else if (status === 'processing') {
          setExtractJobProgress(`Extracting structured data... (${attempts}/${maxAttempts})`);
        } else {
          setExtractJobProgress(`Queued... (${attempts}/${maxAttempts})`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setExtractError('Job polling timeout. Please check status manually.');
          setExtractLoading(false);
        }
      } catch (err) {
        console.error('Extract polling error:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setExtractError('Failed to check job status');
          setExtractLoading(false);
        }
      }
    };

    poll();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const ctx: TabContext = {
    loading, setLoading,
    result, setResult,
    error, setError,
    jobStatus, setJobStatus,
    jobProgress, setJobProgress,
    pollingJobId, setPollingJobId,
    copied, setCopied,
    extractLoading, setExtractLoading,
    extractResult, setExtractResult,
    extractError, setExtractError,
    extractJobStatus, setExtractJobStatus,
    extractJobProgress, setExtractJobProgress,
    extractPollingJobId, setExtractPollingJobId,
    pollJobStatus,
    pollExtractJobStatus,
    copyToClipboard,
    downloadMarkdown,
    getFileIcon,
  };

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      pb: 8
    }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 4 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            color: '#1a202c',
            fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
          }}
        >
          Document Processor
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '0.95rem', sm: '1.1rem' } }}
        >
          Convert PDF, Word, Excel, and other documents to clean Markdown format.
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="document processing tabs"
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Convert to Markdown" icon={<DocumentIcon />} id="document-tab-0" />
          <Tab label="URL to Markdown" icon={<LinkIcon />} id="document-tab-1" />
          <Tab label="Extract Structured Data" icon={<ExtractIcon />} id="document-tab-2" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <ConvertToMarkdownTab ctx={ctx} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <UrlToMarkdownTab ctx={ctx} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ExtractStructuredDataTab ctx={ctx} />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Documents;
