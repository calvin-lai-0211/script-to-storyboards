import { apiCall } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { PropsResponse } from '../types'

export const propService = {
  /**
   * Get all props across all scripts
   */
  async getAllProps(signal?: AbortSignal): Promise<PropsResponse> {
    return apiCall<PropsResponse>(API_ENDPOINTS.getAllProps(), { signal })
  }
}
