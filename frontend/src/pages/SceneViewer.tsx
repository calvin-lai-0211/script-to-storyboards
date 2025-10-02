import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapPin, Sparkles, AlertCircle, ArrowLeft, Star } from 'lucide-react';
import ImageDisplay from '../components/ImageDisplay';
import { API_ENDPOINTS, apiCall } from '@api';
import { useSceneStore } from '@store/useSceneStore';

interface SceneData {
  id: number;
  drama_name: string;
  episode_number: number;
  scene_name: string;
  image_prompt: string;
  reflection: string;
  version: string;
  image_url: string;
  shots_appeared: string[] | null;
  is_key_scene: boolean | null;
  scene_brief: string | null;
  created_at: string | null;
}

const SceneViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentScene } = useSceneStore();
  const [sceneData, setSceneData] = useState<SceneData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchSceneData(id);
    }
  }, [id]);

  const fetchSceneData = async (sceneId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall<any>(API_ENDPOINTS.getScene(sceneId));
      setSceneData(data as SceneData);
    } catch (err) {
      console.error('Error fetching scene data:', err);
      setError('获取场景数据失败，请检查网络或服务器。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-teal-50">
      {/* 返回按钮 */}
      <button
        onClick={() => navigate('/scenes')}
        className="absolute top-4 left-4 z-10 flex items-center space-x-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg shadow-lg hover:bg-white hover:shadow-xl transition-all duration-200"
      >
        <ArrowLeft className="w-5 h-5 text-slate-700" />
        <span className="text-slate-700 font-medium">返回列表</span>
      </button>

      <div className="relative flex flex-col items-center justify-start py-8 px-6">
        {/* 页面标题区域 */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
                <MapPin className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="w-4 h-4 text-yellow-500" />
              </div>
            </div>
            <div>
              <p className="text-lg text-slate-800 font-semibold leading-relaxed">
                {currentScene?.scene_name || sceneData?.scene_name || '加载中...'}
              </p>
              {sceneData?.is_key_scene && (
                <span className="inline-flex items-center space-x-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full mt-1">
                  <Star className="w-3 h-3" />
                  <span>关键场景</span>
                </span>
              )}
            </div>
          </div>
          {currentScene && (
            <p className="text-sm text-slate-500">
              {currentScene.drama_name} - 第{currentScene.episode_number}集
            </p>
          )}
        </div>

        {/* 主要内容区域 */}
        <div className="w-full max-w-6xl">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl shadow-md">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <div>
                  <p className="text-red-800 font-medium">加载失败</p>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="grid lg:grid-cols-3 gap-6 items-start">
            {/* 左侧: 场景图片显示区域 (1列) */}
            <div className="lg:col-span-1">
              <ImageDisplay
                imageUrl={sceneData?.image_url || null}
                loading={loading}
              />
            </div>

            {/* 右侧: 信息区域 (2列) */}
            <div className="lg:col-span-2 space-y-6">
              {/* 场景简介 */}
              {sceneData?.scene_brief && (
                <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-6">
                  <h3 className="font-display font-bold text-slate-800 text-lg flex items-center mb-3">
                    <Sparkles className="w-5 h-5 text-green-500 mr-2" />
                    场景简介
                  </h3>
                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {sceneData.scene_brief}
                  </p>
                </div>
              )}

              {/* 场景描述 - Image Prompt */}
              <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-6 flex flex-col h-[350px]">
                <div className="flex items-center mb-3 flex-shrink-0 h-8">
                  <h3 className="font-display font-bold text-slate-800 text-lg flex items-center">
                    <Sparkles className="w-5 h-5 text-purple-500 mr-2" />
                    场景描述
                  </h3>
                </div>
                {loading ? (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="animate-pulse text-slate-400">加载中...</div>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto prose max-w-none">
                    <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {sceneData?.image_prompt || '暂无描述'}
                    </p>
                  </div>
                )}
              </div>

              {/* 创作提示 - Reflection */}
              {sceneData?.reflection && (
                <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-6 flex flex-col h-[276px]">
                  <div className="flex items-center mb-3 flex-shrink-0 h-8">
                    <h3 className="font-display font-bold text-slate-800 text-lg flex items-center">
                      <Sparkles className="w-5 h-5 text-yellow-500 mr-2" />
                      Reflection
                    </h3>
                  </div>
                  {loading ? (
                    <div className="flex-1 flex items-center justify-center">
                      <div className="animate-pulse text-slate-400">加载中...</div>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto prose max-w-none">
                      <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {sceneData.reflection}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* 场景元信息 */}
              <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg p-6">
                <h3 className="font-display font-bold text-slate-800 text-lg mb-4">场景信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  {sceneData?.version && (
                    <div>
                      <p className="text-xs text-slate-500 mb-1">版本</p>
                      <p className="text-sm text-slate-700 font-medium">{sceneData.version}</p>
                    </div>
                  )}
                  {sceneData?.shots_appeared && sceneData.shots_appeared.length > 0 && (
                    <div>
                      <p className="text-xs text-slate-500 mb-1">出现镜头数</p>
                      <p className="text-sm text-slate-700 font-medium">{sceneData.shots_appeared.length} 个</p>
                    </div>
                  )}
                  {sceneData?.created_at && (
                    <div className="col-span-2">
                      <p className="text-xs text-slate-500 mb-1">创建时间</p>
                      <p className="text-sm text-slate-700 font-medium">
                        {new Date(sceneData.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  )}
                </div>
                {sceneData?.shots_appeared && sceneData.shots_appeared.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-slate-500 mb-2">出现镜头列表</p>
                    <div className="flex flex-wrap gap-2">
                      {sceneData.shots_appeared.map((shot, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-green-50 text-green-700 text-xs rounded-full border border-green-200"
                        >
                          {shot}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SceneViewer;
