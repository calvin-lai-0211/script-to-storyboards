import { apiCall } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { StoryboardsResponse } from '../types'

export const storyboardService = {
  /**
   * Get storyboards for a specific script
   */
  async getStoryboards(key: string, signal?: AbortSignal): Promise<StoryboardsResponse> {
    return apiCall<StoryboardsResponse>(API_ENDPOINTS.getStoryboards(key), {
      signal
    })
  }
}
