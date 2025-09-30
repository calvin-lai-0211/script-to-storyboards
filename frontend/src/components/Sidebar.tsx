import React from 'react';
import { Image, Layers, ChevronRight, Sparkles } from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  setCurrentPage: (page: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentPage, setCurrentPage }) => {
  const menuItems = [
    {
      id: 'NanoBanana',
      name: 'AI Generator',
      icon: Image,
      description: 'Create images'
    },
    {
      id: 'Gallery',
      name: 'Gallery',
      icon: Layers,
      description: 'View your creations',
      disabled: true
    },
  ];

  return (
    <div className="relative flex flex-col w-64 h-full">
      {/* 艺术感背景 - 更明亮协调 */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-700 via-slate-800 to-slate-900"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-800/30 via-indigo-800/25 to-cyan-900/20"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-purple-600/10 via-indigo-600/8 to-cyan-600/6"></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-purple-500/8 via-transparent to-transparent"></div>

      {/* 艺术感装饰网格 */}
      <div className="absolute inset-0 opacity-20">
        <div className="h-full w-full" style={{
          backgroundImage: `
            linear-gradient(rgba(168,85,247,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px'
        }}></div>
      </div>

      <div className="relative flex flex-col h-full">
        {/* 菜单项 - 改进设计 */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            const isDisabled = item.disabled;

            return (
              <button
                key={item.id}
                onClick={() => !isDisabled && setCurrentPage(item.id)}
                disabled={isDisabled}
                className={`
                  group relative w-full text-left rounded-xl transition-all duration-200 overflow-hidden
                  ${isActive
                    ? 'bg-gradient-to-r from-purple-600/25 via-indigo-600/20 to-cyan-600/15 border border-purple-400/40 shadow-lg shadow-purple-500/10'
                    : isDisabled
                    ? 'bg-white/5 border border-white/5 opacity-50 cursor-not-allowed'
                    : 'bg-white/8 hover:bg-gradient-to-r hover:from-purple-600/15 hover:to-cyan-600/10 border border-white/10 hover:border-purple-400/20'
                  }
                `}
              >
                {/* 活动状态的发光背景 */}
                {isActive && (
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/8 via-indigo-500/6 to-cyan-500/5"></div>
                )}

                <div className="relative p-3 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {/* 图标区域 */}
                    <div className={`
                      p-2 rounded-lg transition-all duration-200
                      ${isActive
                        ? 'bg-gradient-to-br from-purple-500/30 via-indigo-500/25 to-cyan-500/20 shadow-lg scale-105'
                        : 'bg-white/10 group-hover:bg-gradient-to-br group-hover:from-purple-500/20 group-hover:to-cyan-500/15 group-hover:scale-105'
                      }
                    `}>
                      <Icon className={`w-5 h-5 transition-colors duration-200 ${
                        isActive ? 'text-white' : 'text-white/80 group-hover:text-white'
                      }`} />
                    </div>

                    {/* 文本内容 */}
                    <div className="flex-1">
                      <div className={`font-semibold transition-colors duration-200 ${
                        isActive ? 'text-white' : 'text-white/90 group-hover:text-white'
                      }`}>
                        {item.name}
                      </div>
                      <div className="text-sm text-white/60 mt-0.5">
                        {item.description}
                      </div>
                    </div>
                  </div>

                  {/* 右侧箭头指示器 */}
                  <ChevronRight className={`w-4 h-4 transition-all duration-200 ${
                    isActive
                      ? 'text-white opacity-100 translate-x-0'
                      : 'text-white/40 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0'
                  }`} />
                </div>

                {/* 底部装饰线 */}
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500"></div>
                )}
              </button>
            );
          })}
        </nav>

        {/* 底部装饰 - 艺术感设计 */}
        <div className="p-4 border-t border-purple-500/20">
          <div className="flex items-center justify-center space-x-2 text-purple-200/70">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-medium">AI 创作工具</span>
            <Sparkles className="w-4 h-4 text-pink-400" />
          </div>

          {/* 版本信息 */}
          <div className="text-center mt-2">
            <div className="text-xs text-purple-300/40">Version 1.0</div>
          </div>
        </div>
      </div>

      {/* 右侧边框渐变 */}
      <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-transparent via-purple-400/25 to-transparent"></div>
    </div>
  );
};

export default Sidebar;