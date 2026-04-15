import { useState, useCallback } from 'react';
import { directApi } from '../utils/api';
import { JobResult, JobType, JobStatus } from '../types/pollinations';

export const useJobPolling = () => {
  const [result, setResult] = useState<JobResult | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transformJobResult = useCallback((jobResult: unknown, jobType: JobType): JobResult['result'] => {
    // Transform the result based on job type to match expected UI structure
    let transformedResult: JobResult['result'] = jobResult as JobResult['result'];

    if (jobType === 'chat' && jobResult) {
      // Cast to handle dynamic API response structure
      const chatResult = jobResult as Record<string, unknown>;
      transformedResult = {
        response: jobResult as Record<string, unknown>,
        assistant_message: (chatResult.choices as Array<{ message?: { content?: string } }>)?.[0]?.message?.content ||
          (chatResult.assistant_message as string) ||
          (chatResult.text as string) || '',
        model_used: (chatResult.model_used as string) || (chatResult.model as string) || 'unknown',
        generation_time: (chatResult.generation_time as number) || (chatResult._metadata as { generation_time?: number })?.generation_time || 0,
        message_count: (chatResult.message_count as number) || 1,
        has_tool_calls: (chatResult.has_tool_calls as boolean) || false
      };
    } else if (jobType === 'text' && jobResult) {
      // Cast to handle dynamic API response structure
      const textResult = jobResult as Record<string, unknown>;
      transformedResult = {
        text: (textResult.text as string) || (textResult.content as string) || (textResult.assistant_message as string) || '',
        response: jobResult as Record<string, unknown>,
        model_used: (textResult.model_used as string) || (textResult.model as string) || 'unknown',
        generation_time: (textResult.generation_time as number) || (textResult._metadata as { generation_time?: number })?.generation_time || 0,
        prompt: (textResult.prompt as string) || '',
        character_count: ((textResult.text as string) || (textResult.content as string) || '').length
      };
    }
    // Vision results are typically already in the correct format

    return transformedResult;
  }, []);

  const pollJobStatus = useCallback(async (jobId: string, jobType: JobType) => {
    const maxAttempts = 60; // 5 minutes max
    const maxConsecutiveErrors = 5; // Stop after 5 consecutive errors
    let attempts = 0;
    let consecutiveErrors = 0;

    const poll = async () => {
      try {
        attempts++;
        // Use unified job status endpoint instead of provider-specific endpoints
        const statusResponse = await directApi.getJobStatus(jobId);

        if (!statusResponse.success) {
          const errorMessage = statusResponse.error || 'Failed to get job status';
          // Check for terminal error conditions — stop polling immediately
          if (errorMessage.includes('404') || errorMessage.includes('not found')) {
            setError('❓ Job not found. It may have expired or been removed.');
            setLoading(false);
            return;
          }
          if (errorMessage.includes('failed') || errorMessage.includes('error')) {
            setError(`⚠️ ${errorMessage}`);
            setLoading(false);
            return;
          }
          // Transient errors — retry
          throw new Error(`⚠️ ${errorMessage}`);
        }

        consecutiveErrors = 0; // Reset on successful API call

        const status = statusResponse.data?.status;
        const jobResult = statusResponse.data?.result;
        const jobError = statusResponse.data?.error;

        setJobStatus(status as JobStatus);

        if (status === 'completed') {
          setJobProgress('Processing completed successfully!');
          const transformedResult = transformJobResult(jobResult, jobType);
          setResult({ job_id: jobId, result: transformedResult, status: 'completed' });
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Processing failed');
          // Enhanced error message handling for failed jobs
          let enhancedError = jobError || 'Processing failed';
          if (jobError) {
            if (jobError.includes('502') || jobError.includes('Bad Gateway')) {
              enhancedError = '🌐 The Pollinations API is temporarily unavailable. This is usually a temporary issue - please try again in a few minutes.';
            } else if (jobError.includes('503') || jobError.includes('service temporarily unavailable')) {
              enhancedError = '🔧 The service is temporarily unavailable due to high demand or maintenance. Please try again later.';
            } else if (jobError.includes('timeout')) {
              enhancedError = '⏱️ The request timed out due to high API load. Please try again.';
            } else if (jobError.includes('rate limit')) {
              enhancedError = '⏰ Rate limit exceeded. Please wait a moment and try again.';
            } else if (jobError.includes('retry_exhausted')) {
              enhancedError = '🔄 The request failed after multiple retry attempts. The API may be experiencing issues - please try again later.';
            } else {
              enhancedError = `⚠️ ${jobError}`;
            }
          }
          setError(enhancedError);
          setLoading(false);
          return;
        } else if (status === 'processing') {
          setJobProgress(`Processing with Pollinations AI... (${attempts}/${maxAttempts})`);
        } else {
          setJobProgress(`Queued... (${attempts}/${maxAttempts})`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setError('Job polling timeout. Please check status manually.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Pollinations polling error:', err);
        consecutiveErrors++;

        if (consecutiveErrors >= maxConsecutiveErrors) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          if (errorMsg.includes('NetworkError') || errorMsg.includes('Failed to fetch')) {
            setError('🔌 Network error: Please check your internet connection and try again.');
          } else if (errorMsg.includes('service temporarily unavailable') || errorMsg.includes('502')) {
            setError('🌐 The API service is temporarily unavailable. Please try again later.');
          } else {
            setError(`💥 ${errorMsg}`);
          }
          setLoading(false);
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          setError(`💥 ${errorMsg}`);
          setLoading(false);
        }
      }
    };

    poll();
  }, [transformJobResult]);

  const resetState = useCallback(() => {
    setResult(null);
    setError(null);
    setJobStatus(null);
    setJobProgress('');
    setPollingJobId(null);
    setLoading(false);
  }, []);

  const startJob = useCallback((jobId: string, jobType: JobType, progressMessage: string) => {
    setPollingJobId(jobId);
    setJobStatus('pending');
    setJobProgress(progressMessage);
    pollJobStatus(jobId, jobType);
  }, [pollJobStatus]);

  return {
    result,
    jobStatus,
    jobProgress,
    pollingJobId,
    loading,
    error,
    setResult,
    setLoading,
    setError,
    startJob,
    resetState
  };
};