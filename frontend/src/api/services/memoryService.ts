import { apiCall } from "../client";
import { API_ENDPOINTS } from "../endpoints";
import type { Memory } from "../types";

export const memoryService = {
  /**
   * Get episode memory for a specific script
   */
  async getEpisodeMemory(key: string, signal?: AbortSignal): Promise<Memory> {
    return apiCall<Memory>(API_ENDPOINTS.getEpisodeMemory(key), { signal });
  },
};
