import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, User, MapPin, Package, ChevronLeft, ChevronRight, Film } from 'lucide-react'

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const navItems = [
    {
      icon: Home,
      label: '剧集',
      path: '/',
      description: '浏览所有剧集'
    },
    {
      icon: User,
      label: '角色',
      path: '/characters',
      description: '所有角色资产'
    },
    {
      icon: MapPin,
      label: '场景',
      path: '/scenes',
      description: '所有场景资产'
    },
    {
      icon: Package,
      label: '道具',
      path: '/props',
      description: '所有道具资产'
    }
  ]

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 左侧导航栏 */}
      <aside
        className={`relative flex flex-col border-r border-slate-800 bg-slate-900 shadow-2xl transition-all duration-300 ${
          collapsed ? 'w-16' : 'w-48'
        }`}
      >
        {/* Logo 区域 */}
        <div
          className={`flex h-16 items-center border-b border-slate-800 ${collapsed ? 'justify-center' : 'px-4'}`}
        >
          {!collapsed ? (
            <div className="flex items-center space-x-2">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
                <Film className="h-4 w-4 text-white" />
              </div>
              <h1 className="truncate text-base font-bold text-white">Drama Creator</h1>
            </div>
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
              <Film className="h-4 w-4 text-white" />
            </div>
          )}
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center rounded-lg transition-all duration-200 ${
                  collapsed ? 'justify-center p-3' : 'space-x-3 px-3 py-2.5'
                } ${
                  active
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/50'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`h-5 w-5 flex-shrink-0 ${active ? 'text-white' : 'text-slate-400'}`}
                />
                {!collapsed && (
                  <div className="min-w-0 flex-1">
                    <div
                      className={`text-sm font-medium ${active ? 'text-white' : 'text-slate-300'}`}
                    >
                      {item.label}
                    </div>
                  </div>
                )}
              </Link>
            )
          })}
        </nav>

        {/* 底部按钮区域 */}
        <div className="cursor-pointer border-t border-slate-800">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex w-full items-center justify-center rounded-lg p-2.5 transition-colors duration-200 hover:bg-slate-800"
            title={collapsed ? '展开侧边栏' : '收起侧边栏'}
          >
            {collapsed ? (
              <ChevronRight className="h-5 w-5 text-slate-400" />
            ) : (
              <ChevronLeft className="h-5 w-5 text-slate-400" />
            )}
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}

export default MainLayout
