/**
 * Simple voice caching utility to avoid repeated API calls
 */

import { VoiceInfo } from '../types/griot';

interface VoiceCacheData {
  voices: Record<string, Record<string, VoiceInfo[]>>;
  providers: string[];
  total_voices: number;
  timestamp: number;
}

const CACHE_KEY = 'griot_voice_cache';
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

export class VoiceCache {
  static get(): VoiceCacheData | null {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;

      const data: VoiceCacheData = JSON.parse(cached);
      const now = Date.now();

      // Check if cache is expired
      if (now - data.timestamp > CACHE_DURATION) {
        localStorage.removeItem(CACHE_KEY);
        return null;
      }

      console.log('Voice cache hit - using cached voices');
      return data;
    } catch (error) {
      console.warn('Failed to read voice cache:', error);
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
  }

  static set(voices: Record<string, Record<string, VoiceInfo[]>>, providers: string[], totalVoices: number): void {
    try {
      const data: VoiceCacheData = {
        voices,
        providers,
        total_voices: totalVoices,
        timestamp: Date.now()
      };

      localStorage.setItem(CACHE_KEY, JSON.stringify(data));
      console.log(`Voice cache updated with ${totalVoices} voices`);
    } catch (error) {
      console.warn('Failed to cache voices:', error);
      // If localStorage is full, try to clear old cache and retry
      try {
        localStorage.removeItem(CACHE_KEY);
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          voices,
          providers,
          total_voices: totalVoices,
          timestamp: Date.now()
        }));
      } catch (retryError) {
        console.warn('Failed to cache voices even after cleanup:', retryError);
      }
    }
  }

  static clear(): void {
    localStorage.removeItem(CACHE_KEY);
    console.log('Voice cache cleared');
  }

  static isExpired(): boolean {
    const cached = this.get();
    return cached === null;
  }
}