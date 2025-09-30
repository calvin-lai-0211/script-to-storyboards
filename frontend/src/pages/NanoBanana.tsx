import React, { useState } from 'react';
import { Wand2, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import ImageDisplay from '../components/ImageDisplay';
import PromptInput from '../components/PromptInput';

const NanoBanana: React.FC = () => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendPrompt = async (prompt: string, referenceImageUrl?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8899/api/gem-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt, referenceImageUrl }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.code === 0 && data.data) {
        setImageUrl(data.data);
      } else {
        setError(data.message || '获取图片失败');
      }
    } catch (err) {
      console.error('Error fetching image:', err);
      setError('请求图片失败，请检查网络或服务器。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 简化背景 */}
      <div className="absolute inset-0 bg-gradient-to-t from-white/60 to-transparent"></div>

      {/* 减少装饰性元素 */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-gradient-to-br from-blue-200/30 to-purple-200/30 rounded-full blur-2xl animate-float"></div>
      <div className="absolute bottom-20 right-20 w-16 h-16 bg-gradient-to-br from-purple-200/30 to-pink-200/30 rounded-full blur-xl animate-float" style={{ animationDelay: '3s' }}></div>

      <div className="relative flex flex-col items-center justify-start py-8 px-6">
        {/* 页面标题区域 - 简化和提高对比度 */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Wand2 className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="w-4 h-4 text-yellow-500" />
              </div>
            </div>
          </div>

          <h1 className="text-4xl font-display font-bold text-slate-800 mb-3">
            AI 图像生成器
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            使用人工智能的力量，将你的想象力转化为令人惊叹的视觉作品。只需描述你的想法，让AI为你创造独特的艺术品。
          </p>

          {/* 生成成功状态 */}
          {imageUrl && (
            <div className="flex items-center justify-center mt-6">
              <div className="flex items-center space-x-2 px-4 py-2 bg-green-50/90 backdrop-blur-sm rounded-full shadow-md border border-green-200 animate-slide-up">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-700">图像生成成功</span>
              </div>
            </div>
          )}
        </div>

        {/* 主要内容区域 - 改进布局 */}
        <div className="w-full max-w-5xl">
          <div className="grid lg:grid-cols-3 gap-6 items-start">
            {/* 图像显示区域 */}
            <div className="lg:col-span-2">
              <div className="relative">
                <ImageDisplay imageUrl={imageUrl} loading={loading} />

                {/* 错误提示 - 改进样式 */}
                {error && (
                  <div className="mt-4 p-4 bg-red-50/95 backdrop-blur-sm border border-red-200 rounded-xl shadow-md animate-slide-up">
                    <div className="flex items-center space-x-3">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <div>
                        <p className="text-red-800 font-medium">生成失败</p>
                        <p className="text-red-600 text-sm mt-1">{error}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 输入控制区域 */}
            <div className="lg:col-span-1">
              <div className="sticky top-6">
                <PromptInput onSend={handleSendPrompt} loading={loading} />

                {/* 生成提示 - 统一设计 */}
                <div className="mt-6 p-5 bg-white/95 backdrop-blur-sm border-2 border-slate-300 rounded-2xl shadow-lg transition-all duration-300 hover:shadow-xl hover:border-slate-400">
                  <h3 className="font-display font-bold text-slate-800 mb-4 flex items-center">
                    <Sparkles className="w-5 h-5 text-yellow-500 mr-2" />
                    创作提示
                  </h3>
                  <div className="space-y-3 text-sm text-slate-600">
                    <div className="flex items-start space-x-3">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p>描述具体的场景、物体或风格</p>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p>添加颜色、光线、情感等细节</p>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-1.5 h-1.5 bg-pink-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p>尝试不同的艺术风格和创意</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NanoBanana;