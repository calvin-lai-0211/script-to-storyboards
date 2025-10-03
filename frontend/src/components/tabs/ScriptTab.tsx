import React, { useState, useEffect } from "react";
import { Loader2, AlertCircle, FileText, RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { API_ENDPOINTS, apiCall } from "@api";
import { useEpisodeStore } from "@store/useEpisodeStore";

interface ScriptTabProps {
  scriptKey: string;
}

interface ScriptData {
  key: string;
  title: string;
  episode_num: number;
  content: string;
  roles: string[];
  sceneries: string[];
  author: string | null;
  creation_year: number | null;
}

const ScriptTab: React.FC<ScriptTabProps> = ({ scriptKey }) => {
  const { getEpisode, setEpisode, setCurrentEpisode, currentEpisode } =
    useEpisodeStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get episode from store
  const episode = getEpisode(scriptKey);

  useEffect(() => {
    // If already in store, skip fetch
    if (episode) {
      console.debug("ScriptTab: Using cached episode");
      return;
    }

    // Only fetch if no cache
    fetchEpisode();
  }, [scriptKey, getEpisode]);

  const fetchEpisode = async () => {
    try {
      setLoading(true);
      setError(null);

      console.debug("ScriptTab fetching episode with key:", scriptKey);
      const data = await apiCall<ScriptData>(
        API_ENDPOINTS.getScript(scriptKey),
      );

      setEpisode(scriptKey, data);

      // Also update currentEpisode if not set or different
      if (!currentEpisode || currentEpisode.key !== scriptKey) {
        setCurrentEpisode(data);
      }
    } catch (err) {
      console.error("Error fetching episode:", err);
      setError("获取剧本失败");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    console.debug("ScriptTab: Manually refreshing episode");
    fetchEpisode();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载剧本中...</p>
        </div>
      </div>
    );
  }

  if (error || !episode) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error || "剧本不存在"}</p>
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
            <FileText className="w-5 h-5 text-blue-500" />
            <span className="font-medium text-slate-800">
              {episode.title} - 第 {episode.episode_num} 集
            </span>
          </div>

          {episode.roles && episode.roles.length > 0 && (
            <div className="text-sm text-slate-600">
              角色: {episode.roles.join(", ")}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {episode.author && (
            <div className="text-sm text-slate-600">作者: {episode.author}</div>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="刷新剧本"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span>刷新</span>
          </button>
        </div>
      </div>

      {/* 剧本内容 */}
      <div className="flex-1 overflow-auto bg-slate-50">
        <div className="max-w-5xl mx-auto p-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="prose p-8">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="whitespace-pre-wrap">{children}</p>
                  ),
                }}
              >
                {episode.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScriptTab;
