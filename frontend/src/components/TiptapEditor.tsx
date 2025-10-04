import React, { useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Typography from '@tiptap/extension-typography'
import Placeholder from '@tiptap/extension-placeholder'
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Heading3,
  Quote,
  Undo,
  Redo,
  Code,
  Minus
} from 'lucide-react'
import { markdownToHTML, htmlToMarkdown } from '../utils/markdownConverter'

interface TiptapEditorProps {
  content: string
  onChange: (markdown: string) => void
  placeholder?: string
  editable?: boolean
}

export const TiptapEditor: React.FC<TiptapEditorProps> = ({
  content,
  onChange,
  placeholder = '开始输入剧本内容...',
  editable = true
}) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3]
        },
        hardBreak: {
          // 支持 Shift+Enter 插入硬换行
          keepMarks: true
        }
      }),
      Typography,
      Placeholder.configure({
        placeholder
      })
    ],
    content: markdownToHTML(content),
    editable,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      const markdown = htmlToMarkdown(html)
      onChange(markdown)
    },
    // 支持 Shift+Enter 插入换行
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none'
      }
    },
    // 编辑器创建后，将光标移到文档开头的空白位置，避免误触发 active 状态
    onCreate: ({ editor }) => {
      // 将光标设置到文档开头
      editor.commands.setTextSelection(0)
      // 然后失去焦点，这样按钮不会显示为激活状态
      editor.commands.blur()
    }
  })

  // 当外部 content 变化时更新编辑器（但不触发 onChange）
  useEffect(() => {
    if (editor && content !== htmlToMarkdown(editor.getHTML())) {
      editor.commands.setContent(markdownToHTML(content))
    }
  }, [content, editor])

  if (!editor) {
    return null
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Toolbar */}
      {editable && (
        <div className="flex flex-wrap gap-1 border-b border-gray-200 bg-gray-50 p-2">
          {/* Text formatting */}
          <button
            type="button"
            onClick={() => editor.chain().focus().toggleBold().run()}
            disabled={!editor.can().chain().focus().toggleBold().run()}
            className={`rounded p-2 hover:bg-gray-200 disabled:opacity-30 ${
              editor.isFocused && editor.isActive('bold') ? 'bg-gray-300' : ''
            }`}
            title="加粗 (Ctrl+B)"
          >
            <Bold size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            disabled={!editor.can().chain().focus().toggleItalic().run()}
            className={`rounded p-2 hover:bg-gray-200 disabled:opacity-30 ${
              editor.isFocused && editor.isActive('italic') ? 'bg-gray-300' : ''
            }`}
            title="斜体 (Ctrl+I)"
          >
            <Italic size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().toggleCode().run()}
            disabled={!editor.can().chain().focus().toggleCode().run()}
            className={`rounded p-2 hover:bg-gray-200 disabled:opacity-30 ${
              editor.isFocused && editor.isActive('code') ? 'bg-gray-300' : ''
            }`}
            title="行内代码"
          >
            <Code size={18} />
          </button>

          <div className="mx-1 h-6 w-px bg-gray-300" />

          {/* Headings */}
          <button
            type="button"
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('heading', { level: 1 }) ? 'bg-gray-300' : ''
            }`}
            title="一级标题"
          >
            <Heading1 size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('heading', { level: 2 }) ? 'bg-gray-300' : ''
            }`}
            title="二级标题"
          >
            <Heading2 size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('heading', { level: 3 }) ? 'bg-gray-300' : ''
            }`}
            title="三级标题"
          >
            <Heading3 size={18} />
          </button>

          <div className="mx-1 h-6 w-px bg-gray-300" />

          {/* Lists */}
          <button
            type="button"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('bulletList') ? 'bg-gray-300' : ''
            }`}
            title="无序列表"
          >
            <List size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('orderedList') ? 'bg-gray-300' : ''
            }`}
            title="有序列表"
          >
            <ListOrdered size={18} />
          </button>

          <div className="mx-1 h-6 w-px bg-gray-300" />

          {/* Blockquote and HR */}
          <button
            type="button"
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            className={`rounded p-2 hover:bg-gray-200 ${
              editor.isFocused && editor.isActive('blockquote') ? 'bg-gray-300' : ''
            }`}
            title="引用"
          >
            <Quote size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().setHorizontalRule().run()}
            className="rounded p-2 hover:bg-gray-200"
            title="分隔线"
          >
            <Minus size={18} />
          </button>

          <div className="mx-1 h-6 w-px bg-gray-300" />

          {/* Undo/Redo */}
          <button
            type="button"
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().chain().focus().undo().run()}
            className="rounded p-2 hover:bg-gray-200 disabled:opacity-30"
            title="撤销 (Ctrl+Z)"
          >
            <Undo size={18} />
          </button>

          <button
            type="button"
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().chain().focus().redo().run()}
            className="rounded p-2 hover:bg-gray-200 disabled:opacity-30"
            title="重做 (Ctrl+Shift+Z)"
          >
            <Redo size={18} />
          </button>
        </div>
      )}

      {/* Editor Content */}
      <EditorContent
        editor={editor}
        className="prose prose-sm max-w-none flex-1 overflow-auto p-4"
      />
    </div>
  )
}
