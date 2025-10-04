import React, { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'

// 动态懒加载 Tiptap 编辑器
const TiptapEditor = lazy(() =>
  import('./TiptapEditor').then((module) => ({ default: module.TiptapEditor }))
)

interface TiptapEditorLazyProps {
  content: string
  onChange: (markdown: string) => void
  placeholder?: string
  editable?: boolean
}

/**
 * Tiptap 编辑器懒加载包装组件
 * 只有在需要编辑时才加载完整的 Tiptap 库，减少初始包大小
 */
export const TiptapEditorLazy: React.FC<TiptapEditorLazyProps> = (props) => {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center rounded-lg border border-gray-300 bg-white">
          <div className="text-center">
            <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-blue-500" />
            <p className="text-gray-600">加载编辑器中...</p>
          </div>
        </div>
      }
    >
      <TiptapEditor {...props} />
    </Suspense>
  )
}
