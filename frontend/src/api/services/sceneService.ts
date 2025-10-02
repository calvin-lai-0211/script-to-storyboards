import { apiCall } from '../client';
import { API_ENDPOINTS } from '../endpoints';
import type { ScenesResponse } from '../types';

export const sceneService = {
  /**
   * Get all scenes across all scripts
   */
  async getAllScenes(signal?: AbortSignal): Promise<ScenesResponse> {
    return apiCall<ScenesResponse>(API_ENDPOINTS.getAllScenes(), { signal });
  },

  /**
   * Get scenes for a specific script
   */
  async getScenes(key: string, signal?: AbortSignal): Promise<ScenesResponse> {
    return apiCall<ScenesResponse>(API_ENDPOINTS.getScenes(key), { signal });
  },
};
