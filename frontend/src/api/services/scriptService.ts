import { apiCall } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { ScriptsResponse, ScriptDetail } from '../types'

export const scriptService = {
  /**
   * Get all scripts
   */
  async getAllScripts(signal?: AbortSignal): Promise<ScriptsResponse> {
    return apiCall<ScriptsResponse>(API_ENDPOINTS.getAllScripts(), { signal })
  },

  /**
   * Get script detail by key
   */
  async getScript(key: string, signal?: AbortSignal): Promise<ScriptDetail> {
    return apiCall<ScriptDetail>(API_ENDPOINTS.getScript(key), { signal })
  }
}
