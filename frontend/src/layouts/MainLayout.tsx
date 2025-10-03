import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Home,
  User,
  MapPin,
  Package,
  ChevronLeft,
  ChevronRight,
  Film,
} from "lucide-react";

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navItems = [
    {
      icon: Home,
      label: "剧集",
      path: "/",
      description: "浏览所有剧集",
    },
    {
      icon: User,
      label: "角色",
      path: "/characters",
      description: "所有角色资产",
    },
    {
      icon: MapPin,
      label: "场景",
      path: "/scenes",
      description: "所有场景资产",
    },
    {
      icon: Package,
      label: "道具",
      path: "/props",
      description: "所有道具资产",
    },
  ];

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 左侧导航栏 */}
      <aside
        className={`relative bg-slate-900 border-r border-slate-800 shadow-2xl transition-all duration-300 flex flex-col ${
          collapsed ? "w-16" : "w-48"
        }`}
      >
        {/* Logo 区域 */}
        <div
          className={`h-16 flex items-center border-b border-slate-800 ${collapsed ? "justify-center" : "px-4"}`}
        >
          {!collapsed ? (
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Film className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-base font-bold text-white truncate">
                Drama Creator
              </h1>
            </div>
          ) : (
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Film className="w-4 h-4 text-white" />
            </div>
          )}
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group flex items-center rounded-lg transition-all duration-200 ${
                  collapsed ? "justify-center p-3" : "px-3 py-2.5 space-x-3"
                } ${
                  active
                    ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/50"
                    : "hover:bg-slate-800 text-slate-400 hover:text-white"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 ${active ? "text-white" : "text-slate-400"}`}
                />
                {!collapsed && (
                  <div className="flex-1 min-w-0">
                    <div
                      className={`text-sm font-medium ${active ? "text-white" : "text-slate-300"}`}
                    >
                      {item.label}
                    </div>
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* 底部按钮区域 */}
        <div className="border-t border-slate-800 cursor-pointer">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full p-2.5 hover:bg-slate-800 rounded-lg transition-colors duration-200 flex items-center justify-center"
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
          >
            {collapsed ? (
              <ChevronRight className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronLeft className="w-5 h-5 text-slate-400" />
            )}
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
};

export default MainLayout;
