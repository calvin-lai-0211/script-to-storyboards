import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, Calendar, User, Star, Loader2, AlertCircle, Key, Copy, Check, RefreshCw } from 'lucide-react';
import { API_ENDPOINTS, apiCall } from '@api';
import { useEpisodeStore } from '@store/useEpisodeStore';
import { ScriptData } from '@store/types';

const ScriptsList: React.FC = () => {
  const navigate = useNavigate();
  const { allEpisodes, setAllEpisodes, setCurrentEpisode } = useEpisodeStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Use cached data if available
  const episodes = allEpisodes || [];

  useEffect(() => {
    // If already in store, skip fetch
    if (allEpisodes) {
      console.debug('EpisodesList: Using cached data');
      return;
    }

    fetchEpisodes();
  }, [allEpisodes]);

  const fetchEpisodes = async () => {
    try {
      setLoading(true);
      setError(null);

      console.debug('EpisodesList: Fetching from API');
      const data = await apiCall<{ scripts: ScriptData[]; count: number }>(
        API_ENDPOINTS.getAllScripts()
      );

      setAllEpisodes(data.scripts);
    } catch (err) {
      console.error('Error fetching episodes:', err);
      setError('获取剧集列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (episode: ScriptData) => {
    // Set current episode in store first
    setCurrentEpisode({
      key: episode.key,
      title: episode.title,
      episode_num: episode.episode_num,
    });
    // Navigate to episode detail page
    navigate(`/episode/${encodeURIComponent(episode.key)}`);
  };

  const handleCopyKey = (e: React.MouseEvent, key: string) => {
    e.stopPropagation(); // 阻止触发卡片点击
    navigator.clipboard.writeText(key).then(() => {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000); // 2秒后恢复
    });
  };

  const handleRefresh = () => {
    fetchEpisodes();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载剧集列表中...</p>
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
          <button
            onClick={() => fetchEpisodes()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-7xl mx-auto p-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">剧集列表</h1>
            <p className="text-slate-600">共 {episodes.length} 个剧集</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
        </div>

        {/* 卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {episodes.map((episode) => (
            <div
              key={`${episode.title}-${episode.episode_num}`}
              onClick={() => handleCardClick(episode)}
              className="group cursor-pointer bg-white rounded-2xl border-2 border-slate-200 hover:border-blue-400 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 overflow-hidden"
              title={episode.title}
            >
              {/* 卡片头部 - 渐变背景 */}
              <div className="h-28 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 relative overflow-hidden">
                <div className="absolute inset-0 bg-black/10 group-hover:bg-black/0 transition-colors duration-300"></div>
                <div className="absolute bottom-3 left-4 right-4">
                  <h3
                    className="text-white font-bold text-base truncate drop-shadow-lg leading-tight mb-1"
                    title={episode.title}
                  >
                    {episode.title}
                  </h3>
                  <p className="text-white/90 text-sm drop-shadow">第 {episode.episode_num} 集</p>
                </div>
                <div className="absolute top-3 right-3">
                  <Film className="w-5 h-5 text-white/80" />
                </div>
              </div>

              {/* 卡片内容 */}
              <div className="p-3 space-y-2">
                {/* Key with copy button */}
                <div className="flex items-center space-x-2 text-xs text-slate-500 group/key">
                  <Key className="w-3 h-3 flex-shrink-0" />
                  <span className="font-mono truncate flex-1" title={episode.key}>{episode.key}</span>
                  <button
                    onClick={(e) => handleCopyKey(e, episode.key)}
                    className="cursor-pointer p-1 hover:bg-slate-100 rounded"
                    title="复制 Key"
                  >
                    {copiedKey === episode.key ? (
                      <Check className="w-3 h-3 text-green-600" />
                    ) : (
                      <Copy className="w-3 h-3 text-slate-400 hover:text-slate-600" />
                    )}
                  </button>
                </div>

                {/* 作者 */}
                {episode.author && (
                  <div className="flex items-center space-x-2 text-sm text-slate-600">
                    <User className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{episode.author}</span>
                  </div>
                )}

                {/* 年份和评分 */}
                <div className="flex items-center justify-between text-sm">
                  {episode.creation_year && (
                    <div className="flex items-center space-x-2 text-slate-600">
                      <Calendar className="w-4 h-4" />
                      <span>{episode.creation_year}</span>
                    </div>
                  )}

                  {episode.score !== null && (
                    <div className="flex items-center space-x-1 text-amber-600">
                      <Star className="w-4 h-4 fill-amber-400" />
                      <span className="font-medium">{episode.score.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {episodes.length === 0 && (
          <div className="text-center py-16">
            <Film className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">暂无剧集</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScriptsList;
