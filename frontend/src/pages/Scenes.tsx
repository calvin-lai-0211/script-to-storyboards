import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, Loader2, AlertCircle, RefreshCw, Search, X } from 'lucide-react'
import { API_ENDPOINTS, apiCall } from '@api'
import { useSceneStore } from '@store/useSceneStore'

interface Scene {
  id: number
  drama_name: string
  episode_number: number
  scene_name: string
  image_url: string | null
  image_prompt: string
}

const Scenes: React.FC = () => {
  const navigate = useNavigate()
  const { allScenes, setAllScenes, setCurrentScene } = useSceneStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  // Use cached data if available
  const scenes = allScenes || []

  useEffect(() => {
    // If already in store, skip fetch
    if (allScenes) {
      console.debug('Scenes: Using cached data')
      return
    }

    fetchScenes()
  }, [allScenes])

  const fetchScenes = async () => {
    try {
      setLoading(true)
      setError(null)

      console.debug('Scenes: Fetching from API')
      const data = await apiCall<{ scenes: Scene[]; count: number }>(API_ENDPOINTS.getAllScenes())

      setAllScenes(data.scenes)
    } catch (err) {
      console.error('Error fetching scenes:', err)
      setError('获取场景数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSceneClick = (scene: Scene) => {
    setCurrentScene(scene)
    navigate(`/scene/${scene.id}`)
  }

  const handleImageClick = (e: React.MouseEvent, imageUrl: string) => {
    e.stopPropagation() // Prevent card click
    setPreviewImage(imageUrl)
  }

  const handleRefresh = () => {
    fetchScenes()
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-green-500" />
          <p className="text-slate-600">加载场景数据中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-500" />
          <p className="mb-4 text-red-600">{error}</p>
          <button
            onClick={() => fetchScenes()}
            className="rounded-lg bg-green-500 px-6 py-2 text-white transition-colors hover:bg-green-600"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // Sort by id ascending
  const sortedScenes = [...scenes].sort((a, b) => a.id - b.id)

  return (
    <div className="h-full overflow-auto bg-slate-50">
      <div className="mx-auto max-w-7xl p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 flex items-center text-3xl font-bold text-slate-800">
              <MapPin className="mr-3 h-8 w-8 text-green-500" />
              场景
            </h1>
            <p className="text-slate-600">共 {scenes.length} 个场景</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 rounded-lg bg-green-500 px-4 py-2 text-white transition-colors hover:bg-green-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 场景列表 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {sortedScenes.map((scene) => (
            <div
              key={scene.id}
              onClick={() => handleSceneClick(scene)}
              className="group cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-300 hover:border-green-400 hover:shadow-xl"
            >
              {scene.image_url ? (
                <div
                  className="relative h-48 w-full overflow-hidden"
                  onClick={(e) => handleImageClick(e, scene.image_url!)}
                >
                  <img
                    src={scene.image_url}
                    alt={scene.scene_name}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors duration-300 group-hover:bg-black/10">
                    <Search className="h-8 w-8 text-white opacity-0 transition-opacity duration-300 group-hover:opacity-80" />
                  </div>
                </div>
              ) : (
                <div className="flex h-48 w-full items-center justify-center bg-gradient-to-br from-green-100 to-teal-100">
                  <MapPin className="h-16 w-16 text-slate-400" />
                </div>
              )}
              <div className="p-4">
                <h3 className="mb-1 font-bold text-slate-800">{scene.scene_name}</h3>
                <p className="mb-2 text-xs text-slate-600">
                  {scene.drama_name} - 第{scene.episode_number}集
                </p>
                <p className="text-xs text-slate-500">ID: {scene.id}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {sortedScenes.length === 0 && (
          <div className="py-16 text-center">
            <MapPin className="mx-auto mb-4 h-16 w-16 text-slate-300" />
            <p className="text-slate-500">暂无场景数据</p>
          </div>
        )}
      </div>

      {/* 图片预览模态框 */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <button
            onClick={() => setPreviewImage(null)}
            className="absolute top-4 right-4 rounded-full bg-white/10 p-2 transition-colors hover:bg-white/20"
          >
            <X className="h-6 w-6 text-white" />
          </button>
          <img
            src={previewImage}
            alt="Preview"
            className="max-h-full max-w-full rounded-lg object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}

export default Scenes
