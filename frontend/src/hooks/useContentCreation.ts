import { useState, useCallback, useEffect } from 'react';
import { directApi } from '../utils/api';
import {
  VideoCreationRequest,
  VideoCreationResult,
  TopicResearchRequest,
  TopicResearchResult,
  ContentCreationJobResult,
  ContentCreationJobStatus,
  VoiceInfo,
  VoiceProviderInfo
} from '../types/contentCreation';



// Persistent job storage helpers
const STORAGE_KEY = 'griot_video_jobs';

interface PersistentJob {
  jobId: string;
  endpoint: string;
  type: 'video' | 'research';
  timestamp: number;
  progress?: string;
  status?: ContentCreationJobStatus;
}

const savePersistentJob = (job: PersistentJob) => {
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as PersistentJob[];
    const filtered = existing.filter(j => j.jobId !== job.jobId);
    filtered.push(job);
    // Keep only last 10 jobs to prevent storage bloat
    const limited = filtered.slice(-10);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(limited));
  } catch (error) {
    console.warn('Failed to save persistent job:', error);
  }
};

const removePersistentJob = (jobId: string) => {
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as PersistentJob[];
    const filtered = existing.filter(j => j.jobId !== jobId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.warn('Failed to remove persistent job:', error);
  }
};

const getActivePersistentJobs = (): PersistentJob[] => {
  try {
    const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as PersistentJob[];
    // Filter jobs older than 2 hours
    const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000);
    return jobs.filter(job => job.timestamp > twoHoursAgo && (!job.status || !['completed', 'failed'].includes(job.status)));
  } catch (error) {
    console.warn('Failed to get persistent jobs:', error);
    return [];
  }
};

const clearAllPersistentJobs = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    // Successfully cleared persistent jobs
  } catch (error) {
    console.warn('Failed to clear persistent jobs:', error);
  }
};

const clearOrphanedJobs = async (): Promise<void> => {
  try {
    const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as PersistentJob[];
    const validJobs: PersistentJob[] = [];

    for (const job of jobs) {
      try {
        // Try to check if job exists on server using unified endpoint
        const response = await directApi.get(`/jobs/${job.jobId}/status`);
        if (response.status === 200) {
          // Job exists, keep it
          validJobs.push(job);
        }
      } catch (error) {
        // Job doesn't exist, skip it (will be removed)
        // Job doesn't exist on server, will be removed
      }
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(validJobs));
    // Cleaned up orphaned jobs from localStorage
  } catch (error) {
    console.warn('Failed to clear orphaned jobs:', error);
  }
};

