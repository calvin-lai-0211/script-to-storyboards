import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Lightbulb, History, Sparkles, Wand2, Upload, X, Image } from 'lucide-react'

interface PromptInputProps {
  onSend: (prompt: string, referenceImageUrl?: string) => void
  loading: boolean
}

const PromptInput: React.FC<PromptInputProps> = ({ onSend, loading }) => {
  const [prompt, setPrompt] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [referenceImage, setReferenceImage] = useState<File | null>(null)
  const [referenceImageUrl, setReferenceImageUrl] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const promptSuggestions = [
    '一只在太空中漂浮的猫，超现实主义风格',
    '未来科幻城市，霓虹灯光，赛博朋克风格',
    '梦幻森林中的精灵，魔法光芒围绕',
    '蒸汽朋克风格的机械龙，青铜色泽',
    '日式庭院中的樱花飘落，水墨画风格'
  ]

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [prompt])

  const handleSend = () => {
    if (prompt.trim() && !loading) {
      onSend(prompt, referenceImageUrl || undefined)
      setPrompt('')
      setShowSuggestions(false)
    }
  }

  const uploadImage = async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('image', file)

    const response = await fetch('http://localhost:8899/api/upload-image', {
      method: 'POST',
      body: formData
    })

    const data = await response.json()

    // Check unified response format
    if (data.code === 0 && data.data) {
      return data.data
    } else {
      throw new Error(data.message || '图片上传失败')
    }
  }

  const handleImageUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('图片大小不能超过10MB')
      return
    }

    setUploading(true)
    try {
      const imageUrl = await uploadImage(file)
      setReferenceImage(file)
      setReferenceImageUrl(imageUrl)
    } catch (error) {
      console.error('图片上传失败:', error)
      alert('图片上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleImageUpload(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      handleImageUpload(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const removeReferenceImage = () => {
    setReferenceImage(null)
    setReferenceImageUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setPrompt(suggestion)
    setShowSuggestions(false)
    textareaRef.current?.focus()
  }

  const characterCount = prompt.length
  const maxCharacters = 500
  const isNearLimit = characterCount > maxCharacters * 0.8

  return (
    <div className="relative">
      {/* 主输入容器 - 提高对比度 */}
      <div
        className={`relative rounded-2xl border-2 bg-white/95 shadow-lg backdrop-blur-sm transition-all duration-300 ${
          isFocused
            ? 'border-blue-400 bg-white shadow-xl'
            : 'border-slate-300 hover:border-slate-400 hover:shadow-xl'
        }`}
      >
        {/* 输入框标题 */}
        <div className="flex items-center justify-between border-b border-slate-200 p-4 pb-3">
          <div className="flex items-center space-x-2">
            <Wand2 className="h-5 w-5 text-blue-600" />
            <span className="font-semibold text-slate-800">创意描述</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="rounded-lg p-2 text-slate-600 transition-colors duration-200 hover:bg-blue-50 hover:text-blue-600"
              title="获取灵感"
            >
              <Lightbulb className="h-4 w-4" />
            </button>
            <button
              className="rounded-lg p-2 text-slate-600 transition-colors duration-200 hover:bg-purple-50 hover:text-purple-600"
              title="历史记录"
            >
              <History className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 输入区域 */}
        <div className="p-4">
          <textarea
            ref={textareaRef}
            className={`w-full resize-none bg-transparent text-slate-800 placeholder-slate-500 transition-all duration-200 focus:outline-none ${
              loading ? 'cursor-not-allowed opacity-70' : ''
            }`}
            rows={3}
            placeholder="描述你想要创作的图像... (例如: 一个梦幻的城堡在云端，周围有彩虹和独角兽)"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, maxCharacters))}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={loading}
            style={{ minHeight: '80px', maxHeight: '200px' }}
          />

          {/* 图片上传区域 */}
          <div className="mt-4">
            {/* 参考图片上传 */}
            {!referenceImage && (
              <div
                className={`relative cursor-pointer rounded-xl border-2 border-dashed p-4 transition-all duration-300 ${
                  dragOver
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-slate-300 hover:border-slate-400 hover:bg-slate-50'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="flex flex-col items-center justify-center space-y-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
                    {uploading ? (
                      <Loader2 className="h-5 w-5 animate-spin text-slate-600" />
                    ) : (
                      <Upload className="h-5 w-5 text-slate-600" />
                    )}
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-slate-700">
                      {uploading ? '上传中...' : '上传参考图片（可选）'}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      点击选择或拖拽图片到此区域，支持 JPG、PNG 格式，最大 10MB
                    </p>
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading || loading}
                />
              </div>
            )}

            {/* 参考图片预览 */}
            {referenceImage && referenceImageUrl && (
              <div className="relative">
                <div className="flex items-center space-x-3 rounded-xl border border-blue-200 bg-blue-50 p-3">
                  <div className="h-12 w-12 overflow-hidden rounded-lg border border-blue-200 bg-white">
                    <img
                      src={referenceImageUrl}
                      alt="参考图片"
                      className="h-full w-full object-cover"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <Image className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">参考图片</span>
                    </div>
                    <p className="mt-1 text-xs text-blue-600">{referenceImage.name}</p>
                  </div>
                  <button
                    onClick={removeReferenceImage}
                    className="rounded-lg p-1.5 text-blue-600 transition-colors duration-200 hover:bg-red-50 hover:text-red-600"
                    title="删除参考图片"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 底部控制栏 */}
          <div className="mt-3 flex items-center justify-between border-t border-slate-200 pt-3">
            <div className="flex items-center space-x-3 text-sm">
              <span
                className={`transition-colors duration-200 ${
                  isNearLimit ? 'text-orange-600' : 'text-slate-600'
                }`}
              >
                {characterCount}/{maxCharacters}
              </span>
              {prompt.length > 0 && (
                <div className="flex items-center space-x-1 text-green-600">
                  <Sparkles className="h-3 w-3" />
                  <span className="text-xs font-medium">准备就绪</span>
                </div>
              )}
            </div>

            {/* 发送按钮 */}
            <button
              onClick={handleSend}
              disabled={!prompt.trim() || loading}
              className={`group relative overflow-hidden rounded-xl px-6 py-3 font-semibold transition-all duration-300 ${
                !prompt.trim() || loading
                  ? 'cursor-not-allowed bg-slate-200 text-slate-500'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:scale-105 hover:shadow-xl active:scale-95'
              }`}
            >
              <div className="relative flex items-center space-x-2">
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>创作中...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
                    <span>生成图像</span>
                  </>
                )}
              </div>
            </button>
          </div>
          {/* 快捷键提示 */}
          {isFocused && !loading && (
            <div className="animate-fade-in absolute -bottom-6 left-4 z-20 text-xs text-slate-500">
              按 Enter 发送，Shift + Enter 换行
            </div>
          )}
        </div>
      </div>

      {/* 建议提示词面板 */}
      {showSuggestions && (
        <div className="animate-slide-down absolute top-full right-0 left-0 z-10 mt-2 rounded-xl border border-slate-300 bg-white/95 p-4 shadow-xl backdrop-blur-sm">
          <div className="mb-3 flex items-center space-x-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            <span className="font-semibold text-slate-800">创意建议</span>
          </div>
          <div className="space-y-2">
            {promptSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full rounded-lg border border-transparent bg-slate-50 p-3 text-left text-sm text-slate-700 transition-all duration-200 hover:border-blue-200 hover:bg-blue-50 hover:text-slate-900"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PromptInput
