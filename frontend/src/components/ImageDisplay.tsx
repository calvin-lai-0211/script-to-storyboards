import React, { useState } from 'react'
import { ImageIcon, Maximize2, Sparkles, Camera } from 'lucide-react'
import ImagePreviewModal from './ImagePreviewModal'

interface ImageDisplayProps {
  imageUrl: string | null
  loading?: boolean
}

const ImageDisplay: React.FC<ImageDisplayProps> = ({ imageUrl, loading = false }) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const handlePreview = () => {
    if (imageUrl) {
      setShowPreview(true)
    }
  }

  return (
    <div className="group relative">
      {/* 主容器 - 简化设计 */}
      <div
        className="relative h-96 w-full overflow-hidden rounded-2xl border-2 border-slate-300 bg-white/95 shadow-lg backdrop-blur-sm transition-all duration-300 hover:border-slate-400 hover:shadow-xl lg:h-[700px]"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* 统一背景样式 */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-slate-50/80"></div>

        {/* 装饰性网格 - 降低透明度 */}
        {!imageUrl && !loading && (
          <div className="absolute inset-0 opacity-10">
            <div
              className="h-full w-full"
              style={{
                backgroundImage: `
                linear-gradient(rgba(148, 163, 184, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.3) 1px, transparent 1px)
              `,
                backgroundSize: '30px 30px'
              }}
            ></div>
          </div>
        )}

        {/* 加载状态 */}
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/95 backdrop-blur-sm">
            {/* 加载动画 */}
            <div className="relative mb-6">
              <div className="h-16 w-16 animate-spin rounded-full border-4 border-slate-200 border-t-blue-500"></div>
              <div
                className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-4 border-transparent border-r-purple-500"
                style={{
                  animationDirection: 'reverse',
                  animationDuration: '1.5s'
                }}
              ></div>
            </div>

            {/* 生成进度文字 */}
            <div className="text-center">
              <div className="mb-2 flex items-center space-x-2">
                <Sparkles className="h-5 w-5 animate-pulse text-blue-500" />
                <span className="text-lg font-semibold text-slate-800">AI 正在创作中</span>
                <Sparkles className="h-5 w-5 animate-pulse text-purple-500" />
              </div>
              <p className="text-sm text-slate-600">请稍候，正在将您的想象转化为现实...</p>
            </div>

            {/* 波浪动画 */}
            <div className="absolute right-0 bottom-0 left-0 h-1 bg-gradient-to-r from-blue-400 to-purple-400">
              <div className="animate-shimmer h-full bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
            </div>
          </div>
        )}

        {/* 图片显示 */}
        {imageUrl && (
          <>
            <img
              src={imageUrl}
              alt="AI Generated Artwork"
              className={`h-full w-full cursor-pointer object-contain transition-all duration-700 ${
                imageLoaded ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
              } ${isHovered ? 'scale-105' : 'scale-100'}`}
              onLoad={() => setImageLoaded(true)}
              onClick={handlePreview}
              style={{
                filter: isHovered ? 'brightness(1.05) contrast(1.05)' : 'none'
              }}
            />

            {/* 悬停时的操作按钮 */}
            <div
              className={`absolute top-4 right-4 flex space-x-2 transition-all duration-300 ${
                isHovered ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0'
              }`}
            >
              <button
                onClick={handlePreview}
                className="group rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur-sm transition-all duration-200 hover:scale-110 hover:bg-white"
                title="全屏查看"
              >
                <Maximize2 className="h-5 w-5 text-slate-700 group-hover:text-blue-600" />
              </button>
            </div>

            {/* 底部信息栏 */}
            <div
              className={`absolute right-0 bottom-0 left-0 bg-gradient-to-t from-slate-800/80 to-transparent p-4 transition-all duration-300 ${
                isHovered ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
              }`}
            >
              <div className="flex items-center justify-between text-white">
                <div className="flex items-center space-x-2">
                  <Camera className="h-4 w-4" />
                  <span className="text-sm font-medium">AI Generated</span>
                </div>
                <div className="text-xs opacity-90">{new Date().toLocaleDateString()}</div>
              </div>
            </div>
          </>
        )}

        {/* 空状态 */}
        {!imageUrl && !loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="relative mb-6">
              <div className="animate-float flex h-24 w-24 items-center justify-center rounded-2xl border border-slate-200 bg-gradient-to-br from-blue-100 to-purple-100">
                <ImageIcon className="h-12 w-12 text-slate-600" />
              </div>
              <div className="absolute -top-2 -right-2">
                <Sparkles className="h-6 w-6 animate-pulse text-yellow-500" />
              </div>
            </div>

            <div className="max-w-xs text-center">
              <h3 className="mb-2 text-xl font-semibold text-slate-800">等待创作</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                在右侧输入你的创意提示，让AI为你创造独特的艺术作品
              </p>
            </div>

            {/* 装饰性元素 */}
            <div className="absolute top-8 left-8 h-2 w-2 animate-pulse rounded-full bg-blue-400"></div>
            <div className="absolute top-12 right-12 h-1 w-1 animate-pulse rounded-full bg-purple-400 delay-500"></div>
            <div className="absolute bottom-16 left-12 h-1.5 w-1.5 animate-pulse rounded-full bg-pink-400 delay-1000"></div>
          </div>
        )}
      </div>

      {/* 底部阴影 */}
      <div className="absolute -bottom-4 left-1/2 h-4 w-3/4 -translate-x-1/2 transform bg-gradient-to-r from-transparent via-slate-300/30 to-transparent blur-lg"></div>

      {/* 图片预览浮层 */}
      {showPreview && imageUrl && (
        <ImagePreviewModal imageUrl={imageUrl} onClose={() => setShowPreview(false)} />
      )}
    </div>
  )
}

export default ImageDisplay