export const useVideoCreation = () => {
  const [result, setResult] = useState<ContentCreationJobResult | null>(null);
  const [jobStatus, setJobStatus] = useState<ContentCreationJobStatus | null>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isResumedJob, setIsResumedJob] = useState(false);

  const pollJobStatus = useCallback(async (jobId: string) => {
    const maxAttempts = 30; // 30 minutes max (30 attempts × 60 seconds = 30 minutes)
    const maxConsecutiveErrors = 5; // Stop after 5 consecutive errors
    let attempts = 0;
    let consecutiveErrors = 0;

    const poll = async () => {
      try {
        attempts++;
        // Always use the unified job status endpoint, not the service-specific endpoint
        const response = await directApi.get(`/jobs/${jobId}/status`);
        const responseData = response.data;
        consecutiveErrors = 0; // Reset on successful API call

        // Handle both direct response format and wrapped format
        let status: ContentCreationJobStatus;
        let jobResult: unknown;
        let jobError: string | undefined;

        if (responseData.success === false) {
          // Wrapped error format — check if it contains a job failure status
          const errorMessage = responseData.error || 'Failed to get job status';
          // Check if the error itself indicates the job failed
          if (errorMessage.includes('failed') || errorMessage.includes('error')) {
            setJobProgress('Video processing failed');
            setError(`⚠️ ${errorMessage}`);
            removePersistentJob(jobId);
            setLoading(false);
            return;
          }
          if (errorMessage.includes('404') || errorMessage.includes('not found')) {
            setError('❓ Job not found. It may have expired or been removed.');
            removePersistentJob(jobId);
            setLoading(false);
            return;
          }
          // Transient errors — retry a few times
          throw new Error(`⚠️ ${errorMessage}`);
        } else if (responseData.success && responseData.data) {
          // Wrapped success format
          status = responseData.data.status as ContentCreationJobStatus;
          jobResult = responseData.data.result;
          jobError = responseData.data.error;
        } else if (responseData.status) {
          // Direct format from backend
          status = responseData.status as ContentCreationJobStatus;
          jobResult = responseData.result;
          jobError = responseData.error;
        } else {
          throw new Error('Invalid response format from job status endpoint');
        }

        setJobStatus(status);

        // Update persistent job status
        if (pollingJobId) {
          const activeJobs = getActivePersistentJobs();
          const currentJob = activeJobs.find(j => j.jobId === pollingJobId);
          if (currentJob) {
            currentJob.status = status;
            currentJob.progress = jobProgress;
            savePersistentJob(currentJob);
          }
        }

        if (status === 'completed') {
          setJobProgress('Video processing completed successfully!');
          setResult({
            job_id: jobId,
            status: 'completed',
            result: jobResult as VideoCreationResult | TopicResearchResult
          });
          // Remove completed job from persistent storage
          removePersistentJob(jobId);
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Video processing failed');
          let enhancedError = jobError || 'Processing failed';
          if (jobError) {
            if (jobError.includes('502') || jobError.includes('Bad Gateway')) {
              enhancedError = '🌐 The video processing service is temporarily unavailable. Please try again in a few minutes.';
            } else if (jobError.includes('503') || jobError.includes('service temporarily unavailable')) {
              enhancedError = '🔧 The service is temporarily unavailable due to high demand. Please try again later.';
            } else if (jobError.includes('timeout')) {
              enhancedError = '⏱️ Video processing timed out. This can happen with complex videos - please try with shorter content.';
            } else if (jobError.includes('rate limit')) {
              enhancedError = '⏰ Rate limit exceeded. Please wait a moment and try again.';
            } else if (jobError.includes('storage') || jobError.includes('S3')) {
              enhancedError = '💾 Storage error occurred during video processing. Please try again.';
            } else {
              enhancedError = `⚠️ ${jobError}`;
            }
          }
          setError(enhancedError);
          // Remove failed job from persistent storage
          removePersistentJob(jobId);
          setLoading(false);
          return;
        } else if (status === 'processing') {
          const elapsedMinutes = attempts;
          setJobProgress(`Processing video... This may take 15-20 minutes (${elapsedMinutes}/30 minutes)`);
        } else {
          setJobProgress(`Queued for processing... (${attempts}/30 minutes)`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 60000); // Poll every 60 seconds (1 minute)
        } else {
          setError('Job polling timeout after 30 minutes. Video processing is taking longer than expected. Please check the Jobs page for status or try again later.');
          removePersistentJob(jobId);
          setLoading(false);
        }
      } catch (err) {
        console.error('Video creation polling error:', err);
        consecutiveErrors++;

        // Stop polling after too many consecutive errors
        if (consecutiveErrors >= maxConsecutiveErrors) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          if (errorMsg.includes('NetworkError') || errorMsg.includes('Failed to fetch')) {
            setError('🔌 Network error: Please check your internet connection and try again.');
          } else if (errorMsg.includes('service temporarily unavailable') || errorMsg.includes('502')) {
            setError('🌐 The video service is temporarily unavailable. Please try again later.');
          } else {
            setError(`💥 ${errorMsg}`);
          }
          removePersistentJob(jobId);
          setLoading(false);
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 60000); // Poll every 60 seconds
        } else {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          setError(`💥 ${errorMsg}`);
          removePersistentJob(jobId);
          setLoading(false);
        }
      }
    };

    poll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Video polling function manages its own state

  const createVideo = useCallback(async (request: VideoCreationRequest) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      setJobStatus('pending');
      setJobProgress('Starting video creation...');

      // VideoCreatorTab always uses footage-to-video endpoint
      // It works with both custom scripts and topics
      const endpoint = '/ai/footage-to-video';

      if (request.custom_script && !request.topic) {
        setJobProgress('Creating video from your custom script...');
      } else {
        setJobProgress('Generating script and creating video from topic...');
      }

      const response = await directApi.post(endpoint, request as unknown as Record<string, unknown>);
      const responseData = response.data;

      // Handle both direct response format {job_id: "..."} and wrapped format {success: true, data: {job_id: "..."}}
      let jobId: string;
      if (responseData.job_id) {
        // Direct response format from backend
        jobId = responseData.job_id;
      } else if (responseData.success && responseData.data?.job_id) {
        // Wrapped response format
        jobId = responseData.data.job_id;
      } else if (responseData.success === false) {
        throw new Error(responseData.error || 'Failed to create video');
      } else {
        throw new Error('No job ID returned from video creation');
      }

      setPollingJobId(jobId);
      setJobProgress('Video creation job started...');

      // Save job to persistent storage
      savePersistentJob({
        jobId,
        endpoint: '/jobs',
        type: 'video',
        timestamp: Date.now(),
        progress: 'Video creation job started...',
        status: 'pending'
      });

      pollJobStatus(jobId);

      return jobId;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create video';
      setError(`Failed to start video creation: ${errorMsg}`);
      setLoading(false);
      throw err;
    }
  }, [pollJobStatus]);

  // Check for persistent jobs on mount
  useEffect(() => {
    const initializeJobs = async () => {
      // First clean up orphaned jobs
      await clearOrphanedJobs();

      // Then check for remaining active jobs
      const activeJobs = getActivePersistentJobs().filter(job => job.type === 'video');
      if (activeJobs.length > 0) {
        // Resume the most recent job
        const mostRecent = activeJobs[activeJobs.length - 1];
        setPollingJobId(mostRecent.jobId);
        setJobStatus(mostRecent.status || 'pending');
        setJobProgress(mostRecent.progress || 'Resuming video processing...');
        setLoading(true);
        setIsResumedJob(true);

        // Start polling for the resumed job
        pollJobStatus(mostRecent.jobId);
      }
    };

    initializeJobs();
  }, [pollJobStatus]);

  const resetState = useCallback(() => {
    setResult(null);
    setError(null);
    setJobStatus(null);
    setJobProgress('');
    setPollingJobId(null);
    setLoading(false);
    setIsResumedJob(false);
  }, []);

  return {
    result,
    jobStatus,
    jobProgress,
    pollingJobId,
    loading,
    error,
    isResumedJob,
    createVideo,
    resetState,
    setError,
    setLoading,
    clearAllJobs: clearAllPersistentJobs,
    clearOrphanedJobs
  };
};

