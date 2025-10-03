import React from 'react'
import { Zap } from 'lucide-react'

interface HeaderProps {
  siteName?: string
}

const Header: React.FC<HeaderProps> = ({ siteName = 'Video Creation' }) => {
  return (
    <header className="relative overflow-hidden border-b border-purple-500/30 bg-gradient-to-r from-indigo-900 via-purple-900 to-pink-900">
      {/* 背景层 */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/15 to-pink-500/10"></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-400/5 via-transparent to-transparent"></div>

      {/* 装饰光点 */}
      <div className="absolute top-3 right-12 h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50"></div>
      <div className="absolute top-5 right-24 h-1 w-1 animate-pulse rounded-full bg-pink-400 shadow-sm shadow-pink-400/50 delay-700"></div>
      <div className="absolute top-2 right-36 h-0.5 w-0.5 animate-pulse rounded-full bg-violet-400 delay-1000"></div>

      <div className="relative flex items-center justify-between px-6 py-2">
        <div className="group flex items-center">
          {/* Logo区域 */}
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 p-1 shadow-lg transition-all duration-300 group-hover:scale-105">
              <img
                src="/logo.svg"
                alt="Video Creation Logo"
                className="h-full w-full drop-shadow-sm"
              />
            </div>
            {/* 彩虹发光效果 */}
            <div className="absolute inset-0 -z-10 rounded-xl bg-gradient-to-r from-cyan-400/40 via-purple-400/40 to-pink-400/40 blur-lg transition-all duration-300 group-hover:blur-xl"></div>
            <div className="absolute inset-0 -z-20 rounded-xl bg-gradient-to-r from-cyan-300/20 via-purple-300/20 to-pink-300/20 blur-2xl transition-all duration-300 group-hover:blur-3xl"></div>
          </div>

          {/* 站点名称 - 提高对比度 */}
          <div className="ml-4">
            <h1 className="font-display text-xl font-bold tracking-wide text-white">{siteName}</h1>
            <div className="mt-0.5 flex items-center">
              <Zap className="mr-1 h-3 w-3 text-cyan-400 drop-shadow-sm" />
              <span className="text-xs font-medium text-cyan-100">AI-Powered Creation</span>
            </div>
          </div>
        </div>
      </div>

      {/* 底部分割线 */}
      <div className="absolute right-0 bottom-0 left-0 h-px bg-gradient-to-r from-transparent via-purple-400/60 to-transparent"></div>
      <div className="absolute right-0 bottom-0 left-0 h-0.5 bg-gradient-to-r from-cyan-500/20 via-purple-500/30 to-pink-500/20 blur-sm"></div>
    </header>
  )
}

export default Header
