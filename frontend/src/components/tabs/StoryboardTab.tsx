import React, { useState, useEffect } from "react";
import {
  Loader2,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Film,
  Camera,
  Image as ImageIcon,
  RefreshCw,
  ChevronsDown,
  ChevronsRight,
} from "lucide-react";
import { API_ENDPOINTS, apiCall } from "@api";
import { useStoryboardStore, Scene } from "@store/useStoryboardStore";

interface StoryboardTabProps {
  scriptKey: string;
}

const StoryboardTab: React.FC<StoryboardTabProps> = ({ scriptKey }) => {
  const { getStoryboard, setStoryboard } = useStoryboardStore();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedScenes, setExpandedScenes] = useState<Set<string>>(new Set());
  const [expandedShots, setExpandedShots] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Check store cache first
    const cachedStoryboard = getStoryboard(scriptKey);
    if (cachedStoryboard) {
      console.debug("StoryboardTab: Using cached storyboard");
      setScenes(cachedStoryboard);
      return;
    }

    // Only fetch if no cache
    const abortController = new AbortController();
    fetchStoryboards(abortController.signal);

    return () => {
      abortController.abort();
    };
  }, [scriptKey, getStoryboard]);

  const fetchStoryboards = async (signal?: AbortSignal) => {
    try {
      setLoading(true);
      setError(null);

      if (signal?.aborted) return;

      const data = await apiCall<{ storyboards: Record<string, unknown>[] }>(
        API_ENDPOINTS.getStoryboards(scriptKey),
      );

      if (signal?.aborted) return;

      // 将扁平数据转换为层级结构
      const scenesMap = new Map<string, Scene>();

      data.storyboards.forEach((item: any) => {
        const sceneKey = item.scene_number as string;

        if (!scenesMap.has(sceneKey)) {
          scenesMap.set(sceneKey, {
            scene_number: item.scene_number as string,
            scene_description: item.scene_description as string,
            shots: [],
          });
        }

        const scene = scenesMap.get(sceneKey)!;
        let shot = scene.shots.find((s) => s.shot_number === item.shot_number);

        if (!shot) {
          shot = {
            shot_number: item.shot_number as string,
            shot_description: item.shot_description as string,
            subShots: [],
          };
          scene.shots.push(shot);
        }

        shot.subShots.push({
          id: item.id as number,
          sub_shot_number: item.sub_shot_number as string,
          camera_angle: item.camera_angle as string,
          characters: (item.characters as string[]) || [],
          scene_context: (item.scene_context as string[]) || [],
          key_props: (item.key_props as string[]) || [],
          image_prompt: item.image_prompt as string,
          dialogue_sound: item.dialogue_sound as string,
          duration_seconds: item.duration_seconds as number,
          notes: item.notes as string,
        });
      });

      // 对数据进行排序
      const scenesData = Array.from(scenesMap.values());

      // 对每个场景的镜头排序
      scenesData.forEach(scene => {
        scene.shots.sort((a, b) => {
          const numA = parseFloat(a.shot_number) || 0;
          const numB = parseFloat(b.shot_number) || 0;
          return numA - numB;
        });

        // 对每个镜头的子镜头排序
        scene.shots.forEach(shot => {
          shot.subShots.sort((a, b) => {
            const numA = parseFloat(a.sub_shot_number) || 0;
            const numB = parseFloat(b.sub_shot_number) || 0;
            return numA - numB;
          });
        });
      });

      setScenes(scenesData);
      setStoryboard(scriptKey, scenesData);
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        console.debug("Storyboards fetch cancelled");
        return;
      }
      console.error("Error fetching storyboards:", err);
      setError("获取分镜数据失败");
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  const toggleScene = (sceneNumber: string) => {
    const newExpanded = new Set(expandedScenes);
    if (newExpanded.has(sceneNumber)) {
      newExpanded.delete(sceneNumber);
    } else {
      newExpanded.add(sceneNumber);
    }
    setExpandedScenes(newExpanded);
  };

  const toggleShot = (shotKey: string) => {
    const newExpanded = new Set(expandedShots);
    if (newExpanded.has(shotKey)) {
      newExpanded.delete(shotKey);
    } else {
      newExpanded.add(shotKey);
    }
    setExpandedShots(newExpanded);
  };

  const handleRefresh = () => {
    console.debug("StoryboardTab: Manually refreshing storyboards");
    const abortController = new AbortController();
    fetchStoryboards(abortController.signal);
  };

  const toggleAllScenes = () => {
    if (expandedScenes.size === scenes.length) {
      // 全部展开 -> 全部折叠
      setExpandedScenes(new Set());
    } else {
      // 部分展开或全部折叠 -> 全部展开
      setExpandedScenes(new Set(scenes.map(s => s.scene_number)));
    }
  };

  const toggleAllShotsInScene = (sceneNumber: string) => {
    const scene = scenes.find(s => s.scene_number === sceneNumber);
    if (!scene) return;

    const shotKeys = scene.shots.map(shot => `${sceneNumber}-${shot.shot_number}`);
    const allExpanded = shotKeys.every(key => expandedShots.has(key));

    const newExpanded = new Set(expandedShots);
    if (allExpanded) {
      // 全部展开 -> 全部折叠
      shotKeys.forEach(key => newExpanded.delete(key));
    } else {
      // 部分展开或全部折叠 -> 全部展开
      shotKeys.forEach(key => newExpanded.add(key));
    }
    setExpandedShots(newExpanded);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载分镜数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (scenes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Film className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">暂无分镜数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 工具栏 */}
      <div className="bg-white border-b border-slate-200 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Film className="w-5 h-5 text-blue-500" />
            <span className="font-medium text-slate-800">分镜脚本</span>
            <span className="text-sm text-slate-500">
              共 {scenes.length} 个场景
            </span>
          </div>
          <button
            onClick={toggleAllScenes}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            title={expandedScenes.size === scenes.length ? "折叠所有场景" : "展开所有场景"}
          >
            {expandedScenes.size === scenes.length ? (
              <ChevronsRight className="w-4 h-4" />
            ) : (
              <ChevronsDown className="w-4 h-4" />
            )}
            <span>{expandedScenes.size === scenes.length ? "全部折叠" : "全部展开"}</span>
          </button>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="刷新分镜"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span>刷新</span>
        </button>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-4">
          {scenes.map((scene) => {
            const sceneExpanded = expandedScenes.has(scene.scene_number);

            return (
              <div
                key={scene.scene_number}
                className="bg-white rounded-xl shadow-sm border-2 border-slate-200 overflow-hidden"
              >
                {/* 场景标题 */}
                <button
                  onClick={() => toggleScene(scene.scene_number)}
                  className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {sceneExpanded ? (
                      <ChevronDown className="w-5 h-5 text-blue-600" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-blue-600" />
                    )}
                    <Film className="w-5 h-5 text-blue-600" />
                    <div className="text-left">
                      <div className="font-bold text-slate-800">
                        场景 {scene.scene_number}
                      </div>
                      <div className="text-sm text-slate-600">
                        {scene.scene_description}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-slate-500">
                    {scene.shots.length} 个镜头
                  </div>
                </button>

                {/* 镜头列表 */}
                {sceneExpanded && (
                  <div className="border-t border-slate-200">
                    {/* 镜头全展开/折叠按钮 */}
                    <div className="px-6 py-2 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                      <span className="text-sm text-slate-600">
                        {scene.shots.length} 个镜头
                      </span>
                      <button
                        onClick={() => toggleAllShotsInScene(scene.scene_number)}
                        className="flex items-center space-x-1 px-2 py-1 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded transition-colors"
                        title={scene.shots.every(shot => expandedShots.has(`${scene.scene_number}-${shot.shot_number}`)) ? "折叠所有镜头" : "展开所有镜头"}
                      >
                        {scene.shots.every(shot => expandedShots.has(`${scene.scene_number}-${shot.shot_number}`)) ? (
                          <ChevronsRight className="w-3 h-3" />
                        ) : (
                          <ChevronsDown className="w-3 h-3" />
                        )}
                        <span>{scene.shots.every(shot => expandedShots.has(`${scene.scene_number}-${shot.shot_number}`)) ? "全部折叠" : "全部展开"}</span>
                      </button>
                    </div>
                    {scene.shots.map((shot) => {
                      const shotKey = `${scene.scene_number}-${shot.shot_number}`;
                      const shotExpanded = expandedShots.has(shotKey);

                      return (
                        <div
                          key={shotKey}
                          className="border-b border-slate-100 last:border-0"
                        >
                          {/* 镜头标题 */}
                          <button
                            onClick={() => toggleShot(shotKey)}
                            className="w-full px-8 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors"
                          >
                            <div className="flex items-center space-x-3">
                              {shotExpanded ? (
                                <ChevronDown className="w-4 h-4 text-purple-600" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-purple-600" />
                              )}
                              <Camera className="w-4 h-4 text-purple-600" />
                              <div className="text-left">
                                <div className="font-medium text-slate-800">
                                  镜头 {shot.shot_number}
                                </div>
                                <div className="text-sm text-slate-600">
                                  {shot.shot_description}
                                </div>
                              </div>
                            </div>
                            <div className="text-sm text-slate-500">
                              {shot.subShots.length} 个子镜头
                            </div>
                          </button>

                          {/* 子镜头列表 */}
                          {shotExpanded && (
                            <div className="bg-slate-50 px-12 py-4 space-y-3">
                              {shot.subShots.map((subShot) => (
                                <div
                                  key={subShot.id}
                                  className="bg-white rounded-lg border border-slate-200 p-4"
                                >
                                  <div className="flex items-start space-x-3 mb-3">
                                    <ImageIcon className="w-4 h-4 text-pink-600 mt-1" />
                                    <div className="flex-1">
                                      <div className="font-medium text-slate-800 mb-1">
                                        子镜头 {subShot.sub_shot_number}
                                      </div>
                                      <div className="text-sm text-slate-600 mb-2">
                                        {subShot.camera_angle}
                                      </div>

                                      <div className="grid grid-cols-2 gap-3 text-sm">
                                        {subShot.characters.length > 0 && (
                                          <div>
                                            <span className="text-slate-500">
                                              角色:
                                            </span>{" "}
                                            <span className="text-slate-700">
                                              {subShot.characters.join(", ")}
                                            </span>
                                          </div>
                                        )}
                                        {subShot.scene_context.length > 0 && (
                                          <div>
                                            <span className="text-slate-500">
                                              场景:
                                            </span>{" "}
                                            <span className="text-slate-700">
                                              {subShot.scene_context.join(", ")}
                                            </span>
                                          </div>
                                        )}
                                        {subShot.key_props.length > 0 && (
                                          <div className="col-span-2">
                                            <span className="text-slate-500">
                                              道具:
                                            </span>{" "}
                                            <span className="text-slate-700">
                                              {subShot.key_props.join(", ")}
                                            </span>
                                          </div>
                                        )}
                                        {subShot.duration_seconds && (
                                          <div>
                                            <span className="text-slate-500">
                                              时长:
                                            </span>{" "}
                                            <span className="text-slate-700">
                                              {subShot.duration_seconds}秒
                                            </span>
                                          </div>
                                        )}
                                      </div>

                                      {subShot.image_prompt && (
                                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                                          <div className="text-xs text-slate-500 mb-1">
                                            画面提示词
                                          </div>
                                          <div className="text-sm text-slate-700">
                                            {subShot.image_prompt}
                                          </div>
                                        </div>
                                      )}

                                      {subShot.dialogue_sound && (
                                        <div className="mt-2 p-3 bg-purple-50 rounded-lg">
                                          <div className="text-xs text-slate-500 mb-1">
                                            对白/音效
                                          </div>
                                          <div className="text-sm text-slate-700">
                                            {subShot.dialogue_sound}
                                          </div>
                                        </div>
                                      )}

                                      {subShot.notes && (
                                        <div className="mt-2 p-3 bg-amber-50 rounded-lg">
                                          <div className="text-xs text-slate-500 mb-1">
                                            备注
                                          </div>
                                          <div className="text-sm text-slate-700">
                                            {subShot.notes}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default StoryboardTab;