export const useTopicResearch = () => {
  const [result, setResult] = useState<ContentCreationJobResult | null>(null);
  const [jobStatus, setJobStatus] = useState<ContentCreationJobStatus | null>(null);
  const [jobProgress, setJobProgress] = useState<string>('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isResumedJob, setIsResumedJob] = useState(false);

  const pollJobStatus = useCallback(async (jobId: string) => {
    const maxAttempts = 30; // 30 minutes max (30 attempts × 60 seconds = 30 minutes)
    const maxConsecutiveErrors = 5; // Stop after 5 consecutive errors
    let attempts = 0;
    let consecutiveErrors = 0;

    const poll = async () => {
      try {
        attempts++;
        const response = await directApi.get(`/footage-to-video/${jobId}`);
        const responseData = response.data;
        consecutiveErrors = 0; // Reset on successful API call

        // Handle both direct response format and wrapped format
        let status: ContentCreationJobStatus;
        let jobResult: unknown;
        let jobError: string | undefined;

        if (responseData.success === false) {
          // Wrapped error format — check if it contains a job failure
          const errorMessage = responseData.error || 'Failed to get job status';
          if (errorMessage.includes('failed') || errorMessage.includes('error')) {
            setJobProgress('Research processing failed');
            setError(`⚠️ ${errorMessage}`);
            removePersistentJob(jobId);
            setLoading(false);
            return;
          }
          if (errorMessage.includes('404') || errorMessage.includes('not found')) {
            setError('❓ Job not found. It may have expired or been removed.');
            removePersistentJob(jobId);
            setLoading(false);
            return;
          }
          throw new Error(`⚠️ ${errorMessage}`);
        } else if (responseData.success && responseData.data) {
          // Wrapped success format
          status = responseData.data.status as ContentCreationJobStatus;
          jobResult = responseData.data.result;
          jobError = responseData.data.error;
        } else if (responseData.status) {
          // Direct format from backend
          status = responseData.status as ContentCreationJobStatus;
          jobResult = responseData.result;
          jobError = responseData.error;
        } else {
          throw new Error('Invalid response format from job status endpoint');
        }

        setJobStatus(status);

        // Update persistent job status
        if (pollingJobId) {
          const activeJobs = getActivePersistentJobs();
          const currentJob = activeJobs.find(j => j.jobId === pollingJobId);
          if (currentJob) {
            currentJob.status = status;
            currentJob.progress = jobProgress;
            savePersistentJob(currentJob);
          }
        }

        if (status === 'completed') {
          setJobProgress('Research and video creation completed successfully!');
          setResult({
            job_id: jobId,
            status: 'completed',
            result: jobResult as VideoCreationResult | TopicResearchResult
          });
          // Remove completed job from persistent storage
          removePersistentJob(jobId);
          setLoading(false);
          return;
        } else if (status === 'failed') {
          setJobProgress('Research processing failed');
          let enhancedError = jobError || 'Processing failed';
          if (jobError) {
            if (jobError.includes('research')) {
              enhancedError = '🔍 Failed to research the topic. Please try with a different topic or simpler terms.';
            } else if (jobError.includes('script')) {
              enhancedError = '📝 Failed to generate script from research. Please try again.';
            } else if (jobError.includes('timeout')) {
              enhancedError = '⏱️ Research processing timed out. Please try with a simpler topic.';
            } else {
              enhancedError = `⚠️ ${jobError}`;
            }
          }
          setError(enhancedError);
          // Remove failed job from persistent storage
          removePersistentJob(jobId);
          setLoading(false);
          return;
        } else if (status === 'processing') {
          const elapsedMinutes = attempts;
          setJobProgress(`Researching topic and creating video... This may take 15-20 minutes (${elapsedMinutes}/30 minutes)`);
        } else {
          setJobProgress(`Queued for research... (${attempts}/30 minutes)`);
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 60000); // Poll every 60 seconds (1 minute)
        } else {
          setError('Job polling timeout after 30 minutes. Research is taking longer than expected. Please check the Jobs page for status or try again later.');
          removePersistentJob(jobId);
          setLoading(false);
        }
      } catch (err) {
        console.error('Topic research polling error:', err);
        consecutiveErrors++;

        if (consecutiveErrors >= maxConsecutiveErrors) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          setError(`💥 ${errorMsg}`);
          removePersistentJob(jobId);
          setLoading(false);
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 60000); // Poll every 60 seconds
        } else {
          const errorMsg = err instanceof Error ? err.message : 'Failed to check job status';
          setError(`💥 ${errorMsg}`);
          removePersistentJob(jobId);
          setLoading(false);
        }
      }
    };

    poll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Research polling function manages its own state

  const researchTopic = useCallback(async (request: TopicResearchRequest) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      setJobStatus('pending');
      setJobProgress('Starting topic research...');

      const response = await directApi.post('/footage-to-video', request as unknown as Record<string, unknown>);
      const responseData = response.data;

      // Handle both direct response format {job_id: "..."} and wrapped format {success: true, data: {job_id: "..."}}
      let jobId: string;
      if (responseData.job_id) {
        // Direct response format from backend
        jobId = responseData.job_id;
      } else if (responseData.success && responseData.data?.job_id) {
        // Wrapped response format
        jobId = responseData.data.job_id;
      } else if (responseData.success === false) {
        throw new Error(responseData.error || 'Failed to start topic research');
      } else {
        throw new Error('No job ID returned from topic research');
      }

      setPollingJobId(jobId);
      setJobProgress('Topic research job started...');

      // Save job to persistent storage
      savePersistentJob({
        jobId,
        endpoint: '/jobs',
        type: 'research',
        timestamp: Date.now(),
        progress: 'Topic research job started...',
        status: 'pending'
      });

      pollJobStatus(jobId);

      return jobId;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start topic research';
      setError(`Failed to start topic research: ${errorMsg}`);
      setLoading(false);
      throw err;
    }
  }, [pollJobStatus]);

  // Check for persistent jobs on mount
  useEffect(() => {
    const initializeJobs = async () => {
      // First clean up orphaned jobs
      await clearOrphanedJobs();

      // Then check for remaining active jobs
      const activeJobs = getActivePersistentJobs().filter(job => job.type === 'research');
      if (activeJobs.length > 0) {
        // Resume the most recent job
        const mostRecent = activeJobs[activeJobs.length - 1];
        setPollingJobId(mostRecent.jobId);
        setJobStatus(mostRecent.status || 'pending');
        setJobProgress(mostRecent.progress || 'Resuming topic research...');
        setLoading(true);
        setIsResumedJob(true);

        // Start polling for the resumed job
        pollJobStatus(mostRecent.jobId);
      }
    };

    initializeJobs();
  }, [pollJobStatus]);

  const resetState = useCallback(() => {
    setResult(null);
    setError(null);
    setJobStatus(null);
    setJobProgress('');
    setPollingJobId(null);
    setLoading(false);
    setIsResumedJob(false);
  }, []);

  return {
    result,
    jobStatus,
    jobProgress,
    pollingJobId,
    loading,
    error,
    isResumedJob,
    researchTopic,
    resetState,
    setError,
    setLoading,
    clearAllJobs: clearAllPersistentJobs,
    clearOrphanedJobs
  };
};

