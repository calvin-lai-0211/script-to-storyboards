# 样式和主题

本文档详细说明项目中的样式系统、Tailwind CSS 使用、主题配置和最佳实践。

## 技术栈

- **Tailwind CSS 4**: 实用优先的 CSS 框架
- **@tailwindcss/typography**: 富文本样式插件
- **自定义主题**: 专业的蓝紫色系统

## Tailwind 配置

### 1. tailwind.config.ts

**完整配置**:
```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // 自定义颜色系统
      colors: {
        // 主色调：专业蓝色
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',  // 主色
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // 辅助色：优雅紫色
        accent: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',  // 辅助色
          600: '#9333ea',
          700: '#7c3aed',
          800: '#6b21a8',
          900: '#581c87',
        },
        // 中性色：专业灰色
        neutral: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },

      // 渐变背景
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)',
        'gradient-accent': 'linear-gradient(135deg, #60a5fa 0%, #c084fc 100%)',
        'gradient-dark': 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        'gradient-hero': 'linear-gradient(135deg, #1e40af 0%, #7c3aed 50%, #9333ea 100%)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
      },

      // 自定义动画
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },

      // 动画关键帧
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },

      // 自定义阴影
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glow': '0 0 20px rgba(167, 139, 250, 0.5)',
        'glow-lg': '0 0 40px rgba(167, 139, 250, 0.6)',
      },

      // 字体
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};

export default config;
```

---

## 全局样式（index.css）

### 1. Tailwind 导入

```css
@import "tailwindcss";
```

### 2. 基础样式

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### 3. 自定义滚动条

```css
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.1);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ec4899 0%, #a855f7 50%, #6366f1 100%);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #db2777 0%, #9333ea 50%, #4f46e5 100%);
}
```

### 4. 选择文本样式

```css
::selection {
  background: rgba(167, 139, 250, 0.3);
  color: inherit;
}
```

### 5. Typography 样式（重要！）

**原因**: Tailwind v4 不完全支持 prose 修饰符（如 `prose-hr:my-8`），需要在 CSS 中自定义。

```css
.prose {
  color: #334155;
  max-width: none;
}

.prose p {
  margin-bottom: 1rem;
  line-height: 1.875;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4,
.prose h5,
.prose h6 {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  color: #1e293b;
}

.prose hr {
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
  border-color: #e2e8f0;
}

.prose blockquote {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  padding-left: 1rem;
  border-left: 3px solid #a855f7;
  color: #64748b;
  font-style: italic;
}
```

---

## 颜色系统

### 主色调（Primary）

蓝色系统，用于主要按钮、链接、强调元素。

```tsx
<button className="bg-primary-500 hover:bg-primary-600 text-white">
  主要按钮
</button>

<div className="text-primary-700">主要文字</div>
```

### 辅助色（Accent）

紫色系统，用于次要按钮、高亮、装饰元素。

```tsx
<button className="bg-accent-500 hover:bg-accent-600 text-white">
  次要按钮
</button>

<div className="border-l-4 border-accent-500">侧边栏高亮</div>
```

### 中性色（Neutral）

灰色系统，用于背景、边框、文字。

```tsx
<div className="bg-neutral-50 text-neutral-900">
  浅色背景，深色文字
</div>

<div className="border border-neutral-200">边框</div>
```

### Slate 色系（Tailwind 内置）

用于深色导航栏、卡片背景。

```tsx
<aside className="bg-slate-900 text-slate-300">
  深色侧边栏
</aside>
```

---

## 渐变背景

### 使用示例

```tsx
// 主色渐变
<div className="bg-gradient-primary">主色渐变</div>

// 紫色渐变
<div className="bg-gradient-secondary">紫色渐变</div>

// 英雄区渐变
<div className="bg-gradient-hero">英雄区</div>

// 自定义渐变
<div className="bg-gradient-to-r from-blue-500 to-purple-500">
  自定义渐变
</div>

// 激活菜单渐变（MainLayout）
<Link className="bg-gradient-to-r from-blue-500 to-purple-500">
  激活菜单
</Link>
```

---

## 动画系统

### 内置动画

```tsx
// 淡入
<div className="animate-fade-in">淡入</div>

// 上滑
<div className="animate-slide-up">上滑</div>

// 浮动
<div className="animate-float">浮动图标</div>

// 闪烁
<div className="animate-shimmer">加载动画</div>

// Tailwind 内置
<div className="animate-spin">旋转</div>
<div className="animate-pulse">脉冲</div>
```

### 组合使用

```tsx
<Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
<Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />
```

---

## 阴影系统

### 标准阴影（Tailwind 内置）

