import React from 'react'
import { Image, Layers, ChevronRight, Sparkles } from 'lucide-react'

interface SidebarProps {
  currentPage: string
  setCurrentPage: (page: string) => void
}

const Sidebar: React.FC<SidebarProps> = ({ currentPage, setCurrentPage }) => {
  const menuItems = [
    {
      id: 'character',
      name: 'Character Generator',
      icon: Image,
      description: ''
    },
    {
      id: 'Gallery',
      name: 'Gallery',
      icon: Layers,
      description: 'View your creations',
      disabled: true
    }
  ]

  return (
    <div className="relative flex h-full w-64 flex-col">
      {/* 艺术感背景 - 更明亮协调 */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-700 via-slate-800 to-slate-900"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-800/30 via-indigo-800/25 to-cyan-900/20"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-purple-600/10 via-indigo-600/8 to-cyan-600/6"></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-purple-500/8 via-transparent to-transparent"></div>

      {/* 艺术感装饰网格 */}
      <div className="absolute inset-0 opacity-20">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
            linear-gradient(rgba(168,85,247,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px)
          `,
            backgroundSize: '24px 24px'
          }}
        ></div>
      </div>

      <div className="relative flex h-full flex-col">
        {/* 菜单项 - 改进设计 */}
        <nav className="flex-1 space-y-2 px-4 py-6">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.id
            const isDisabled = item.disabled

            return (
              <button
                key={item.id}
                onClick={() => !isDisabled && setCurrentPage(item.id)}
                disabled={isDisabled}
                className={`group relative w-full overflow-hidden rounded-xl text-left transition-all duration-200 ${
                  isActive
                    ? 'border border-purple-400/40 bg-gradient-to-r from-purple-600/25 via-indigo-600/20 to-cyan-600/15 shadow-lg shadow-purple-500/10'
                    : isDisabled
                      ? 'cursor-not-allowed border border-white/5 bg-white/5 opacity-50'
                      : 'border border-white/10 bg-white/8 hover:border-purple-400/20 hover:bg-gradient-to-r hover:from-purple-600/15 hover:to-cyan-600/10'
                } `}
              >
                {/* 活动状态的发光背景 */}
                {isActive && (
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/8 via-indigo-500/6 to-cyan-500/5"></div>
                )}

                <div className="relative flex items-center justify-between p-3">
                  <div className="flex items-center space-x-3">
                    {/* 图标区域 */}
                    <div
                      className={`rounded-lg p-2 transition-all duration-200 ${
                        isActive
                          ? 'scale-105 bg-gradient-to-br from-purple-500/30 via-indigo-500/25 to-cyan-500/20 shadow-lg'
                          : 'bg-white/10 group-hover:scale-105 group-hover:bg-gradient-to-br group-hover:from-purple-500/20 group-hover:to-cyan-500/15'
                      } `}
                    >
                      <Icon
                        className={`h-5 w-5 transition-colors duration-200 ${
                          isActive ? 'text-white' : 'text-white/80 group-hover:text-white'
                        }`}
                      />
                    </div>

                    {/* 文本内容 */}
                    <div className="flex-1">
                      <div
                        className={`font-semibold transition-colors duration-200 ${
                          isActive ? 'text-white' : 'text-white/90 group-hover:text-white'
                        }`}
                      >
                        {item.name}
                      </div>
                      <div className="mt-0.5 text-sm text-white/60">{item.description}</div>
                    </div>
                  </div>

                  {/* 右侧箭头指示器 */}
                  <ChevronRight
                    className={`h-4 w-4 transition-all duration-200 ${
                      isActive
                        ? 'translate-x-0 text-white opacity-100'
                        : '-translate-x-1 text-white/40 opacity-0 group-hover:translate-x-0 group-hover:opacity-100'
                    }`}
                  />
                </div>

                {/* 底部装饰线 */}
                {isActive && (
                  <div className="absolute right-0 bottom-0 left-0 h-0.5 bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500"></div>
                )}
              </button>
            )
          })}
        </nav>

        {/* 底部装饰 - 艺术感设计 */}
        <div className="border-t border-purple-500/20 p-4">
          <div className="flex items-center justify-center space-x-2 text-purple-200/70">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-medium">Video Creation</span>
            <Sparkles className="h-4 w-4 text-pink-400" />
          </div>

          {/* 版本信息 */}
          <div className="mt-2 text-center">
            <div className="text-xs text-purple-300/40">Version 1.0</div>
          </div>
        </div>
      </div>

      {/* 右侧边框渐变 */}
      <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-transparent via-purple-400/25 to-transparent"></div>
    </div>
  )
}

export default Sidebar
