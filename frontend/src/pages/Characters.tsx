import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Loader2, AlertCircle, RefreshCw, Search, X } from 'lucide-react'
import { API_ENDPOINTS, apiCall } from '@api'
import { useCharacterStore } from '@store/useCharacterStore'

interface Character {
  id: number
  drama_name: string
  episode_number: number
  character_name: string
  image_url: string | null
  image_prompt: string
  is_key_character: boolean
}

const Characters: React.FC = () => {
  const navigate = useNavigate()
  const { allCharacters, setAllCharacters, setCurrentCharacter } = useCharacterStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  // Use cached data if available
  const characters = allCharacters || []

  useEffect(() => {
    // If already in store, skip fetch
    if (allCharacters) {
      console.debug('Characters: Using cached data')
      return
    }

    fetchCharacters()
  }, [allCharacters])

  const fetchCharacters = async () => {
    try {
      setLoading(true)
      setError(null)

      console.debug('Characters: Fetching from API')
      const data = await apiCall<{ characters: Character[]; count: number }>(
        API_ENDPOINTS.getAllCharacters()
      )

      setAllCharacters(data.characters)
    } catch (err) {
      console.error('Error fetching characters:', err)
      setError('获取角色数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCharacterClick = (character: Character) => {
    setCurrentCharacter(character)
    navigate(`/character/${character.id}`)
  }

  const handleImageClick = (e: React.MouseEvent, imageUrl: string) => {
    e.stopPropagation() // Prevent card click
    setPreviewImage(imageUrl)
  }

  const handleRefresh = () => {
    fetchCharacters()
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-blue-500" />
          <p className="text-slate-600">加载角色数据中...</p>
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
            onClick={() => fetchCharacters()}
            className="rounded-lg bg-blue-500 px-6 py-2 text-white transition-colors hover:bg-blue-600"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // Sort by id ascending
  const sortedCharacters = [...characters].sort((a, b) => a.id - b.id)

  return (
    <div className="h-full overflow-auto bg-slate-50">
      <div className="mx-auto max-w-7xl p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="mb-2 flex items-center text-3xl font-bold text-slate-800">
              <User className="mr-3 h-8 w-8 text-blue-500" />
              角色
            </h1>
            <p className="text-slate-600">共 {characters.length} 个角色</p>
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

        {/* 角色列表 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {sortedCharacters.map((character) => (
            <div
              key={character.id}
              onClick={() => handleCharacterClick(character)}
              className="group cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-300 hover:border-blue-400 hover:shadow-xl"
            >
              {character.image_url ? (
                <div
                  className="relative h-48 w-full overflow-hidden"
                  onClick={(e) => handleImageClick(e, character.image_url!)}
                >
                  <img
                    src={character.image_url}
                    alt={character.character_name}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors duration-300 group-hover:bg-black/10">
                    <Search className="h-8 w-8 text-white opacity-0 transition-opacity duration-300 group-hover:opacity-80" />
                  </div>
                </div>
              ) : (
                <div className="flex h-48 w-full items-center justify-center bg-gradient-to-br from-blue-100 to-purple-100">
                  <User className="h-16 w-16 text-slate-400" />
                </div>
              )}
              <div className="p-4">
                <h3 className="mb-1 font-bold text-slate-800">{character.character_name}</h3>
                <p className="mb-2 text-xs text-slate-600">
                  {character.drama_name} - 第{character.episode_number}集
                </p>
                {character.is_key_character && (
                  <span className="mb-2 inline-block rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-700">
                    关键角色
                  </span>
                )}
                <p className="text-xs text-slate-500">ID: {character.id}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {sortedCharacters.length === 0 && (
          <div className="py-16 text-center">
            <User className="mx-auto mb-4 h-16 w-16 text-slate-300" />
            <p className="text-slate-500">暂无角色数据</p>
          </div>
        )}
      </div>

      {/* 图片预览模态框 */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-4"
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

export default Characters
