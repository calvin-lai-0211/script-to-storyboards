import React, { useState } from 'react';
import { ImageIcon, Download, Maximize2, Sparkles, Camera } from 'lucide-react';

interface ImageDisplayProps {
  imageUrl: string | null;
  loading?: boolean;
}

const ImageDisplay: React.FC<ImageDisplayProps> = ({ imageUrl, loading = false }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleDownload = () => {
    if (imageUrl) {
      const link = document.createElement('a');
      link.href = imageUrl;
      link.download = `ai-generated-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="relative group">
      {/* 主容器 - 简化设计 */}
      <div
        className="relative w-full h-96 lg:h-[700px] rounded-2xl overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-slate-300 shadow-lg transition-all duration-300 hover:shadow-xl hover:border-slate-400"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* 统一背景样式 */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-slate-50/80"></div>

        {/* 装饰性网格 - 降低透明度 */}
        {!imageUrl && !loading && (
          <div className="absolute inset-0 opacity-10">
            <div className="h-full w-full" style={{
              backgroundImage: `
                linear-gradient(rgba(148, 163, 184, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.3) 1px, transparent 1px)
              `,
              backgroundSize: '30px 30px'
            }}></div>
          </div>
        )}

        {/* 加载状态 */}
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/95 backdrop-blur-sm">
            {/* 加载动画 */}
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-slate-200 border-t-blue-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-purple-500 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
            </div>

            {/* 生成进度文字 */}
            <div className="text-center">
              <div className="flex items-center space-x-2 mb-2">
                <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
                <span className="text-lg font-semibold text-slate-800">AI 正在创作中</span>
                <Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />
              </div>
              <p className="text-sm text-slate-600">请稍候，正在将您的想象转化为现实...</p>
            </div>

            {/* 波浪动画 */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-purple-400">
              <div className="h-full bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer"></div>
            </div>
          </div>
        )}

        {/* 图片显示 */}
        {imageUrl && (
          <>
            <img
              src={imageUrl}
              alt="AI Generated Artwork"
              className={`w-full h-full object-contain transition-all duration-700 ${
                imageLoaded ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
              } ${isHovered ? 'scale-105' : 'scale-100'}`}
              onLoad={() => setImageLoaded(true)}
              style={{ filter: isHovered ? 'brightness(1.05) contrast(1.05)' : 'none' }}
            />

            {/* 悬停时的操作按钮 */}
            <div className={`absolute top-4 right-4 flex space-x-2 transition-all duration-300 ${
              isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
            }`}>
              <button
                onClick={handleDownload}
                className="p-3 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg hover:bg-white hover:scale-110 transition-all duration-200 group border border-slate-200"
                title="下载图片"
              >
                <Download className="w-5 h-5 text-slate-700 group-hover:text-blue-600" />
              </button>
              <button
                className="p-3 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg hover:bg-white hover:scale-110 transition-all duration-200 group border border-slate-200"
                title="全屏查看"
              >
                <Maximize2 className="w-5 h-5 text-slate-700 group-hover:text-blue-600" />
              </button>
            </div>

            {/* 底部信息栏 */}
            <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-800/80 to-transparent p-4 transition-all duration-300 ${
              isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}>
              <div className="flex items-center justify-between text-white">
                <div className="flex items-center space-x-2">
                  <Camera className="w-4 h-4" />
                  <span className="text-sm font-medium">AI Generated</span>
                </div>
                <div className="text-xs opacity-90">
                  {new Date().toLocaleDateString()}
                </div>
              </div>
            </div>
          </>
        )}

        {/* 空状态 */}
        {!imageUrl && !loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="relative mb-6">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center border border-slate-200 animate-float">
                <ImageIcon className="w-12 h-12 text-slate-600" />
              </div>
              <div className="absolute -top-2 -right-2">
                <Sparkles className="w-6 h-6 text-yellow-500 animate-pulse" />
              </div>
            </div>

            <div className="text-center max-w-xs">
              <h3 className="text-xl font-semibold text-slate-800 mb-2">等待创作</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                在右侧输入你的创意提示，让AI为你创造独特的艺术作品
              </p>
            </div>

            {/* 装饰性元素 */}
            <div className="absolute top-8 left-8 w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            <div className="absolute top-12 right-12 w-1 h-1 bg-purple-400 rounded-full animate-pulse delay-500"></div>
            <div className="absolute bottom-16 left-12 w-1.5 h-1.5 bg-pink-400 rounded-full animate-pulse delay-1000"></div>
          </div>
        )}
      </div>

      {/* 底部阴影 */}
      <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 w-3/4 h-4 bg-gradient-to-r from-transparent via-slate-300/30 to-transparent blur-lg"></div>
    </div>
  );
};

export default ImageDisplay;