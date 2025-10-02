import React, { useState, useEffect } from 'react';
import { Loader2, Brain, Calendar, Sparkles } from 'lucide-react';
import { API_ENDPOINTS, apiCall } from '@api';

interface MemoryTabProps {
  scriptKey: string;
}

interface EpisodeMemory {
  id: number;
  script_name: string;
  episode_number: number;
  plot_summary: string;
  options: Record<string, unknown>;
  created_at: string;
}

const MemoryTab: React.FC<MemoryTabProps> = ({ scriptKey }) => {
  const [memory, setMemory] = useState<EpisodeMemory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const abortController = new AbortController();
    fetchMemory(abortController.signal);

    return () => {
      abortController.abort();
    };
  }, [scriptKey]);

  const fetchMemory = async (signal?: AbortSignal) => {
    try {
      setLoading(true);
      setError(null);

      if (signal?.aborted) return;

      const data = await apiCall<EpisodeMemory>(
        API_ENDPOINTS.getEpisodeMemory(scriptKey)
      );

      if (signal?.aborted) return;

      setMemory(data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'name' in err && err.name === 'AbortError') {
        console.debug('Memory fetch cancelled');
        return;
      }
      console.error('Error fetching memory:', err);
      // 友好提示，区分不同错误
      if (err && typeof err === 'object' && 'message' in err &&
          typeof err.message === 'string' && err.message.includes('暂无')) {
        setError(err.message);
      } else {
        setError('获取剧集摘要失败');
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">加载剧集摘要中...</p>
        </div>
      </div>
    );
  }

  if (error || !memory) {
    const isNotFound = error && error.includes('暂无');
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Brain className={`w-16 h-16 mx-auto mb-4 ${isNotFound ? 'text-slate-300' : 'text-red-400'}`} />
          <p className={`text-lg font-medium mb-2 ${isNotFound ? 'text-slate-700' : 'text-red-600'}`}>
            {error || '暂无剧集摘要'}
          </p>
          <p className="text-sm text-slate-500">
            {isNotFound
              ? '此剧集尚未生成摘要，请前往「流程控制」Tab 执行生成步骤'
              : '加载失败，请稍后重试'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* 头部卡片 */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl p-8 mb-6 text-white shadow-xl">
          <div className="flex items-center space-x-3 mb-4">
            <Brain className="w-8 h-8" />
            <h1 className="text-3xl font-bold">剧集记忆</h1>
          </div>
          <div className="flex items-center space-x-4 text-purple-100">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4" />
              <span>{memory.script_name}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4" />
              <span>第 {memory.episode_number} 集</span>
            </div>
          </div>
        </div>

        {/* 剧情摘要 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-slate-200 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <span>剧情摘要</span>
            </h2>
          </div>

          <div className="p-6">
            <div className="prose max-w-none">
              <p className="text-slate-700 leading-relaxed whitespace-pre-wrap text-lg">
                {memory.plot_summary}
              </p>
            </div>
          </div>
        </div>

        {/* 元数据 */}
        {memory.options && Object.keys(memory.options).length > 0 && (
          <div className="mt-6 bg-white rounded-2xl shadow-lg border-2 border-slate-200 overflow-hidden">
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-4 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-800">额外信息</h2>
            </div>

            <div className="p-6">
              <pre className="bg-slate-50 rounded-lg p-4 text-sm text-slate-700 overflow-auto">
                {JSON.stringify(memory.options, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* 生成时间 */}
        <div className="mt-4 text-center text-sm text-slate-500">
          生成时间: {new Date(memory.created_at).toLocaleString('zh-CN')}
        </div>
      </div>
    </div>
  );
};

export default MemoryTab;
