import { apiClient } from '../../utils/api';
import type { StudioProject, ProjectListItem, StudioScene, AudioTrack, JobStatus } from './types';

const BASE = '/studio/projects';

export const studioApi = {
  // ── Projects ──────────────────────────────────────────────────────────
  createProject: (data: { name: string; description?: string; settings?: Record<string, unknown> }) =>
    apiClient.post<StudioProject>(BASE, data).then(r => r.data),

  listProjects: () =>
    apiClient.get<ProjectListItem[]>(BASE).then(r => r.data),

  getProject: (id: string) =>
    apiClient.get<StudioProject>(`${BASE}/${id}`).then(r => r.data),

  updateProject: (id: string, data: { name?: string; description?: string; settings?: Record<string, unknown> }) =>
    apiClient.patch<StudioProject>(`${BASE}/${id}`, data).then(r => r.data),

  deleteProject: (id: string) =>
    apiClient.delete(`${BASE}/${id}`).then(r => r.data),

  // ── Scenes ────────────────────────────────────────────────────────────
  addScene: (projectId: string, data: Partial<StudioScene> & { after_index?: number }) =>
    apiClient.post<StudioScene>(`${BASE}/${projectId}/scenes`, data).then(r => r.data),

  updateScene: (projectId: string, sceneId: string, data: Partial<StudioScene>) =>
    apiClient.patch<StudioScene>(`${BASE}/${projectId}/scenes/${sceneId}`, data).then(r => r.data),

  deleteScene: (projectId: string, sceneId: string) =>
    apiClient.delete(`${BASE}/${projectId}/scenes/${sceneId}`).then(r => r.data),

  reorderScenes: (projectId: string, sceneIds: string[]) =>
    apiClient.post<StudioScene[]>(`${BASE}/${projectId}/scenes/reorder`, { scene_ids: sceneIds }).then(r => r.data),

  uploadMedia: (projectId: string, sceneId: string, file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return apiClient.post<StudioScene>(`${BASE}/${projectId}/scenes/${sceneId}/upload-media`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },

  // ── Audio Tracks ──────────────────────────────────────────────────────
  addAudioTrack: (projectId: string, data: Partial<AudioTrack>) =>
    apiClient.post<AudioTrack>(`${BASE}/${projectId}/audio-tracks`, data).then(r => r.data),

  updateAudioTrack: (projectId: string, trackId: string, data: Partial<AudioTrack>) =>
    apiClient.patch<AudioTrack>(`${BASE}/${projectId}/audio-tracks/${trackId}`, data).then(r => r.data),

  deleteAudioTrack: (projectId: string, trackId: string) =>
    apiClient.delete(`${BASE}/${projectId}/audio-tracks/${trackId}`).then(r => r.data),

  // ── Media Search ─────────────────────────────────────────────────────
  searchMedia: (projectId: string, sceneId: string) =>
    apiClient.post<{ results: Array<{ id: string | number; url: string; thumbnail: string; download_url: string; duration?: number; photographer?: string; provider: string; type: string }>; query: string; provider: string }>(
      `${BASE}/${projectId}/scenes/${sceneId}/search-media`
    ).then(r => r.data),

  // ── Generation ────────────────────────────────────────────────────────
  generateTTS: (projectId: string, sceneIds?: string[]) =>
    apiClient.post<{ job_id: string }>(`${BASE}/${projectId}/generate-tts`, { scene_ids: sceneIds }).then(r => r.data),

  generateMedia: (projectId: string, sceneIds?: string[]) =>
    apiClient.post<{ job_id: string }>(`${BASE}/${projectId}/generate-media`, { scene_ids: sceneIds }).then(r => r.data),

  generateAIScenes: (projectId: string, data: { topic?: string; script?: string; scene_count?: number; language?: string }) =>
    apiClient.post<{ job_id: string }>(`${BASE}/${projectId}/generate-scenes`, data).then(r => r.data),

  exportVideo: (projectId: string, data: { include_captions?: boolean; include_background_music?: boolean; caption_style_override?: string }) =>
    apiClient.post<{ job_id: string }>(`${BASE}/${projectId}/export`, data).then(r => r.data),

  getJobStatus: (projectId: string, jobId: string) =>
    apiClient.get<JobStatus>(`${BASE}/${projectId}/jobs/${jobId}`).then(r => r.data),
};
