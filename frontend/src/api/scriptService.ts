import { apiCall } from './client'
import { API_ENDPOINTS } from './endpoints'

export interface Script {
  script_id: number
  key: string
  title: string
  episode_num: number
  content: string
  roles: string
  sceneries: string
  author: string | null
  creation_year: number | null
  score: number | null
}

interface ScriptsResponse {
  scripts: Script[]
  count: number
}

class ScriptService {
  /**
   * 获取所有剧本列表
   */
  async getAllScripts(): Promise<Script[]> {
    const response = await apiCall<ScriptsResponse>(API_ENDPOINTS.getAllScripts())
    return response.scripts
  }

  /**
   * 根据 key 获取剧本详情
   */
  async getScript(key: string): Promise<Script> {
    return await apiCall<Script>(API_ENDPOINTS.getScript(key))
  }

  /**
   * 更新剧本内容（Markdown 格式）
   */
  async updateScriptContent(key: string, content: string): Promise<void> {
    await apiCall(API_ENDPOINTS.updateScriptContent(key), {
      method: 'PUT',
      body: JSON.stringify({ content })
    })
  }
}

export const scriptService = new ScriptService()