export const useVoices = () => {
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [voiceProviders, setVoiceProviders] = useState<VoiceProviderInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVoices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await directApi.getLongTimeout('/audio/voices/all', 60000);
      const responseData = response.data;

      // Handle both success/error format and direct data format
      const voicesResponse = responseData.voices || responseData.data?.voices || responseData;

      if (!voicesResponse) {
        throw new Error('No voices data received from server');
      }

      // Convert grouped voices format to flat list
      const flatVoices: VoiceInfo[] = [];
      const providers: { [key: string]: VoiceProviderInfo } = {};

      Object.entries(voicesResponse).forEach(([providerName, voiceList]: [string, unknown]) => {
        // Skip invalid providers but don't warn for now - some providers might return empty arrays
        if (providerName !== 'kokoro' && providerName !== 'edge' && providerName !== 'piper') {
          console.warn(`Unknown voice provider: ${providerName}. Skipping.`);
          return;
        }

        const provider: VoiceProviderInfo = {
          name: providerName,
          voices: [],
          languages: []
        };

        providers[providerName] = provider;

        // Handle case where voiceList might not be an array (empty response, error, etc.)
        if (!Array.isArray(voiceList)) {
          console.warn(`Invalid voice list format for provider ${providerName}:`, voiceList);
          return;
        }

        voiceList.forEach((voice: Record<string, unknown>) => {
          // Handle different voice formats from different providers
          let voiceInfo: VoiceInfo;

          if (typeof voice === 'object' && voice !== null) {
            voiceInfo = {
              name: (voice.name as string | undefined) || (voice.id as string | undefined) || String(voice),
              provider: providerName as 'kokoro' | 'edge' | 'piper',
              language: (voice.language as string | undefined) || 'en',
              description: (voice.description as string | undefined) || `${(voice.name as string | undefined) || (voice.id as string | undefined)} voice`,
              gender: (voice.gender as string | undefined) || 'unknown',
              grade: (voice.grade as string | undefined) || (voice.quality as string | undefined) || undefined
            };
          } else {
            // Fallback for string or primitive values
            voiceInfo = {
              name: String(voice),
              provider: providerName as 'kokoro' | 'edge' | 'piper',
              language: 'en',
              description: `${voice} voice`,
              gender: 'unknown'
            };
          }

          flatVoices.push(voiceInfo);
          provider.voices.push(voiceInfo);

          if (!provider.languages.includes(voiceInfo.language)) {
            provider.languages.push(voiceInfo.language);
          }
        });
      });

      setVoices(flatVoices);
      setVoiceProviders(Object.values(providers));
      setLoading(false);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch voices';
      setError(errorMsg);
      setLoading(false);

      // Provide fallback voices when API fails to ensure UI doesn't break
      console.warn('Voice API failed, providing fallback voices:', errorMsg);
      const fallbackVoices: VoiceInfo[] = [
        // Piper fallback voices
        { name: 'en_US-lessac-medium', provider: 'piper', language: 'en-US', description: 'English US - Lessac (Medium)', gender: 'female' },
        { name: 'en_US-amy-medium', provider: 'piper', language: 'en-US', description: 'English US - Amy (Medium)', gender: 'female' },
        { name: 'en_US-ryan-medium', provider: 'piper', language: 'en-US', description: 'English US - Ryan (Medium)', gender: 'male' },
        { name: 'en_GB-alan-medium', provider: 'piper', language: 'en-GB', description: 'English GB - Alan (Medium)', gender: 'male' },
        { name: 'fr_FR-siwis-medium', provider: 'piper', language: 'fr-FR', description: 'French - Siwis (Medium)', gender: 'female' },
        // Kokoro fallback voices
        { name: 'af_heart', provider: 'kokoro', language: 'en-US', description: 'American Female - Heart (Grade A)', gender: 'female', grade: 'A' },
        { name: 'af_bella', provider: 'kokoro', language: 'en-US', description: 'American Female - Bella (Grade A-)', gender: 'female', grade: 'A-' },
        { name: 'am_michael', provider: 'kokoro', language: 'en-US', description: 'American Male - Michael (Grade C+)', gender: 'male', grade: 'C+' },
        // Edge fallback voices (minimal)
        { name: 'en-US-AriaNeural', provider: 'edge', language: 'en-US', description: 'English US - Aria (Neural)', gender: 'female' }
      ];

      const fallbackProviders: { [key: string]: VoiceProviderInfo } = {
        piper: {
          name: 'piper',
          voices: fallbackVoices.filter(v => v.provider === 'piper'),
          languages: ['en-US', 'en-GB', 'fr-FR']
        },
        kokoro: {
          name: 'kokoro',
          voices: fallbackVoices.filter(v => v.provider === 'kokoro'),
          languages: ['en-US']
        },
        edge: {
          name: 'edge',
          voices: fallbackVoices.filter(v => v.provider === 'edge'),
          languages: ['en-US']
        }
      };

      setVoices(fallbackVoices);
      setVoiceProviders(Object.values(fallbackProviders));
    }
  }, []);

  const getVoicesByProvider = useCallback((provider: string): VoiceInfo[] => {
    return voices.filter(voice => voice.provider === provider);
  }, [voices]);

  const getVoicesByLanguage = useCallback((language: string): VoiceInfo[] => {
    return voices.filter(voice => voice.language === language);
  }, [voices]);

  const getVoice = useCallback((provider: string, voiceName: string): VoiceInfo | undefined => {
    return voices.find(voice => voice.provider === provider && voice.name === voiceName);
  }, [voices]);

  return {
    voices,
    voiceProviders,
    loading,
    error,
    fetchVoices,
    getVoicesByProvider,
    getVoicesByLanguage,
    getVoice
  };
};
