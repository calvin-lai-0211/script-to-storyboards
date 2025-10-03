import React from "react";
import { Zap } from "lucide-react";

interface HeaderProps {
  siteName?: string;
}

const Header: React.FC<HeaderProps> = ({ siteName = "Video Creation" }) => {
  return (
    <header className="relative overflow-hidden bg-gradient-to-r from-indigo-900 via-purple-900 to-pink-900 border-b border-purple-500/30">
      {/* 背景层 */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/15 to-pink-500/10"></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-400/5 via-transparent to-transparent"></div>

      {/* 装饰光点 */}
      <div className="absolute top-3 right-12 w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-cyan-400/50 shadow-sm"></div>
      <div className="absolute top-5 right-24 w-1 h-1 bg-pink-400 rounded-full animate-pulse delay-700 shadow-pink-400/50 shadow-sm"></div>
      <div className="absolute top-2 right-36 w-0.5 h-0.5 bg-violet-400 rounded-full animate-pulse delay-1000"></div>

      <div className="relative flex items-center justify-between px-6 py-2">
        <div className="flex items-center group">
          {/* Logo区域 */}
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-105 transition-all duration-300 p-1">
              <img
                src="/logo.svg"
                alt="Video Creation Logo"
                className="w-full h-full drop-shadow-sm"
              />
            </div>
            {/* 彩虹发光效果 */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-cyan-400/40 via-purple-400/40 to-pink-400/40 blur-lg group-hover:blur-xl transition-all duration-300 -z-10"></div>
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-cyan-300/20 via-purple-300/20 to-pink-300/20 blur-2xl group-hover:blur-3xl transition-all duration-300 -z-20"></div>
          </div>

          {/* 站点名称 - 提高对比度 */}
          <div className="ml-4">
            <h1 className="text-xl font-display font-bold text-white tracking-wide">
              {siteName}
            </h1>
            <div className="flex items-center mt-0.5">
              <Zap className="w-3 h-3 text-cyan-400 mr-1 drop-shadow-sm" />
              <span className="text-xs text-cyan-100 font-medium">
                AI-Powered Creation
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 底部分割线 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-400/60 to-transparent"></div>
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500/20 via-purple-500/30 to-pink-500/20 blur-sm"></div>
    </header>
  );
};

export default Header;
