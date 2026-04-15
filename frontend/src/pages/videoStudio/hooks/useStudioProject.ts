import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studioApi } from '../api';
import type { StudioScene, JobStatus } from '../types';

const POLL_INTERVAL = 3000;
const MAX_POLL_ERRORS = 10;

export function useStudioProject(projectId: string | null) {
  const queryClient = useQueryClient();
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJobType, setActiveJobType] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollErrorCount = useRef(0);

  // ── Project query ────────────────────────────────────────────────────
  const projectQuery = useQuery({
    queryKey: ['studio-project', projectId],
    queryFn: () => studioApi.getProject(projectId!),
    enabled: !!projectId,
    refetchOnWindowFocus: false,
  });

  const project = projectQuery.data ?? null;
  const selectedScene = project?.scenes.find(s => s.id === selectedSceneId) ?? null;

  const stopPolling = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
    pollErrorCount.current = 0;
    setActiveJobId(null);
  }, []);

  // ── Job polling ──────────────────────────────────────────────────────
  const startPolling = useCallback((jobId: string, jobType: string) => {
    setActiveJobId(jobId);
    setActiveJobType(jobType);
    setJobStatus({ job_id: jobId, status: 'processing', progress: null, result: null, error: null });

    if (pollRef.current) clearInterval(pollRef.current);
    pollErrorCount.current = 0;

    pollRef.current = setInterval(async () => {
      if (!projectId) return;
      try {
        const status = await studioApi.getJobStatus(projectId, jobId);
        pollErrorCount.current = 0;
        setJobStatus(status);

        // Stop on terminal status OR when result contains a video_url
        const isDone = status.status === 'completed' || status.status === 'failed';
        const hasVideoUrl = !!(status.result?.video_url);
        if (isDone || hasVideoUrl) {
          if (hasVideoUrl && status.status !== 'completed') {
            // Backend returned the URL but status wasn't 'completed' — force it
            setJobStatus({ ...status, status: 'completed' });
          }
          stopPolling();
          queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
        }
      } catch (err) {
        pollErrorCount.current += 1;
        console.warn(`[Studio] Poll error ${pollErrorCount.current}/${MAX_POLL_ERRORS}:`, err);

        // Job info may be gone (server restart, cache expiry) — check project directly
        try {
          const freshProject = await studioApi.getProject(projectId);
          if (freshProject?.final_video_url) {
            setJobStatus({
              job_id: jobId, status: 'completed', progress: null, error: null,
              result: { video_url: freshProject.final_video_url },
            });
            stopPolling();
            queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
            return;
          }
        } catch { /* project fetch also failed — continue error counting */ }

        if (pollErrorCount.current >= MAX_POLL_ERRORS) {
          setJobStatus(prev => prev ? { ...prev, status: 'failed', error: 'Lost connection to server' } : null);
          stopPolling();
          queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
        }
      }
    }, POLL_INTERVAL);
  }, [projectId, queryClient, stopPolling]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // ── Scene mutations ──────────────────────────────────────────────────
  const addScene = useMutation({
    mutationFn: (data: { script_text?: string; after_index?: number }) =>
      studioApi.addScene(projectId!, data),
    onSuccess: (scene) => {
      queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
      setSelectedSceneId(scene.id);
    },
  });

  const updateScene = useMutation({
    mutationFn: ({ sceneId, data }: { sceneId: string; data: Partial<StudioScene> }) =>
      studioApi.updateScene(projectId!, sceneId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
    },
  });

  const deleteScene = useMutation({
    mutationFn: (sceneId: string) => studioApi.deleteScene(projectId!, sceneId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
      if (selectedSceneId) setSelectedSceneId(null);
    },
  });

  const reorderScenes = useMutation({
    mutationFn: (sceneIds: string[]) => studioApi.reorderScenes(projectId!, sceneIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
    },
  });

  // ── Pipeline actions ─────────────────────────────────────────────────
  const generateTTS = useCallback(async (sceneIds?: string[]) => {
    if (!projectId) return;
    const { job_id } = await studioApi.generateTTS(projectId, sceneIds);
    startPolling(job_id, 'tts');
  }, [projectId, startPolling]);

  const generateMedia = useCallback(async (sceneIds?: string[]) => {
    if (!projectId) return;
    const { job_id } = await studioApi.generateMedia(projectId, sceneIds);
    startPolling(job_id, 'media');
  }, [projectId, startPolling]);

  const generateAIScenes = useCallback(async (data: { topic?: string; script?: string; scene_count?: number }) => {
    if (!projectId) return;
    const { job_id } = await studioApi.generateAIScenes(projectId, data);
    startPolling(job_id, 'ai_scenes');
  }, [projectId, startPolling]);

  const exportVideo = useCallback(async (data?: { include_captions?: boolean; include_background_music?: boolean }) => {
    if (!projectId) return;
    const { job_id } = await studioApi.exportVideo(projectId, data ?? {});
    startPolling(job_id, 'export');
  }, [projectId, startPolling]);

  const uploadMedia = useCallback(async (sceneId: string, file: File) => {
    if (!projectId) return;
    await studioApi.uploadMedia(projectId, sceneId, file);
    queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
  }, [projectId, queryClient]);

  const updateSettings = useCallback(async (settings: Record<string, unknown>) => {
    if (!projectId) return;
    await studioApi.updateProject(projectId, { settings });
    queryClient.invalidateQueries({ queryKey: ['studio-project', projectId] });
  }, [projectId, queryClient]);

  return {
    project,
    isLoading: projectQuery.isLoading,
    error: projectQuery.error,
    selectedScene,
    selectedSceneId,
    setSelectedSceneId,

    // Mutations
    addScene: addScene.mutateAsync,
    updateScene: updateScene.mutateAsync,
    deleteScene: deleteScene.mutateAsync,
    reorderScenes: reorderScenes.mutateAsync,

    // Pipeline
    generateTTS,
    generateMedia,
    generateAIScenes,
    exportVideo,
    uploadMedia,
    updateSettings,

    // Job status
    activeJobId,
    activeJobType,
    jobStatus,
    isProcessing: !!activeJobId,
  };
}
