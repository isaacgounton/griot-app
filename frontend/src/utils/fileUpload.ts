/**
 * File Upload Utilities for Multimodal Chat
 */

export interface UploadResult {
  url: string;
  filename: string;
  size: number;
  mime_type: string;
  job_id: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

const API_BASE = '/api/v1';

// Helper function to get auth headers
const getAuthHeaders = () => {
  const apiKey = localStorage.getItem('griot_api_key');
  return {
    'Accept': 'application/json',
    ...(apiKey && { 'X-API-Key': apiKey })
  };
};

export async function uploadFile(
  file: File,
  _onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_name', file.name);
  formData.append('public', 'true');
  formData.append('sync', 'true'); // Upload synchronously for chat

  try {
    const response = await fetch(`${API_BASE}/s3/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();

    if (result.status === 'completed' && result.result) {
      // Handle both 'url' and 'file_url' property names
      const fileUrl = result.result.url || result.result.file_url;
      if (!fileUrl) {
        throw new Error('No file URL returned from server');
      }

      return {
        url: fileUrl,
        filename: result.result.filename || result.result.file_name || file.name,
        size: result.result.size || result.result.file_size || file.size,
        mime_type: result.result.mime_type || file.type,
        job_id: result.job_id
      };
    } else {
      throw new Error(result.error || 'Upload failed');
    }
  } catch (error) {
    console.error('File upload error:', error);
    throw new Error(error instanceof Error ? error.message : 'Upload failed');
  }
}

export function isValidFileType(file: File): boolean {
  const validTypes = [
    // Images
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
    // Audio
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/flac',
    // Video
    'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo'
  ];

  return validTypes.includes(file.type) || validTypes.some(type => file.type.startsWith(type.split('/')[0] + '/'));
}

export function getFileType(file: File): 'image' | 'audio' | 'video' | 'unknown' {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('audio/')) return 'audio';
  if (file.type.startsWith('video/')) return 'video';
  return 'unknown';
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function generateUniqueFilename(originalName: string): string {
  const timestamp = Date.now();
  const randomString = Math.random().toString(36).substring(2, 8);
  const extension = originalName.split('.').pop();
  const nameWithoutExt = originalName.split('.').slice(0, -1).join('.');

  return `${nameWithoutExt}_${timestamp}_${randomString}.${extension}`;
}