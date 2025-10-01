import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import CharacterViewer from './pages/CharacterViewer'
import Header from './components/Header'
import Sidebar from './components/Sidebar'

function App() {
  const [currentPage, setCurrentPage] = useState('character')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-purple-50/10 flex flex-col">
        {/* 移动端侧边栏遮罩 */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* 统一的页面 Header - 在小屏幕上隐藏 */}
        <div className="hidden lg:block">
          <Header siteName="Video Creation" />
        </div>

        <div className="flex flex-1">
          {/* 侧边栏 */}
          <div className={`
            fixed lg:static inset-y-0 left-0 z-50 lg:z-auto
            transform transition-transform duration-300 ease-in-out lg:transform-none
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}>
            <Sidebar
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
            />
          </div>

          {/* 主内容区域 */}
          <div className="flex-1 flex flex-col min-w-0 lg:ml-0">
            {/* 移动端菜单按钮 */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden fixed top-4 left-4 z-30 p-3 bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 hover:bg-white hover:scale-105 transition-all duration-200"
            >
              <Menu className="w-6 h-6 text-gray-700" />
            </button>

            {/* 移动端关闭按钮 */}
            {sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden fixed top-4 right-4 z-60 p-3 bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 hover:bg-white hover:scale-105 transition-all duration-200"
              >
                <X className="w-6 h-6 text-gray-700" />
              </button>
            )}

            <main className="flex-1 relative">
              <Routes>
                <Route path="/character/:id" element={<CharacterViewer />} />
              </Routes>
            </main>
          </div>
        </div>

        {/* 装饰性背景元素 */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
          {/* 大型装饰球 */}
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-primary-300/10 to-accent-300/10 rounded-full blur-3xl animate-float"></div>
          <div className="absolute top-1/2 -left-40 w-60 h-60 bg-gradient-to-br from-accent-300/10 to-purple-300/10 rounded-full blur-2xl animate-float" style={{ animationDelay: '3s' }}></div>
          <div className="absolute -bottom-40 right-1/4 w-96 h-96 bg-gradient-to-br from-purple-300/10 to-pink-300/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '6s' }}></div>

          {/* 网格装饰 */}
          <div className="absolute inset-0 opacity-[0.02]">
            <div className="h-full w-full" style={{
              backgroundImage: `
                linear-gradient(rgba(99, 102, 241, 0.5) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.5) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px'
            }}></div>
          </div>

          {/* 光线效果 */}
          <div className="absolute top-0 left-1/2 w-px h-full bg-gradient-to-b from-primary-200/20 via-transparent to-transparent"></div>
          <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-accent-200/20 to-transparent"></div>
        </div>
      </div>
    </Router>
  )
}

export default App
