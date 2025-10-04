import { apiCall } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { ScenesResponse, Scene } from '../types'

export const sceneService = {
  /**
   * Get all scenes across all scripts
   */
  async getAllScenes(signal?: AbortSignal): Promise<ScenesResponse> {
    return apiCall<ScenesResponse>(API_ENDPOINTS.getAllScenes(), { signal })
  },

  /**
   * Get scenes for a specific script
   */
  async getScenes(key: string, signal?: AbortSignal): Promise<ScenesResponse> {
    return apiCall<ScenesResponse>(API_ENDPOINTS.getScenes(key), { signal })
  },

  /**
   * Get scene detail by ID
   */
  async getScene(id: string | number, signal?: AbortSignal): Promise<Scene> {
    return apiCall<Scene>(API_ENDPOINTS.getScene(id), { signal })
  },

  /**
   * Update scene prompt
   */
  async updateScenePrompt(
    id: string | number,
    imagePrompt: string,
    signal?: AbortSignal
  ): Promise<{ scene_id: number }> {
    return apiCall<{ scene_id: number }>(API_ENDPOINTS.updateScenePrompt(id), {
      method: 'PUT',
      body: JSON.stringify({ image_prompt: imagePrompt }),
      signal
    })
  },

  /**
   * Generate scene image (sync mode, may timeout)
   */
  async generateSceneImage(
    id: string | number,
    imagePrompt: string,
    signal?: AbortSignal
  ): Promise<{ scene_id: number; image_url: string; local_path: string }> {
    return apiCall<{
      scene_id: number
      image_url: string
      local_path: string
    }>(API_ENDPOINTS.generateSceneImage(id), {
      method: 'POST',
      body: JSON.stringify({ image_prompt: imagePrompt }),
      signal
    })
  },

  /**
   * Submit async image generation task
   */
  async submitSceneTask(
    id: string | number,
    imagePrompt: string,
    signal?: AbortSignal
  ): Promise<{ task_id: string; status: string }> {
    return apiCall<{
      task_id: string
      status: string
    }>(API_ENDPOINTS.submitSceneTask(id), {
      method: 'POST',
      body: JSON.stringify({ image_prompt: imagePrompt }),
      signal
    })
  },

  /**
   * Poll task status for async image generation
   */
  async getSceneTaskStatus(
    id: string | number,
    taskId: string,
    signal?: AbortSignal
  ): Promise<{
    status: 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAIL' | 'CANCEL' | 'UNKNOWN'
    image_url?: string
    error?: string
  }> {
    return apiCall<{
      status: 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAIL' | 'CANCEL' | 'UNKNOWN'
      image_url?: string
      error?: string
    }>(API_ENDPOINTS.getSceneTaskStatus(id, taskId), {
      signal
    })
  }
}
