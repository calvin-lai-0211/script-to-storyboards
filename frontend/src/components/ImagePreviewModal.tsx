import React, { useEffect, useState } from 'react'
import { X, Download, ZoomIn, ZoomOut, RotateCw } from 'lucide-react'

interface ImagePreviewModalProps {
  imageUrl: string
  onClose: () => void
}

const ImagePreviewModal: React.FC<ImagePreviewModalProps> = ({ imageUrl, onClose }) => {
  const [scale, setScale] = useState(1)
  const [rotation, setRotation] = useState(0)

  // ESC 键关闭
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  // 阻止背景滚动
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  const handleDownload = async () => {
    try {
      // 使用 fetch 获取图片，转为 blob，避免跨域问题
      const response = await fetch(imageUrl)
      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `ai-generated-${Date.now()}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // 清理 blob URL
      URL.revokeObjectURL(blobUrl)
    } catch (error) {
      console.error('下载失败:', error)
      alert('下载失败，请稍后重试')
    }
  }

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3))
  }

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5))
  }

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360)
  }

  const handleReset = () => {
    setScale(1)
    setRotation(0)
  }

  return (
    <div
      className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
      onClick={onClose}
    >
      {/* 顶部工具栏 */}
      <div className="absolute top-0 right-0 left-0 z-10 flex items-center justify-between bg-gradient-to-b from-black/50 to-transparent p-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleZoomOut()
            }}
            className="rounded-lg bg-white/10 p-2 transition-colors duration-200 hover:bg-white/20"
            title="缩小"
          >
            <ZoomOut className="h-5 w-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleZoomIn()
            }}
            className="rounded-lg bg-white/10 p-2 transition-colors duration-200 hover:bg-white/20"
            title="放大"
          >
            <ZoomIn className="h-5 w-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleRotate()
            }}
            className="rounded-lg bg-white/10 p-2 transition-colors duration-200 hover:bg-white/20"
            title="旋转"
          >
            <RotateCw className="h-5 w-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleReset()
            }}
            className="rounded-lg bg-white/10 px-3 py-2 text-sm text-white transition-colors duration-200 hover:bg-white/20"
            title="重置"
          >
            重置
          </button>
          <span className="ml-2 text-sm text-white">{Math.round(scale * 100)}%</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleDownload()
            }}
            className="rounded-lg bg-white/10 p-2 transition-colors duration-200 hover:bg-white/20"
            title="下载图片"
          >
            <Download className="h-5 w-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onClose()
            }}
            className="rounded-lg bg-white/10 p-2 transition-colors duration-200 hover:bg-white/20"
            title="关闭 (ESC)"
          >
            <X className="h-5 w-5 text-white" />
          </button>
        </div>
      </div>

      {/* 图片容器 */}
      <div
        className="relative flex max-h-[95vh] max-w-[95vw] items-center justify-center"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={imageUrl}
          alt="预览"
          className="max-h-[95vh] max-w-full object-contain transition-all duration-300 ease-out"
          style={{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: 'center center'
          }}
          draggable={false}
        />
      </div>

      {/* 底部提示 */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 transform text-sm text-white/60">
        点击空白处或按 ESC 键关闭
      </div>
    </div>
  )
}

export default ImagePreviewModal
