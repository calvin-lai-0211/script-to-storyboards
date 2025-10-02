import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Loader2, AlertCircle, RefreshCw, Search, X } from 'lucide-react';
import { API_ENDPOINTS, apiCall } from '@api';
import { useSceneStore } from '@store/useSceneStore';

interface Scene {
  id: number;
  drama_name: string;
  episode_number: number;
  scene_name: string;
  image_url: string | null;
  image_prompt: string;
}

const Scenes: React.FC = () => {
  const navigate = useNavigate();
  const { allScenes, setAllScenes, setCurrentScene } = useSceneStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  // Use cached data if available
  const scenes = allScenes || [];

  useEffect(() => {
    // If already in store, skip fetch
    if (allScenes) {
      console.debug('Scenes: Using cached data');
      return;
    }

    fetchScenes();
  }, [allScenes]);

  const fetchScenes = async () => {
    try {
      setLoading(true);
      setError(null);

      console.debug('Scenes: Fetching from API');
      const data = await apiCall<{ scenes: Scene[]; count: number }>(
        API_ENDPOINTS.getAllScenes()
      );

      setAllScenes(data.scenes);
    } catch (err) {
      console.error('Error fetching scenes:', err);
      setError('获取场景数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSceneClick = (scene: Scene) => {
    setCurrentScene(scene);
    navigate(`/scene/${scene.id}`);
  };

  const handleImageClick = (e: React.MouseEvent, imageUrl: string) => {
    e.stopPropagation(); // Prevent card click
    setPreviewImage(imageUrl);
  };

  const handleRefresh = () => {
    fetchScenes();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-green-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载场景数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => fetchScenes()}
            className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  // Sort by id ascending
  const sortedScenes = [...scenes].sort((a, b) => a.id - b.id);

  return (
    <div className="h-full overflow-auto bg-slate-50">
      <div className="max-w-7xl mx-auto p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2 flex items-center">
              <MapPin className="w-8 h-8 mr-3 text-green-500" />
              场景
            </h1>
            <p className="text-slate-600">共 {scenes.length} 个场景</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 场景列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sortedScenes.map((scene) => (
            <div
              key={scene.id}
              onClick={() => handleSceneClick(scene)}
              className="group cursor-pointer bg-white rounded-xl border border-slate-200 hover:border-green-400 hover:shadow-xl transition-all duration-300 overflow-hidden"
            >
              {scene.image_url ? (
                <div
                  className="relative w-full h-48 overflow-hidden"
                  onClick={(e) => handleImageClick(e, scene.image_url!)}
                >
                  <img
                    src={scene.image_url}
                    alt={scene.scene_name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300 flex items-center justify-center">
                    <Search className="w-8 h-8 text-white opacity-0 group-hover:opacity-80 transition-opacity duration-300" />
                  </div>
                </div>
              ) : (
                <div className="w-full h-48 bg-gradient-to-br from-green-100 to-teal-100 flex items-center justify-center">
                  <MapPin className="w-16 h-16 text-slate-400" />
                </div>
              )}
              <div className="p-4">
                <h3 className="font-bold text-slate-800 mb-1">{scene.scene_name}</h3>
                <p className="text-xs text-slate-600 mb-2">{scene.drama_name} - 第{scene.episode_number}集</p>
                <p className="text-xs text-slate-500">ID: {scene.id}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {sortedScenes.length === 0 && (
          <div className="text-center py-16">
            <MapPin className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">暂无场景数据</p>
          </div>
        )}
      </div>

      {/* 图片预览模态框 */}
      {previewImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setPreviewImage(null)}
        >
          <button
            onClick={() => setPreviewImage(null)}
            className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-white" />
          </button>
          <img
            src={previewImage}
            alt="Preview"
            className="max-w-full max-h-full object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
};

export default Scenes;
