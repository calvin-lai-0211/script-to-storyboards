import React from 'react';
import { useSearchParams, useParams, Navigate } from 'react-router-dom';
import { FileText, Film, Brain, Settings } from 'lucide-react';
import ScriptTab from '../components/tabs/ScriptTab';
import StoryboardTab from '../components/tabs/StoryboardTab';
import MemoryTab from '../components/tabs/MemoryTab';
import WorkflowTab from '../components/tabs/WorkflowTab';
import { useEpisodeStore } from '@store/useEpisodeStore';

const Workspace: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { key: paramKey } = useParams<{ key: string }>();
  // Support both URL params and route params
  const key = paramKey || searchParams.get('key') || '';
  const [activeTab, setActiveTab] = React.useState('script');
  const { currentEpisode, setCurrentEpisode, getEpisode } = useEpisodeStore();

  // Load episode data: check store first, then fetch if needed
  React.useEffect(() => {
    if (!key) return;

    // If currentEpisode already set with the same key, skip
    if (currentEpisode && currentEpisode.key === key) {
      return;
    }

    // Try to get from cached episode data
    const cachedEpisode = getEpisode(key);
    if (cachedEpisode) {
      setCurrentEpisode({
        key: cachedEpisode.key,
        title: cachedEpisode.title,
        episode_num: cachedEpisode.episode_num,
      });
    }
    // If no cache, currentEpisode might be null
    // ScriptTab will fetch the data when it mounts
  }, [key, currentEpisode, getEpisode, setCurrentEpisode]);

  // 如果缺少必要参数，重定向到首页
  if (!key) {
    return <Navigate to="/" replace />;
  }

  const tabs = [
    { id: 'script', label: '原文', icon: FileText },
    { id: 'storyboard', label: '分镜', icon: Film },
    { id: 'memory', label: 'Memory', icon: Brain },
    { id: 'workflow', label: '流程控制', icon: Settings }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'script':
        return <ScriptTab scriptKey={key} />;
      case 'storyboard':
        return <StoryboardTab scriptKey={key} />;
      case 'memory':
        return <MemoryTab scriptKey={key} />;
      case 'workflow':
        return <WorkflowTab scriptKey={key} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 顶部标题栏 */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-slate-800">
          {currentEpisode ? `${currentEpisode.title} - 第${currentEpisode.episode_num}集` : '加载中...'}
        </h1>
      </div>

      {/* Tab 导航 */}
      <div className="bg-white border-b border-slate-200 px-6">
        <div className="flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-600 hover:text-slate-800'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-hidden">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default Workspace;
