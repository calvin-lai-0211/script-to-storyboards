import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { User, Sparkles, AlertCircle, Save, Edit } from 'lucide-react';
import ImageDisplay from '../components/ImageDisplay';
import { API_ENDPOINTS, apiCall } from '../config/api';

interface CharacterData {
  character_name: string;
  image_prompt: string;
  reflection: string;
  image_url: string;
}

const CharacterViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [characterData, setCharacterData] = useState<CharacterData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditingPrompt, setIsEditingPrompt] = useState<boolean>(false);
  const [editedPrompt, setEditedPrompt] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    if (id) {
      fetchCharacterData(id);
    }
  }, [id]);

  const fetchCharacterData = async (characterId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(API_ENDPOINTS.getCharacter(characterId));
      setCharacterData(data);
      setEditedPrompt(data.image_prompt);
    } catch (err) {
      console.error('Error fetching character data:', err);
      setError('获取角色数据失败，请检查网络或服务器。');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrompt = async () => {
    if (!characterData || !id) return;

    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.updateCharacterPrompt(id), {
        method: 'PUT',
        body: JSON.stringify({ image_prompt: editedPrompt }),
      });

      setCharacterData({ ...characterData, image_prompt: editedPrompt });
      setIsEditingPrompt(false);
    } catch (err) {
      console.error('Error saving prompt:', err);
      alert('保存失败，请重试。');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 简化背景 */}
      <div className="absolute inset-0 bg-gradient-to-t from-white/60 to-transparent"></div>

      {/* 装饰性元素 */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-gradient-to-br from-blue-200/30 to-purple-200/30 rounded-full blur-2xl animate-float"></div>
      <div className="absolute bottom-20 right-20 w-16 h-16 bg-gradient-to-br from-purple-200/30 to-pink-200/30 rounded-full blur-xl animate-float" style={{ animationDelay: '3s' }}></div>

      <div className="relative flex flex-col items-center justify-start py-8 px-6">
        {/* 页面标题区域 */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <User className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="w-4 h-4 text-yellow-500" />
              </div>
            </div>
            <p className="text-lg text-slate-600 leading-relaxed">
              {characterData ? characterData.character_name : '加载中...'}
            </p>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="w-full max-w-6xl">
          {error && (
            <div className="mb-6 p-4 bg-red-50/95 backdrop-blur-sm border border-red-200 rounded-xl shadow-md">
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
            {/* 左侧: 肖像显示区域 (1列) */}
            <div className="lg:col-span-1">
              <ImageDisplay
                imageUrl={characterData?.image_url || null}
                loading={loading}
              />
            </div>

            {/* 右侧: 信息区域 (2列) */}
            <div className="lg:col-span-2 space-y-6">
              {/* 创意描述区域 - 可编辑的 Prompt */}
              <div className="bg-white/95 backdrop-blur-sm border-2 border-slate-300 rounded-2xl shadow-lg transition-all duration-300 hover:shadow-xl hover:border-slate-400 p-6 flex flex-col h-[400px]">
                <div className="flex items-center justify-between mb-3 flex-shrink-0 h-8">
                  <h3 className="font-display font-bold text-slate-800 text-lg flex items-center">
                    <Sparkles className="w-5 h-5 text-purple-500 mr-2" />
                    角色描述
                  </h3>
                  {!isEditingPrompt ? (
                    <button
                      onClick={() => setIsEditingPrompt(true)}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors duration-200"
                    >
                      <Edit className="w-4 h-4" />
                      <span className="text-sm font-medium">编辑</span>
                    </button>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setIsEditingPrompt(false);
                          setEditedPrompt(characterData?.image_prompt || '');
                        }}
                        className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors duration-200 text-sm font-medium"
                      >
                        取消
                      </button>
                      <button
                        onClick={handleSavePrompt}
                        disabled={saving}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Save className="w-4 h-4" />
                        <span className="text-sm font-medium">{saving ? '保存中...' : '保存'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {loading ? (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="animate-pulse text-slate-400">加载中...</div>
                  </div>
                ) : isEditingPrompt ? (
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="flex-1 w-full p-4 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 placeholder-slate-500 resize-none focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200 transition-all duration-200"
                    placeholder="描述角色的外观、服装、表情等细节..."
                  />
                ) : (
                  <div className="flex-1 overflow-y-auto prose max-w-none">
                    <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {characterData?.image_prompt || '暂无描述'}
                    </p>
                  </div>
                )}
              </div>

              {/* 创作提示区域 - 只读的 Reflection */}
              <div className="bg-white/95 backdrop-blur-sm border-2 border-slate-300 rounded-2xl shadow-lg transition-all duration-300 hover:shadow-xl hover:border-slate-400 p-6 flex flex-col h-[276px]">
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
                      {characterData?.reflection || '暂无创作提示'}
                    </p>
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

export default CharacterViewer;