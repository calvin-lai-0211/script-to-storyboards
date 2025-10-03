import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Package,
  Sparkles,
  AlertCircle,
  Star,
  Edit,
  Save,
  Wand2,
} from "lucide-react";
import ImageDisplay from "../components/ImageDisplay";
import BackButton from "../components/BackButton";
import { API_ENDPOINTS, apiCall } from "@api";
import { usePropStore } from "@store/usePropStore";

interface PropData {
  id: number;
  drama_name: string;
  episode_number: number;
  prop_name: string;
  image_prompt: string;
  reflection: string;
  version: string;
  image_url: string;
  shots_appeared: string[] | null;
  is_key_prop: boolean | null;
  prop_brief: string | null;
  created_at: string | null;
}

const PropViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentProp, updateProp } = usePropStore();
  const [propData, setPropData] = useState<PropData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditingPrompt, setIsEditingPrompt] = useState<boolean>(false);
  const [editedPrompt, setEditedPrompt] = useState<string>("");
  const [saving, setSaving] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);

  useEffect(() => {
    if (id) {
      fetchPropData(id);
    }
  }, [id]);

  const fetchPropData = async (propId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall<any>(API_ENDPOINTS.getProp(propId));
      setPropData(data as PropData);
      setEditedPrompt(data.image_prompt as string);
    } catch (err) {
      console.error("Error fetching prop data:", err);
      setError("获取道具数据失败，请检查网络或服务器。");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrompt = async () => {
    if (!propData || !id) return;

    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.updatePropPrompt(id), {
        method: "PUT",
        body: JSON.stringify({ image_prompt: editedPrompt }),
      });

      setPropData({ ...propData, image_prompt: editedPrompt });
      setIsEditingPrompt(false);
    } catch (err) {
      console.error("Error saving prompt:", err);
      alert("保存失败，请重试。");
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!propData || !id) return;

    // Use editedPrompt if editing, otherwise use current prompt
    const promptToUse = isEditingPrompt
      ? editedPrompt
      : propData.image_prompt;

    if (!promptToUse || promptToUse.trim() === "") {
      alert("请先添加道具描述后再生成图片");
      return;
    }

    setGenerating(true);
    try {
      const result = await apiCall<any>(
        API_ENDPOINTS.generatePropImage(id),
        {
          method: "POST",
          body: JSON.stringify({
            image_prompt: promptToUse,
          }),
        },
      );

      // Update prop data with new image URL and prompt
      const updatedData = {
        ...propData,
        image_url: result.image_url as string,
        image_prompt: promptToUse,
      };
      setPropData(updatedData);
      setEditedPrompt(promptToUse);
      setIsEditingPrompt(false);

      // Update store to refresh list page
      if (id) {
        updateProp(Number(id), {
          image_url: result.image_url as string,
          image_prompt: promptToUse,
        });
      }

      console.debug("Image generated successfully:", result.image_url);
    } catch (err) {
      console.error("Error generating image:", err);
      alert("生成图片失败，请检查网络或稍后重试。");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-pink-50">
      {/* 返回按钮 - 固定在左上角 */}
      <div className="absolute top-6 left-6 z-10">
        <BackButton to="/props" label="返回道具列表" />
      </div>

      <div className="relative flex flex-col items-center justify-start py-8 px-6">
        {/* 页面标题区域 */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="w-4 h-4 text-yellow-500" />
              </div>
            </div>
            <div>
              <p className="text-lg text-slate-800 font-semibold leading-relaxed">
                {currentProp?.prop_name ||
                  propData?.prop_name ||
                  "加载中..."}
              </p>
              {propData?.is_key_prop && (
                <span className="inline-flex items-center space-x-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full mt-1">
                  <Star className="w-3 h-3" />
                  <span>关键道具</span>
                </span>
              )}
            </div>
          </div>
          {currentProp && (
            <p className="text-sm text-slate-500">
              {currentProp.drama_name} - 第{currentProp.episode_number}集
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
            {/* 左侧: 道具图片显示区域 (1列) - 固定位置 */}
            <div className="lg:col-span-1 lg:sticky lg:top-6">
              <ImageDisplay
                imageUrl={propData?.image_url || null}
                loading={loading}
              />
            </div>

            {/* 右侧: 信息区域 (2列) - 可滚动 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 道具信息 */}
              <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-5">
                <h3 className="font-display font-bold text-slate-800 text-lg flex items-center mb-4">
                  <Sparkles className="w-5 h-5 text-purple-500 mr-2" />
                  道具信息
                </h3>

                {/* 道具简介 */}
                {propData?.prop_brief && (
                  <div className="mb-4 pb-4 border-b border-slate-200">
                    <p className="text-slate-700 leading-relaxed whitespace-pre-wrap text-sm">
                      {propData.prop_brief}
                    </p>
                  </div>
                )}

                {/* 元信息网格 */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {propData?.version && (
                    <div>
                      <p className="text-xs text-slate-500 mb-1">版本</p>
                      <p className="text-slate-700 font-medium">
                        {propData.version}
                      </p>
                    </div>
                  )}
                  {propData?.shots_appeared &&
                    propData.shots_appeared.length > 0 && (
                      <div>
                        <p className="text-xs text-slate-500 mb-1">
                          出现镜头数
                        </p>
                        <p className="text-slate-700 font-medium">
                          {propData.shots_appeared.length} 个
                        </p>
                      </div>
                    )}
                  {propData?.created_at && (
                    <div className="col-span-2">
                      <p className="text-xs text-slate-500 mb-1">创建时间</p>
                      <p className="text-slate-700 font-medium">
                        {new Date(propData.created_at).toLocaleString("zh-CN")}
                      </p>
                    </div>
                  )}
                </div>

                {/* 镜头列表 */}
                {propData?.shots_appeared &&
                  propData.shots_appeared.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <p className="text-xs text-slate-500 mb-2">
                        出现镜头列表
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {propData.shots_appeared.map((shot, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 bg-purple-50 text-purple-700 text-xs rounded-full border border-purple-200"
                          >
                            {shot}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </div>

              {/* 道具描述 - Image Prompt - 可编辑 */}
              <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-6 flex flex-col h-[350px]">
                <div className="flex items-center justify-between mb-3 flex-shrink-0 h-8">
                  <h3 className="font-display font-bold text-slate-800 text-lg flex items-center">
                    <Sparkles className="w-5 h-5 text-pink-500 mr-2" />
                    道具描述
                  </h3>
                  {!isEditingPrompt ? (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handleGenerateImage}
                        disabled={generating}
                        className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
                      >
                        <Wand2 className="w-4 h-4" />
                        <span className="text-sm font-medium">
                          {generating ? "生成中..." : "生成图片"}
                        </span>
                      </button>
                      <button
                        onClick={() => setIsEditingPrompt(true)}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors duration-200"
                      >
                        <Edit className="w-4 h-4" />
                        <span className="text-sm font-medium">编辑</span>
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setIsEditingPrompt(false);
                          setEditedPrompt(propData?.image_prompt || "");
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
                        <span className="text-sm font-medium">
                          {saving ? "保存中..." : "保存"}
                        </span>
                      </button>
                    </div>
                  )}
                </div>

                {loading ? (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="animate-pulse text-slate-400">
                      加载中...
                    </div>
                  </div>
                ) : isEditingPrompt ? (
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="flex-1 w-full p-4 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 placeholder-slate-500 resize-none focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200 transition-colors duration-200"
                    placeholder="描述道具的外观、材质、颜色等细节..."
                  />
                ) : (
                  <div className="flex-1 overflow-y-auto prose max-w-none">
                    <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {propData?.image_prompt || "暂无描述"}
                    </p>
                  </div>
                )}
              </div>

              {/* 创作提示 - Reflection */}
              {propData?.reflection && (
                <div className="bg-white border-2 border-slate-300 rounded-2xl shadow-lg transition-shadow duration-300 hover:shadow-xl p-6 flex flex-col h-[276px]">
                  <div className="flex items-center mb-3 flex-shrink-0 h-8">
                    <h3 className="font-display font-bold text-slate-800 text-lg flex items-center">
                      <Sparkles className="w-5 h-5 text-yellow-500 mr-2" />
                      Reflection
                    </h3>
                  </div>
                  {loading ? (
                    <div className="flex-1 flex items-center justify-center">
                      <div className="animate-pulse text-slate-400">
                        加载中...
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto prose max-w-none">
                      <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {propData.reflection}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropViewer;
