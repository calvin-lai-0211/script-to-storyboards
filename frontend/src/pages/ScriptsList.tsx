import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Film,
  Calendar,
  User,
  Star,
  Loader2,
  AlertCircle,
  Key,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react'
import { API_ENDPOINTS, apiCall } from '@api'
import { useEpisodeStore } from '@store/useEpisodeStore'
import { ScriptData } from '@store/types'

const ScriptsList: React.FC = () => {
  const navigate = useNavigate()
  const { allEpisodes, setAllEpisodes, setCurrentEpisode } = useEpisodeStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Use cached data if available
  const episodes = allEpisodes || []

  useEffect(() => {
    // If already in store, skip fetch
    if (allEpisodes) {
      console.debug('EpisodesList: Using cached data')
      return
    }

    fetchEpisodes()
  }, [allEpisodes])

  const fetchEpisodes = async () => {
    try {
      setLoading(true)
      setError(null)

      console.debug('EpisodesList: Fetching from API')
      const data = await apiCall<{ scripts: ScriptData[]; count: number }>(
        API_ENDPOINTS.getAllScripts()
      )

      setAllEpisodes(data.scripts)
    } catch (err) {
      console.error('Error fetching episodes:', err)
      setError('获取剧集列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCardClick = (episode: ScriptData) => {
    // Set current episode in store first
    setCurrentEpisode({
      key: episode.key,
      title: episode.title,
      episode_num: episode.episode_num
    })
    // Navigate to episode detail page
    navigate(`/episode/${encodeURIComponent(episode.key)}`)
  }

  const handleCopyKey = (e: React.MouseEvent, key: string) => {
    e.stopPropagation() // 阻止触发卡片点击
    navigator.clipboard.writeText(key).then(() => {
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), 2000) // 2秒后恢复
    })
  }

  const handleRefresh = () => {
    fetchEpisodes()
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-blue-500" />
          <p className="text-slate-600">加载剧集列表中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-500" />
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => fetchEpisodes()}
            className="mt-4 rounded-lg bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-7xl p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-slate-800">剧集列表</h1>
            <p className="text-slate-600">共 {episodes.length} 个剧集</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 rounded-lg bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 卡片网格 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {episodes.map((episode) => (
            <div
              key={`${episode.title}-${episode.episode_num}`}
              onClick={() => handleCardClick(episode)}
              className="group cursor-pointer overflow-hidden rounded-2xl border-2 border-slate-200 bg-white transition-all duration-300 hover:-translate-y-1 hover:border-blue-400 hover:shadow-xl"
              title={episode.title}
            >
              {/* 卡片头部 - 渐变背景 */}
              <div className="relative h-28 overflow-hidden bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500">
                <div className="absolute inset-0 bg-black/10 transition-colors duration-300 group-hover:bg-black/0"></div>
                <div className="absolute right-4 bottom-3 left-4">
                  <h3
                    className="mb-1 truncate text-base leading-tight font-bold text-white drop-shadow-lg"
                    title={episode.title}
                  >
                    {episode.title}
                  </h3>
                  <p className="text-sm text-white/90 drop-shadow">第 {episode.episode_num} 集</p>
                </div>
                <div className="absolute top-3 right-3">
                  <Film className="h-5 w-5 text-white/80" />
                </div>
              </div>

              {/* 卡片内容 */}
              <div className="space-y-2 p-3">
                {/* Key with copy button */}
                <div className="group/key flex items-center space-x-2 text-xs text-slate-500">
                  <Key className="h-3 w-3 flex-shrink-0" />
                  <span className="flex-1 truncate font-mono" title={episode.key}>
                    {episode.key}
                  </span>
                  <button
                    onClick={(e) => handleCopyKey(e, episode.key)}
                    className="cursor-pointer rounded p-1 hover:bg-slate-100"
                    title="复制 Key"
                  >
                    {copiedKey === episode.key ? (
                      <Check className="h-3 w-3 text-green-600" />
                    ) : (
                      <Copy className="h-3 w-3 text-slate-400 hover:text-slate-600" />
                    )}
                  </button>
                </div>

                {/* 作者 */}
                {episode.author && (
                  <div className="flex items-center space-x-2 text-sm text-slate-600">
                    <User className="h-4 w-4 flex-shrink-0" />
                    <span className="truncate">{episode.author}</span>
                  </div>
                )}

                {/* 年份和评分 */}
                <div className="flex items-center justify-between text-sm">
                  {episode.creation_year && (
                    <div className="flex items-center space-x-2 text-slate-600">
                      <Calendar className="h-4 w-4" />
                      <span>{episode.creation_year}</span>
                    </div>
                  )}

                  {episode.score !== null && (
                    <div className="flex items-center space-x-1 text-amber-600">
                      <Star className="h-4 w-4 fill-amber-400" />
                      <span className="font-medium">{episode.score.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {episodes.length === 0 && (
          <div className="py-16 text-center">
            <Film className="mx-auto mb-4 h-16 w-16 text-slate-300" />
            <p className="text-slate-500">暂无剧集</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScriptsList
