import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Save, ArrowLeft, AlertCircle } from 'lucide-react'
import { TiptapEditorLazy } from '../components/TiptapEditorLazy'
import { scriptService, Script } from '../api/scriptService'

export const ScriptEditor: React.FC = () => {
  const { key } = useParams<{ key: string }>()
  const navigate = useNavigate()

  const [script, setScript] = useState<Script | null>(null)
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  // 加载剧本数据
  useEffect(() => {
    const loadScript = async () => {
      if (!key) return

      try {
        setLoading(true)
        setError(null)
        const data = await scriptService.getScript(key)
        setScript(data)
        setContent(data.content || '')
      } catch (err) {
        console.error('Failed to load script:', err)
        setError('加载剧本失败')
      } finally {
        setLoading(false)
      }
    }

    loadScript()
  }, [key])

  // 内容变化处理
  const handleContentChange = (newContent: string) => {
    setContent(newContent)
    setHasChanges(newContent !== (script?.content || ''))
  }

  // 保存剧本
  const handleSave = async () => {
    if (!key || !hasChanges) return

    try {
      setSaving(true)
      setError(null)
      await scriptService.updateScriptContent(key, content)
      setHasChanges(false)

      // 更新 script 对象
      if (script) {
        setScript({ ...script, content })
      }

      // 显示成功提示
      alert('保存成功！')
    } catch (err) {
      console.error('Failed to save script:', err)
      setError('保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  // 返回
  const handleBack = () => {
    if (hasChanges) {
      const confirmed = window.confirm('有未保存的更改，确定要离开吗？')
      if (!confirmed) return
    }
    navigate(-1)
  }

  // 快捷键保存
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        if (hasChanges && !saving) {
          handleSave()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [hasChanges, saving, content])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (error && !script) {
    return (
      <div className="flex h-screen flex-col items-center justify-center">
        <AlertCircle className="mb-4 h-12 w-12 text-red-500" />
        <div className="mb-4 text-red-600">{error}</div>
        <button onClick={handleBack} className="rounded bg-gray-200 px-4 py-2 hover:bg-gray-300">
          返回
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="rounded-lg p-2 transition hover:bg-gray-100"
            title="返回"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{script?.title || '剧本编辑'}</h1>
            <p className="text-sm text-gray-500">
              第 {script?.episode_num} 集{script?.author && ` · ${script.author}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {hasChanges && !error && <span className="text-sm text-amber-600">有未保存的更改</span>}

          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 font-medium transition ${
              hasChanges && !saving
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'cursor-not-allowed bg-gray-200 text-gray-400'
            }`}
            title="保存 (Ctrl+S 或 Cmd+S)"
          >
            <Save size={18} />
            {saving ? '自动保存中...' : '保存'}
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="mx-auto h-full max-w-5xl">
          <TiptapEditorLazy
            content={content}
            onChange={handleContentChange}
            placeholder="开始输入剧本内容..."
            editable={true}
          />
        </div>
      </div>

      {/* Footer Info */}
      <div className="border-t border-gray-200 bg-white px-6 py-2 text-xs text-gray-500">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <span>支持 Markdown 格式</span>
          <span>字数: {content.replace(/<[^>]*>/g, '').length} 字符</span>
        </div>
      </div>
    </div>
  )
}
