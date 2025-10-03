import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { MapPin, Sparkles, AlertCircle, Star } from 'lucide-react'
import ImageDisplay from '../components/ImageDisplay'
import BackButton from '../components/BackButton'
import { API_ENDPOINTS, apiCall } from '@api'
import { useSceneStore } from '@store/useSceneStore'

interface SceneData {
  id: number
  drama_name: string
  episode_number: number
  scene_name: string
  image_prompt: string
  reflection: string
  version: string
  image_url: string
  shots_appeared: string[] | null
  is_key_scene: boolean | null
  scene_brief: string | null
  created_at: string | null
}

const SceneViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { currentScene } = useSceneStore()
  const [sceneData, setSceneData] = useState<SceneData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      fetchSceneData(id)
    }
  }, [id])

  const fetchSceneData = async (sceneId: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiCall<any>(API_ENDPOINTS.getScene(sceneId))
      setSceneData(data as SceneData)
    } catch (err) {
      console.error('Error fetching scene data:', err)
      setError('获取场景数据失败，请检查网络或服务器。')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-teal-50">
      {/* 返回按钮 - 固定在左上角 */}
      <div className="absolute top-6 left-6 z-10">
        <BackButton to="/scenes" label="返回场景列表" />
      </div>

      <div className="relative flex flex-col items-center justify-start px-6 py-8">
        {/* 页面标题区域 */}
        <div className="animate-fade-in mb-8 text-center">
          <div className="mb-4 flex items-center justify-center gap-4">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-600 to-teal-600 shadow-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="h-4 w-4 text-yellow-500" />
              </div>
            </div>
            <div>
              <p className="text-lg leading-relaxed font-semibold text-slate-800">
                {currentScene?.scene_name || sceneData?.scene_name || '加载中...'}
              </p>
              {sceneData?.is_key_scene && (
                <span className="mt-1 inline-flex items-center space-x-1 rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-700">
                  <Star className="h-3 w-3" />
                  <span>关键场景</span>
                </span>
              )}
            </div>
          </div>
          {currentScene && (
            <p className="text-sm text-slate-500">
              {currentScene.drama_name} - 第{currentScene.episode_number}集
            </p>
          )}
        </div>

        {/* 主要内容区域 */}
        <div className="w-full max-w-6xl">
          {error && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 shadow-md">
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
                <div>
                  <p className="font-medium text-red-800">加载失败</p>
                  <p className="mt-1 text-sm text-red-600">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="grid items-start gap-6 lg:grid-cols-3">
            {/* 左侧: 场景图片显示区域 (1列) - 固定位置 */}
            <div className="lg:sticky lg:top-6 lg:col-span-1">
              <ImageDisplay imageUrl={sceneData?.image_url || null} loading={loading} />
            </div>

            {/* 右侧: 信息区域 (2列) - 可滚动 */}
            <div className="space-y-6 lg:col-span-2">
              {/* 场景信息 */}
              <div className="rounded-2xl border-2 border-slate-300 bg-white p-5 shadow-lg transition-shadow duration-300 hover:shadow-xl">
                <h3 className="font-display mb-4 flex items-center text-lg font-bold text-slate-800">
                  <Sparkles className="mr-2 h-5 w-5 text-green-500" />
                  场景信息
                </h3>

                {/* 场景简介 */}
                {sceneData?.scene_brief && (
                  <div className="mb-4 border-b border-slate-200 pb-4">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap text-slate-700">
                      {sceneData.scene_brief}
                    </p>
                  </div>
                )}

                {/* 元信息网格 */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {sceneData?.version && (
                    <div>
                      <p className="mb-1 text-xs text-slate-500">版本</p>
                      <p className="font-medium text-slate-700">{sceneData.version}</p>
                    </div>
                  )}
                  {sceneData?.shots_appeared && sceneData.shots_appeared.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs text-slate-500">出现镜头数</p>
                      <p className="font-medium text-slate-700">
                        {sceneData.shots_appeared.length} 个
                      </p>
                    </div>
                  )}
                  {sceneData?.created_at && (
                    <div className="col-span-2">
                      <p className="mb-1 text-xs text-slate-500">创建时间</p>
                      <p className="font-medium text-slate-700">
                        {new Date(sceneData.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  )}
                </div>

                {/* 镜头列表 */}
                {sceneData?.shots_appeared && sceneData.shots_appeared.length > 0 && (
                  <div className="mt-4 border-t border-slate-200 pt-4">
                    <p className="mb-2 text-xs text-slate-500">出现镜头列表</p>
                    <div className="flex flex-wrap gap-2">
                      {sceneData.shots_appeared.map((shot, idx) => (
                        <span
                          key={idx}
                          className="rounded-full border border-green-200 bg-green-50 px-2.5 py-1 text-xs text-green-700"
                        >
                          {shot}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 场景描述 - Image Prompt */}
              <div className="flex h-[350px] flex-col rounded-2xl border-2 border-slate-300 bg-white p-6 shadow-lg transition-shadow duration-300 hover:shadow-xl">
                <div className="mb-3 flex h-8 flex-shrink-0 items-center">
                  <h3 className="font-display flex items-center text-lg font-bold text-slate-800">
                    <Sparkles className="mr-2 h-5 w-5 text-purple-500" />
                    场景描述
                  </h3>
                </div>
                {loading ? (
                  <div className="flex flex-1 items-center justify-center">
                    <div className="animate-pulse text-slate-400">加载中...</div>
                  </div>
                ) : (
                  <div className="prose max-w-none flex-1 overflow-y-auto">
                    <p className="leading-relaxed whitespace-pre-wrap text-slate-700">
                      {sceneData?.image_prompt || '暂无描述'}
                    </p>
                  </div>
                )}
              </div>

              {/* 创作提示 - Reflection */}
              {sceneData?.reflection && (
                <div className="flex h-[276px] flex-col rounded-2xl border-2 border-slate-300 bg-white p-6 shadow-lg transition-shadow duration-300 hover:shadow-xl">
                  <div className="mb-3 flex h-8 flex-shrink-0 items-center">
                    <h3 className="font-display flex items-center text-lg font-bold text-slate-800">
                      <Sparkles className="mr-2 h-5 w-5 text-yellow-500" />
                      Reflection
                    </h3>
                  </div>
                  {loading ? (
                    <div className="flex flex-1 items-center justify-center">
                      <div className="animate-pulse text-slate-400">加载中...</div>
                    </div>
                  ) : (
                    <div className="prose max-w-none flex-1 overflow-y-auto">
                      <p className="leading-relaxed whitespace-pre-wrap text-slate-700">
                        {sceneData.reflection}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SceneViewer
