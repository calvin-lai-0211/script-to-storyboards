import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { User, Sparkles, AlertCircle, Save, Edit, Wand2 } from 'lucide-react'
import ImageDisplay from '../components/ImageDisplay'
import BackButton from '../components/BackButton'
import { API_ENDPOINTS, apiCall } from '@api'
import { useCharacterStore } from '@store/useCharacterStore'

interface CharacterData {
  character_name: string
  image_prompt: string
  reflection: string
  image_url: string
}

const CharacterViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { currentCharacter, updateCharacter } = useCharacterStore()
  const [characterData, setCharacterData] = useState<CharacterData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditingPrompt, setIsEditingPrompt] = useState<boolean>(false)
  const [editedPrompt, setEditedPrompt] = useState<string>('')
  const [saving, setSaving] = useState<boolean>(false)
  const [generating, setGenerating] = useState<boolean>(false)

  useEffect(() => {
    if (id) {
      fetchCharacterData(id)
    }
  }, [id])

  const fetchCharacterData = async (characterId: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiCall<any>(API_ENDPOINTS.getCharacter(characterId))
      setCharacterData(data as CharacterData)
      setEditedPrompt(data.image_prompt as string)
    } catch (err) {
      console.error('Error fetching character data:', err)
      setError('获取角色数据失败，请检查网络或服务器。')
    } finally {
      setLoading(false)
    }
  }

  const handleSavePrompt = async () => {
    if (!characterData || !id) return

    setSaving(true)
    try {
      await apiCall(API_ENDPOINTS.updateCharacterPrompt(id), {
        method: 'PUT',
        body: JSON.stringify({ image_prompt: editedPrompt })
      })

      setCharacterData({ ...characterData, image_prompt: editedPrompt })
      setIsEditingPrompt(false)
    } catch (err) {
      console.error('Error saving prompt:', err)
      alert('保存失败，请重试。')
    } finally {
      setSaving(false)
    }
  }

  const handleGenerateImage = async () => {
    if (!characterData || !id) return

    // Use editedPrompt if editing, otherwise use current prompt
    const promptToUse = isEditingPrompt ? editedPrompt : characterData.image_prompt

    if (!promptToUse || promptToUse.trim() === '') {
      alert('请先添加角色描述后再生成图片')
      return
    }

    setGenerating(true)
    try {
      const result = await apiCall<any>(API_ENDPOINTS.generateCharacterImage(id), {
        method: 'POST',
        body: JSON.stringify({
          image_prompt: promptToUse
        })
      })

      // Update character data with new image URL and prompt
      const updatedData = {
        ...characterData,
        image_url: result.image_url as string,
        image_prompt: promptToUse
      }
      setCharacterData(updatedData)
      setEditedPrompt(promptToUse)
      setIsEditingPrompt(false)

      // Update store to refresh list page
      if (id) {
        updateCharacter(Number(id), {
          image_url: result.image_url as string,
          image_prompt: promptToUse
        })
      }

      console.debug('Image generated successfully:', result.image_url)
    } catch (err) {
      console.error('Error generating image:', err)
      alert('生成图片失败，请检查网络或稍后重试。')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 返回按钮 - 固定在左上角 */}
      <div className="absolute top-6 left-6 z-10">
        <BackButton to="/characters" label="返回角色列表" />
      </div>

      <div className="relative flex flex-col items-center justify-start px-6 py-8">
        {/* 页面标题区域 */}
        <div className="animate-fade-in mb-8 text-center">
          <div className="mb-4 flex items-center justify-center gap-4">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg">
                <User className="h-6 w-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="h-4 w-4 text-yellow-500" />
              </div>
            </div>
            <p className="text-lg leading-relaxed text-slate-600">
              {currentCharacter?.character_name || characterData?.character_name || '加载中...'}
            </p>
          </div>
          {currentCharacter && (
            <p className="text-sm text-slate-500">
              {currentCharacter.drama_name} - 第{currentCharacter.episode_number}集
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
            {/* 左侧: 肖像显示区域 (1列) */}
            <div className="lg:col-span-1">
              <ImageDisplay imageUrl={characterData?.image_url || null} loading={loading || generating} />
            </div>

            {/* 右侧: 信息区域 (2列) */}
            <div className="space-y-6 lg:col-span-2">
              {/* 创意描述区域 - 可编辑的 Prompt */}
              <div className="flex h-[400px] flex-col rounded-2xl border-2 border-slate-300 bg-white p-6 shadow-lg transition-shadow duration-300 hover:shadow-xl">
                <div className="mb-3 flex h-8 flex-shrink-0 items-center justify-between">
                  <h3 className="font-display flex items-center text-lg font-bold text-slate-800">
                    <Sparkles className="mr-2 h-5 w-5 text-purple-500" />
                    角色描述
                  </h3>
                  {!isEditingPrompt ? (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handleGenerateImage}
                        disabled={generating}
                        className="flex items-center space-x-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 text-white shadow-md transition-all duration-200 hover:from-purple-600 hover:to-pink-600 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <Wand2 className="h-4 w-4" />
                        <span className="text-sm font-medium">
                          {generating ? '生成中...' : '生成图片'}
                        </span>
                      </button>
                      <button
                        onClick={() => setIsEditingPrompt(true)}
                        className="flex items-center space-x-2 rounded-lg bg-blue-50 px-4 py-2 text-blue-700 transition-colors duration-200 hover:bg-blue-100"
                      >
                        <Edit className="h-4 w-4" />
                        <span className="text-sm font-medium">编辑</span>
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setIsEditingPrompt(false)
                          setEditedPrompt(characterData?.image_prompt || '')
                        }}
                        className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200"
                      >
                        取消
                      </button>
                      <button
                        onClick={handleSavePrompt}
                        disabled={saving}
                        className="flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <Save className="h-4 w-4" />
                        <span className="text-sm font-medium">{saving ? '保存中...' : '保存'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {loading ? (
                  <div className="flex flex-1 items-center justify-center">
                    <div className="animate-pulse text-slate-400">加载中...</div>
                  </div>
                ) : isEditingPrompt ? (
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="w-full flex-1 resize-none rounded-xl border border-slate-300 bg-slate-50 p-4 text-slate-800 placeholder-slate-500 transition-colors duration-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-200 focus:outline-none"
                    placeholder="描述角色的外观、服装、表情等细节..."
                  />
                ) : (
                  <div className="prose max-w-none flex-1 overflow-y-auto">
                    <p className="leading-relaxed whitespace-pre-wrap text-slate-700">
                      {characterData?.image_prompt || '暂无描述'}
                    </p>
                  </div>
                )}
              </div>

              {/* 创作提示区域 - 只读的 Reflection */}
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
                      {characterData?.reflection || '暂无创作提示'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CharacterViewer
