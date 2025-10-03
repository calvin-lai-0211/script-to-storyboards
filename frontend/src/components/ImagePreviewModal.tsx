import React, { useEffect, useState } from "react";
import { X, Download, ZoomIn, ZoomOut, RotateCw } from "lucide-react";

interface ImagePreviewModalProps {
  imageUrl: string;
  onClose: () => void;
}

const ImagePreviewModal: React.FC<ImagePreviewModalProps> = ({
  imageUrl,
  onClose,
}) => {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);

  // ESC 键关闭
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  // 阻止背景滚动
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, []);

  const handleDownload = async () => {
    try {
      // 使用 fetch 获取图片，转为 blob，避免跨域问题
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `ai-generated-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 清理 blob URL
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("下载失败:", error);
      alert("下载失败，请稍后重试");
    }
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const handleReset = () => {
    setScale(1);
    setRotation(0);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      {/* 顶部工具栏 */}
      <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between bg-gradient-to-b from-black/50 to-transparent z-10">
        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleZoomOut();
            }}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200"
            title="缩小"
          >
            <ZoomOut className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleZoomIn();
            }}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200"
            title="放大"
          >
            <ZoomIn className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleRotate();
            }}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200"
            title="旋转"
          >
            <RotateCw className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleReset();
            }}
            className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200 text-white text-sm"
            title="重置"
          >
            重置
          </button>
          <span className="text-white text-sm ml-2">
            {Math.round(scale * 100)}%
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDownload();
            }}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200"
            title="下载图片"
          >
            <Download className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors duration-200"
            title="关闭 (ESC)"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>

      {/* 图片容器 */}
      <div
        className="relative max-w-[95vw] max-h-[95vh] flex items-center justify-center"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={imageUrl}
          alt="预览"
          className="max-w-full max-h-[95vh] object-contain transition-all duration-300 ease-out"
          style={{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: "center center",
          }}
          draggable={false}
        />
      </div>

      {/* 底部提示 */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white/60 text-sm">
        点击空白处或按 ESC 键关闭
      </div>
    </div>
  );
};

export default ImagePreviewModal;
