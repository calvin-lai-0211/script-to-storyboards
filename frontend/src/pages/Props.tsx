import React, { useState, useEffect } from "react";
import { Package, Loader2, AlertCircle, Star, RefreshCw } from "lucide-react";
import { API_ENDPOINTS, apiCall } from "@api";
import { usePropStore } from "@store/usePropStore";

interface Prop {
  id: number;
  drama_name: string;
  episode_number: number;
  prop_name: string;
  image_url: string | null;
  image_prompt: string;
  reflection: string | null;
  version: string;
  shots_appeared: string[] | null;
  is_key_prop: boolean | null;
  prop_brief: string | null;
  created_at: string;
}

const Props: React.FC = () => {
  const { allProps, setAllProps } = usePropStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use cached data if available
  const propList = allProps || [];

  useEffect(() => {
    // If already in store, skip fetch
    if (allProps) {
      console.debug("Props: Using cached data");
      return;
    }

    const abortController = new AbortController();
    fetchProps(abortController.signal);

    return () => {
      abortController.abort();
    };
  }, [allProps]);

  const fetchProps = async (signal?: AbortSignal) => {
    try {
      setLoading(true);
      setError(null);

      if (signal?.aborted) return;

      console.debug("Props: Fetching from API");
      const data = await apiCall<{ props: Prop[]; count: number }>(
        API_ENDPOINTS.getAllProps(),
        { signal },
      );

      if (signal?.aborted) return;

      setAllProps(data.props);
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        console.debug("Props fetch cancelled");
        return;
      }
      console.error("Error fetching props:", err);
      setError("获取道具数据失败");
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  const handleRefresh = () => {
    fetchProps();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载道具数据中...</p>
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
            onClick={() => fetchProps()}
            className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  // Sort by id ascending
  const sortedProps = [...propList].sort((a, b) => a.id - b.id);

  return (
    <div className="h-full overflow-auto bg-slate-50">
      <div className="max-w-7xl mx-auto p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2 flex items-center">
              <Package className="w-8 h-8 mr-3 text-purple-500" />
              道具
            </h1>
            <p className="text-slate-600">共 {propList.length} 个道具</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 道具列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sortedProps.map((prop) => (
            <div
              key={prop.id}
              className="bg-white rounded-xl border border-slate-200 hover:border-purple-400 hover:shadow-xl transition-all duration-300 overflow-hidden"
            >
              {prop.image_url ? (
                <img
                  src={prop.image_url}
                  alt={prop.prop_name}
                  className="w-full h-48 object-cover hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-48 bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                  <Package className="w-16 h-16 text-slate-400" />
                </div>
              )}
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-slate-800 flex-1">
                    {prop.prop_name}
                  </h3>
                  {prop.is_key_prop && (
                    <span title="关键道具">
                      <Star className="w-4 h-4 text-amber-500 fill-amber-400 flex-shrink-0 ml-2" />
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-600 mb-2">
                  {prop.drama_name} - 第{prop.episode_number}集
                </p>

                {prop.prop_brief && (
                  <p className="text-xs text-slate-500 mb-2 line-clamp-2">
                    {prop.prop_brief}
                  </p>
                )}

                {prop.shots_appeared && prop.shots_appeared.length > 0 && (
                  <div className="text-xs text-slate-500 mb-2">
                    <span className="font-medium">出现镜头: </span>
                    {prop.shots_appeared.length} 个
                  </div>
                )}

                {prop.version && (
                  <div className="text-xs text-slate-400">
                    版本: {prop.version}
                  </div>
                )}

                <p className="text-xs text-slate-500 mt-2">ID: {prop.id}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {sortedProps.length === 0 && (
          <div className="text-center py-16">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">暂无道具数据</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Props;
