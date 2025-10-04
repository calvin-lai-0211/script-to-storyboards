import React, { useState, useEffect } from 'react'
import { Loader2, AlertCircle, FileText, RefreshCw, Edit, Save, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { API_ENDPOINTS, apiCall } from '@api'
import { useEpisodeStore } from '@store/useEpisodeStore'
import { TiptapEditorLazy } from '../TiptapEditorLazy'
import { scriptService } from '../../api/scriptService'

interface ScriptTabProps {
  scriptKey: string
}

interface ScriptData {
  key: string
  title: string
  episode_num: number
  content: string
  roles: string[]
  sceneries: string[]
  author: string | null
  creation_year: number | null
}

const ScriptTab: React.FC<ScriptTabProps> = ({ scriptKey }) => {
  const { getEpisode, setEpisode, setCurrentEpisode, currentEpisode } = useEpisodeStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [lastSavedContent, setLastSavedContent] = useState('')

  // Get episode from store
  const episode = getEpisode(scriptKey)

  useEffect(() => {
    // If already in store, skip fetch
    if (episode) {
      console.debug('ScriptTab: Using cached episode')
      return
    }

    // Only fetch if no cache
    fetchEpisode()
  }, [scriptKey, getEpisode])

  const fetchEpisode = async () => {
    try {
      setLoading(true)
      setError(null)

      console.debug('ScriptTab fetching episode with key:', scriptKey)
      const data = await apiCall<ScriptData>(API_ENDPOINTS.getScript(scriptKey))

      setEpisode(scriptKey, data)

      // Also update currentEpisode if not set or different
      if (!currentEpisode || currentEpisode.key !== scriptKey) {
        setCurrentEpisode(data)
      }
    } catch (err) {
      console.error('Error fetching episode:', err)
      setError('获取剧本失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    console.debug('ScriptTab: Manually refreshing episode')
    fetchEpisode()
  }

  // 进入编辑模式
  const handleEdit = () => {
    if (episode) {
      const content = episode.content || ''
      setEditContent(content)
      setLastSavedContent(content)
      setIsEditing(true)
    }
  }

  // 取消编辑
  const handleCancelEdit = () => {
    if (editContent !== (episode?.content || '')) {
      const confirmed = window.confirm('有未保存的更改，确定要取消吗？')
      if (!confirmed) return
    }
    setIsEditing(false)
    setEditContent('')
  }

  // 保存编辑
  const handleSave = async (silent = false) => {
    if (!scriptKey) return

    // 如果内容没有变化，跳过保存
    if (editContent === lastSavedContent) {
      console.debug('ScriptTab: Content unchanged, skipping save')
      return
    }

    try {
      setSaving(true)
      setError(null)
      await scriptService.updateScriptContent(scriptKey, editContent)

      // 更新本地 store
      if (episode) {
        const updatedEpisode = { ...episode, content: editContent }
        setEpisode(scriptKey, updatedEpisode)
      }

      setLastSavedContent(editContent)

      if (!silent) {
        setIsEditing(false)
        alert('保存成功！')
      } else {
        console.debug('ScriptTab: Auto-saved successfully')
      }
    } catch (err) {
      console.error('Failed to save script:', err)
      if (!silent) {
        setError('保存失败，请重试')
      }
    } finally {
      setSaving(false)
    }
  }

  // 自动保存（每 5 秒）
  useEffect(() => {
    if (!isEditing) return

    const timer = setInterval(() => {
      if (!saving) {
        handleSave(true) // silent = true，不弹窗不退出编辑
      }
    }, 5000)

    return () => clearInterval(timer)
  }, [isEditing, editContent, saving, lastSavedContent])

  // 快捷键保存
  useEffect(() => {
    if (!isEditing) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        if (!saving) {
          handleSave()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isEditing, saving, editContent])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-blue-500" />
          <p className="text-slate-600">加载剧本中...</p>
        </div>
      </div>
    )
  }

  if (error || !episode) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-500" />
          <p className="text-red-600">{error || '剧本不存在'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* 工具栏 */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white p-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-blue-500" />
            <span className="font-medium text-slate-800">
              {episode.title} - 第 {episode.episode_num} 集
            </span>
          </div>

          {!isEditing && episode.roles && episode.roles.length > 0 && (
            <div className="text-sm text-slate-600">角色: {episode.roles.join(', ')}</div>
          )}

          {isEditing && <span className="text-sm font-medium text-amber-600">编辑模式</span>}
        </div>

        <div className="flex items-center space-x-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {!isEditing && episode.author && (
            <div className="text-sm text-slate-600">作者: {episode.author}</div>
          )}

          {!isEditing ? (
            <>
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="flex items-center space-x-2 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
                title="刷新剧本"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                <span>刷新</span>
              </button>

              <button
                onClick={handleEdit}
                className="flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                title="编辑剧本"
              >
                <Edit className="h-4 w-4" />
                <span>编辑</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCancelEdit}
                disabled={saving}
                className="flex items-center space-x-2 rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
                title="取消编辑"
              >
                <X className="h-4 w-4" />
                <span>取消</span>
              </button>

              <button
                onClick={() => handleSave()}
                disabled={saving}
                className="flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
                title="保存 (Ctrl+S 或 Cmd+S)"
              >
                <Save className="h-4 w-4" />
                <span>{saving ? '保存中...' : '保存'}</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* 剧本内容 */}
      <div className="flex-1 overflow-auto bg-slate-50">
        <div className="mx-auto max-w-5xl p-6">
          {!isEditing ? (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="prose p-8">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="whitespace-pre-wrap">{children}</p>
                  }}
                >
                  {episode.content}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="h-full">
              <TiptapEditorLazy
                content={editContent}
                onChange={setEditContent}
                placeholder="开始输入剧本内容..."
                editable={true}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ScriptTab
