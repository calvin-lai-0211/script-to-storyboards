import React, { useState, useEffect } from 'react'
import { Loader2, Brain, Calendar, Sparkles, RefreshCw } from 'lucide-react'
import { API_ENDPOINTS, apiCall } from '@api'
import { useMemoryStore, EpisodeMemory } from '@store/useMemoryStore'

interface MemoryTabProps {
  scriptKey: string
}

const MemoryTab: React.FC<MemoryTabProps> = ({ scriptKey }) => {
  const { getMemory, setMemory: setCacheMemory } = useMemoryStore()
  const [memory, setMemory] = useState<EpisodeMemory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check store cache first
    const cachedMemory = getMemory(scriptKey)
    if (cachedMemory) {
      console.debug('MemoryTab: Using cached memory')
      setMemory(cachedMemory)
      return
    }

    // Only fetch if no cache
    const abortController = new AbortController()
    fetchMemory(abortController.signal)

    return () => {
      abortController.abort()
    }
  }, [scriptKey, getMemory])

  const fetchMemory = async (signal?: AbortSignal) => {
    try {
      setLoading(true)
      setError(null)

      if (signal?.aborted) return

      const data = await apiCall<EpisodeMemory>(API_ENDPOINTS.getEpisodeMemory(scriptKey))

      if (signal?.aborted) return

      setMemory(data)
      setCacheMemory(scriptKey, data)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'name' in err && err.name === 'AbortError') {
        console.debug('Memory fetch cancelled')
        return
      }
      console.error('Error fetching memory:', err)
      // 友好提示，区分不同错误
      if (
        err &&
        typeof err === 'object' &&
        'message' in err &&
        typeof err.message === 'string' &&
        err.message.includes('暂无')
      ) {
        setError(err.message)
      } else {
        setError('获取剧集摘要失败')
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }

  const handleRefresh = () => {
    console.debug('MemoryTab: Manually refreshing memory')
    const abortController = new AbortController()
    fetchMemory(abortController.signal)
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-blue-500" />
          <p className="text-slate-600">加载剧集摘要中...</p>
        </div>
      </div>
    )
  }

  if (error || !memory) {
    const isNotFound = error && error.includes('暂无')
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Brain
            className={`mx-auto mb-4 h-16 w-16 ${isNotFound ? 'text-slate-300' : 'text-red-400'}`}
          />
          <p
            className={`mb-2 text-lg font-medium ${isNotFound ? 'text-slate-700' : 'text-red-600'}`}
          >
            {error || '暂无剧集摘要'}
          </p>
          <p className="text-sm text-slate-500">
            {isNotFound
              ? '此剧集尚未生成摘要，请前往「流程控制」Tab 执行生成步骤'
              : '加载失败，请稍后重试'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* 工具栏 */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white p-4">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <span className="font-medium text-slate-800">剧集记忆</span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center space-x-2 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
          title="刷新记忆"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>刷新</span>
        </button>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-4xl">
          {/* 头部卡片 */}
          <div className="mb-6 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 p-8 text-white shadow-xl">
            <div className="mb-4 flex items-center space-x-3">
              <Brain className="h-8 w-8" />
              <h1 className="text-3xl font-bold">剧集记忆</h1>
            </div>
            <div className="flex items-center space-x-4 text-purple-100">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-4 w-4" />
                <span>{memory.script_name}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <span>第 {memory.episode_number} 集</span>
              </div>
            </div>
          </div>

          {/* 剧情摘要 */}
          <div className="overflow-hidden rounded-2xl border-2 border-slate-200 bg-white shadow-lg">
            <div className="border-b border-slate-200 bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4">
              <h2 className="flex items-center space-x-2 text-xl font-bold text-slate-800">
                <Sparkles className="h-5 w-5 text-purple-600" />
                <span>剧情摘要</span>
              </h2>
            </div>

            <div className="p-6">
              <div className="prose max-w-none">
                <p className="text-lg leading-relaxed whitespace-pre-wrap text-slate-700">
                  {memory.plot_summary}
                </p>
              </div>
            </div>
          </div>

          {/* 元数据 */}
          {memory.options && Object.keys(memory.options).length > 0 && (
            <div className="mt-6 overflow-hidden rounded-2xl border-2 border-slate-200 bg-white shadow-lg">
              <div className="border-b border-slate-200 bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-4">
                <h2 className="text-xl font-bold text-slate-800">额外信息</h2>
              </div>

              <div className="p-6">
                <pre className="overflow-auto rounded-lg bg-slate-50 p-4 text-sm text-slate-700">
                  {JSON.stringify(memory.options, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* 生成时间 */}
          <div className="mt-4 text-center text-sm text-slate-500">
            生成时间: {new Date(memory.created_at).toLocaleString('zh-CN')}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MemoryTab