```tsx
<div className="shadow-sm">小阴影</div>
<div className="shadow-md">中等阴影</div>
<div className="shadow-lg">大阴影</div>
<div className="shadow-xl">超大阴影</div>
<div className="shadow-2xl">巨大阴影</div>
```

### 自定义阴影

```tsx
// 玻璃态阴影
<div className="shadow-glass">玻璃态</div>

// 发光阴影
<div className="shadow-glow">发光效果</div>
<div className="shadow-glow-lg">大发光</div>
```

---

## 常用样式模式

### 1. 卡片样式

```tsx
<div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
  标准卡片
</div>

<div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
  可悬停卡片
</div>
```

### 2. 按钮样式

```tsx
// 主要按钮
<button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
  主要按钮
</button>

// 次要按钮
<button className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors">
  次要按钮
</button>

// 图标按钮
<button className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
  <Icon className="w-5 h-5" />
</button>
```

### 3. 输入框样式

```tsx
<input
  type="text"
  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
  placeholder="输入内容"
/>
```

### 4. 渐变文字

```tsx
<h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
  渐变标题
</h1>
```

### 5. 玻璃态效果

```tsx
<div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg">
  玻璃态容器
</div>
```

### 6. 悬停效果

```tsx
<div className="transition-all duration-300 hover:scale-105 hover:shadow-xl">
  悬停缩放
</div>

<button className="transform transition-transform hover:-translate-y-1">
  悬停上移
</button>
```

---

## 响应式设计

### 断点

Tailwind 内置断点：
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### 使用示例

```tsx
<div className="w-full md:w-1/2 lg:w-1/3">
  响应式宽度
</div>

<h1 className="text-2xl md:text-3xl lg:text-4xl">
  响应式字号
</h1>

<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  响应式网格
</div>

// ImageDisplay 组件
<div className="h-96 lg:h-[700px]">
  移动端 384px，桌面端 700px
</div>
```

---

## Typography（Markdown 渲染）

### 使用 @tailwindcss/typography

```tsx
import ReactMarkdown from 'react-markdown';

<ReactMarkdown className="prose prose-slate max-w-none">
  {markdownContent}
</ReactMarkdown>
```

### 自定义 prose 样式

由于 Tailwind v4 限制，需要在 `index.css` 中自定义：

```css
.prose {
  color: #334155;
  max-width: none;
}

.prose p {
  margin-bottom: 1rem;
  line-height: 1.875;
}

.prose hr {
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
}
```

---

## 最佳实践

### 1. 使用语义化的颜色类名

```tsx
// ❌ 不推荐：直接使用颜色值
<div className="bg-blue-500">...</div>

// ✅ 推荐：使用语义化名称
<div className="bg-primary-500">...</div>
```

### 2. 组合 Tailwind 类

```tsx
// 提取常用样式
const cardStyles = "bg-white rounded-lg shadow-sm border border-slate-200 p-4";

<div className={cardStyles}>卡片 1</div>
<div className={cardStyles}>卡片 2</div>
```

### 3. 条件样式

```tsx
<div className={`
  base-class
  ${active ? "bg-blue-500" : "bg-slate-200"}
  ${disabled && "opacity-50 cursor-not-allowed"}
`}>
  {/* 内容 */}
</div>
```

### 4. 使用 @apply（谨慎）

```css
/* 仅用于高度复用的组件样式 */
.btn-primary {
  @apply px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors;
}
```

### 5. 动画性能优化

```tsx
// 使用 will-change
<div className="will-change-transform transition-transform hover:scale-105">
  优化动画性能
</div>

// 使用 GPU 加速
<div className="transform-gpu">
  GPU 加速
</div>
```

---

## 主题切换（未来功能）

### 暗色模式支持

Tailwind 支持暗色模式，可以通过 `dark:` 前缀实现：

```tsx
<div className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
  支持暗色模式
</div>
```

**配置**:
```typescript
// tailwind.config.ts
export default {
  darkMode: 'class', // 或 'media'
  // ...
};
```

**切换逻辑**:
```tsx
const [darkMode, setDarkMode] = useState(false);

useEffect(() => {
  if (darkMode) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}, [darkMode]);
```

---

## 总结

样式系统要点：
1. **Tailwind CSS 4**: 实用优先，快速开发
2. **自定义主题**: 蓝紫色专业配色
3. **Typography 插件**: Markdown 富文本渲染
4. **自定义动画**: 淡入、滑动、浮动、闪烁
5. **响应式设计**: 移动优先，断点完善
6. **性能优化**: GPU 加速、will-change

---

**相关文档**:
- [组件开发](./components.md)
- [项目结构](./project-structure.md)
- [代码质量](./code-quality.md)
