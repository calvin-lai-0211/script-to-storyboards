import React from "react";
import { useSearchParams, useParams, Navigate } from "react-router-dom";
import { FileText, Film, Brain, Settings } from "lucide-react";
import BackButton from "../components/BackButton";
import ScriptTab from "../components/tabs/ScriptTab";
import StoryboardTab from "../components/tabs/StoryboardTab";
import MemoryTab from "../components/tabs/MemoryTab";
import WorkflowTab from "../components/tabs/WorkflowTab";
import { useEpisodeStore } from "@store/useEpisodeStore";
import { API_ENDPOINTS, apiCall } from "@api";

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

const Workspace: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { key: paramKey } = useParams<{ key: string }>();
  // Support both URL params and route params
  const key = paramKey || searchParams.get("key") || "";
  const tabFromUrl = searchParams.get("tab") || "script";
  const [activeTab, setActiveTab] = React.useState(tabFromUrl);
  const { currentEpisode, setCurrentEpisode, getEpisode, setEpisode } = useEpisodeStore();

  // Sync activeTab with URL
  React.useEffect(() => {
    const urlTab = searchParams.get("tab") || "script";
    if (urlTab !== activeTab) {
      setActiveTab(urlTab);
    }
  }, [searchParams]);

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
      return;
    }

    // If no cache, fetch episode data from API
    // This ensures the title is loaded even when accessing non-script tabs directly
    const fetchEpisodeInfo = async () => {
      try {
        console.debug("Workspace: Fetching episode info for key:", key);
        const data = await apiCall<ScriptData>(API_ENDPOINTS.getScript(key));

        // Save to store
        setEpisode(key, data);

        // Set as current episode
        setCurrentEpisode({
          key: data.key,
          title: data.title,
          episode_num: data.episode_num,
        });
      } catch (err) {
        console.error("Workspace: Error fetching episode info:", err);
        // Set error state in currentEpisode
        setCurrentEpisode({
          key: key,
          title: "加载失败",
          episode_num: 0,
        });
      }
    };

    fetchEpisodeInfo();
  }, [key, currentEpisode, getEpisode, setCurrentEpisode, setEpisode]);

  // 如果缺少必要参数，重定向到首页
  if (!key) {
    return <Navigate to="/" replace />;
  }

  const tabs = [
    { id: "script", label: "原文", icon: FileText },
    { id: "storyboard", label: "分镜", icon: Film },
    { id: "memory", label: "Memory", icon: Brain },
    { id: "workflow", label: "流程控制 (fake)", icon: Settings },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case "script":
        return <ScriptTab scriptKey={key} />;
      case "storyboard":
        return <StoryboardTab scriptKey={key} />;
      case "memory":
        return <MemoryTab scriptKey={key} />;
      case "workflow":
        return <WorkflowTab scriptKey={key} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 顶部标题栏 */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          <BackButton to="/" label="返回剧集列表" />
          <h1 className="text-2xl font-bold text-slate-800">
            {currentEpisode
              ? `${currentEpisode.title} - 第${currentEpisode.episode_num}集`
              : "加载中..."}
          </h1>
        </div>
      </div>

      {/* Tab 导航 */}
      <div className="bg-white border-b border-slate-200 px-6">
        <div className="flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setSearchParams({ tab: tab.id });
                }}
                className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-slate-600 hover:text-slate-800"
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
      <div className="flex-1 overflow-hidden">{renderTabContent()}</div>
    </div>
  );
};

export default Workspace;
