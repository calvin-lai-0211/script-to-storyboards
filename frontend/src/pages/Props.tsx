import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, Loader2, AlertCircle, Star, RefreshCw } from 'lucide-react'
import { API_ENDPOINTS, apiCall } from '@api'
import { usePropStore } from '@store/usePropStore'

interface Prop {
  id: number
  drama_name: string
  episode_number: number
  prop_name: string
  image_url: string | null
  image_prompt: string
  reflection: string | null
  version: string
  shots_appeared: string[] | null
  is_key_prop: boolean | null
  prop_brief: string | null
  created_at: string
}

const Props: React.FC = () => {
  const navigate = useNavigate()
  const { allProps, setAllProps, setCurrentProp } = usePropStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Use cached data if available
  const propList = allProps || []

  useEffect(() => {
    // If already in store, skip fetch
    if (allProps) {
      console.debug('Props: Using cached data')
      return
    }

    const abortController = new AbortController()
    fetchProps(abortController.signal)

    return () => {
      abortController.abort()
    }
  }, [allProps])

  const fetchProps = async (signal?: AbortSignal) => {
    try {
      setLoading(true)
      setError(null)

      if (signal?.aborted) return

      console.debug('Props: Fetching from API')
      const data = await apiCall<{ props: Prop[]; count: number }>(API_ENDPOINTS.getAllProps(), {
        signal
      })

      if (signal?.aborted) return

      setAllProps(data.props)
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        console.debug('Props fetch cancelled')
        return
      }
      console.error('Error fetching props:', err)
      setError('获取道具数据失败')
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }

  const handleRefresh = () => {
    fetchProps()
  }

  const handlePropClick = (prop: Prop) => {
    setCurrentProp(prop)
    navigate(`/prop/${prop.id}`)
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-purple-500" />
          <p className="text-slate-600">加载道具数据中...</p>
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
            onClick={() => fetchProps()}
            className="rounded-lg bg-purple-500 px-6 py-2 text-white transition-colors hover:bg-purple-600"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // Sort by id ascending
  const sortedProps = [...propList].sort((a, b) => a.id - b.id)

  return (
    <div className="h-full overflow-auto bg-slate-50">
      <div className="mx-auto max-w-7xl p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 flex items-center text-3xl font-bold text-slate-800">
              <Package className="mr-3 h-8 w-8 text-purple-500" />
              道具
            </h1>
            <p className="text-slate-600">共 {propList.length} 个道具</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 rounded-lg bg-purple-500 px-4 py-2 text-white transition-colors hover:bg-purple-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 道具列表 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {sortedProps.map((prop) => (
            <div
              key={prop.id}
              onClick={() => handlePropClick(prop)}
              className="group cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-300 hover:border-purple-400 hover:shadow-xl"
            >
              {prop.image_url ? (
                <img
                  src={prop.image_url}
                  alt={prop.prop_name}
                  className="h-48 w-full object-cover transition-transform duration-300 hover:scale-105"
                />
              ) : (
                <div className="flex h-48 w-full items-center justify-center bg-gradient-to-br from-purple-100 to-pink-100">
                  <Package className="h-16 w-16 text-slate-400" />
                </div>
              )}
              <div className="p-4">
                <div className="mb-2 flex items-start justify-between">
                  <h3 className="flex-1 font-bold text-slate-800">{prop.prop_name}</h3>
                  {prop.is_key_prop && (
                    <span title="关键道具">
                      <Star className="ml-2 h-4 w-4 flex-shrink-0 fill-amber-400 text-amber-500" />
                    </span>
                  )}
                </div>

                <p className="mb-2 text-xs text-slate-600">
                  {prop.drama_name} - 第{prop.episode_number}集
                </p>

                {prop.prop_brief && (
                  <p className="mb-2 line-clamp-2 text-xs text-slate-500">{prop.prop_brief}</p>
                )}

                {prop.shots_appeared && prop.shots_appeared.length > 0 && (
                  <div className="mb-2 text-xs text-slate-500">
                    <span className="font-medium">出现镜头: </span>
                    {prop.shots_appeared.length} 个
                  </div>
                )}

                {prop.version && <div className="text-xs text-slate-400">版本: {prop.version}</div>}

                <p className="mt-2 text-xs text-slate-500">ID: {prop.id}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {sortedProps.length === 0 && (
          <div className="py-16 text-center">
            <Package className="mx-auto mb-4 h-16 w-16 text-slate-300" />
            <p className="text-slate-500">暂无道具数据</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Props
