# 组件设计和使用

本文档详细说明项目中的组件设计、分类、使用方法和最佳实践。

## 组件分类

### 1. 布局组件 (Layout Components)
定义页面的整体结构和导航。

- **MainLayout** - 主布局（侧边栏 + 内容区）

### 2. 页面组件 (Page Components)
对应路由的顶层组件，负责数据获取和页面布局。

- **ScriptsList** - 剧集列表
- **Workspace** - 分镜工作台
- **Characters** - 角色列表
- **Scenes** - 场景列表
- **Props** - 道具列表
- **CharacterViewer** - 角色详情
- **SceneViewer** - 场景详情
- **PropViewer** - 道具详情

### 3. Tab 组件 (Tab Components)
Workspace 中的标签页组件。

- **ScriptTab** - 原文 Tab
- **StoryboardTab** - 分镜 Tab
- **MemoryTab** - Memory Tab
- **WorkflowTab** - 流程控制 Tab

### 4. UI 组件 (UI Components)
可复用的通用组件。

- **Header** - 顶部标题
- **Sidebar** - 侧边栏导航
- **BackButton** - 返回按钮
- **ImageDisplay** - 图像展示
- **ImagePreviewModal** - 图像预览弹窗
- **PromptInput** - 提示词输入

## 主要组件详解

### MainLayout - 主布局

**路径**: `/src/layouts/MainLayout.tsx`

**职责**: 提供整个应用的布局结构，包含侧边栏导航和主内容区。

**Props**:
```typescript
interface MainLayoutProps {
  children: React.ReactNode;  // 子路由内容
}
```

**特性**:
- 支持侧边栏折叠/展开
- 深色导航栏（slate-900）
- 渐变高亮的激活状态
- 响应式设计

**导航项配置**:
```typescript
const navItems = [
  { icon: Home, label: "剧集", path: "/", description: "浏览所有剧集" },
  { icon: User, label: "角色", path: "/characters", description: "所有角色资产" },
  { icon: MapPin, label: "场景", path: "/scenes", description: "所有场景资产" },
  { icon: Package, label: "道具", path: "/props", description: "所有道具资产" },
];
```

**使用示例**:
```typescript
// App.tsx
import MainLayout from "./layouts/MainLayout";

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<ScriptsList />} />
          {/* 其他路由 */}
        </Routes>
      </MainLayout>
    </Router>
  );
}
```

**样式特点**:
- 折叠状态：宽度 64px（w-16）
- 展开状态：宽度 192px（w-48）
- Logo 区域：高度 64px（h-16）
- 激活菜单：渐变背景 `from-blue-500 to-purple-500`
- 悬停效果：`hover:bg-slate-800`

---

### StoryboardTab - 分镜 Tab

**路径**: `/src/components/tabs/StoryboardTab.tsx`

**职责**: 展示分镜脚本的层级结构（场景 → 镜头 → 子镜头）。

**Props**:
```typescript
interface StoryboardTabProps {
  scriptKey: string;  // 剧集唯一标识
}
```

**核心功能**:
1. **三层折叠展开**:
   - 场景层级折叠/展开
   - 镜头层级折叠/展开
   - 子镜头详情展示

2. **批量操作**:
   - 全部展开/折叠所有场景
   - 展开/折叠单个场景的所有镜头

3. **数据缓存**:
   - 优先从 Store 读取缓存
   - 无缓存时自动请求
   - 支持手动刷新

4. **请求取消**:
   - 组件卸载时自动取消请求
   - 使用 AbortController

**数据结构**:
```typescript
interface Scene {
  scene_number: string;
  scene_description: string;
  shots: Shot[];
}

interface Shot {
  shot_number: string;
  shot_description: string;
  subShots: SubShot[];
}

interface SubShot {
  id: number;
  sub_shot_number: string;
  camera_angle: string;
  characters: string[];
  scene_context: string[];
  key_props: string[];
  image_prompt: string;
  dialogue_sound: string;
  duration_seconds: number;
  notes: string;
}
```

**使用示例**:
```typescript
import StoryboardTab from "@/components/tabs/StoryboardTab";

<StoryboardTab scriptKey="da4ef19d-5965-41c3-a971-f17d0ce06ef7" />
```

**关键逻辑**:

1. **数据获取和缓存**:
```typescript
useEffect(() => {
  // 1. 优先检查 Store 缓存
  const cachedStoryboard = getStoryboard(scriptKey);
  if (cachedStoryboard) {
    console.debug("StoryboardTab: Using cached storyboard");
    setScenes(cachedStoryboard);
    return;
  }

  // 2. 无缓存时请求
  const abortController = new AbortController();
  fetchStoryboards(abortController.signal);

  // 3. 组件卸载时取消请求
  return () => {
    abortController.abort();
  };
}, [scriptKey, getStoryboard]);
```

2. **数据转换**:
```typescript
// 将扁平数据转换为层级结构
const scenesMap = new Map<string, Scene>();

data.storyboards.forEach((item: any) => {
  const sceneKey = item.scene_number as string;

  // 创建或获取场景
  if (!scenesMap.has(sceneKey)) {
    scenesMap.set(sceneKey, {
      scene_number: item.scene_number,
      scene_description: item.scene_description,
      shots: [],
    });
  }

  // 添加镜头和子镜头
  // ...
});
```

3. **折叠状态管理**:
```typescript
// 使用 Set 管理展开状态
const [expandedScenes, setExpandedScenes] = useState<Set<string>>(new Set());
const [expandedShots, setExpandedShots] = useState<Set<string>>(new Set());

const toggleScene = (sceneNumber: string) => {
  const newExpanded = new Set(expandedScenes);
  if (newExpanded.has(sceneNumber)) {
    newExpanded.delete(sceneNumber);
  } else {
    newExpanded.add(sceneNumber);
  }
  setExpandedScenes(newExpanded);
};
```

**样式亮点**:
- 场景：渐变背景 `from-blue-50 to-purple-50`
- 镜头：悬停效果 `hover:bg-slate-50`
- 子镜头：圆角卡片 `rounded-lg border border-slate-200`
- 提示词：彩色背景 `bg-blue-50` / `bg-purple-50` / `bg-amber-50`

---

### ImageDisplay - 图像展示

**路径**: `/src/components/ImageDisplay.tsx`

**职责**: 展示 AI 生成的图像，支持加载状态、悬停效果和全屏预览。

**Props**:
```typescript
interface ImageDisplayProps {
  imageUrl: string | null;  // 图像 URL
  loading?: boolean;         // 加载状态
}
```

**核心功能**:
1. **三种状态展示**:
   - 空状态：显示占位图标和提示文字
   - 加载状态：显示动画和进度提示
   - 图片状态：展示图像和操作按钮

2. **交互效果**:
   - 悬停时缩放和亮度增强
   - 点击图片全屏预览
   - 显示底部信息栏

3. **视觉特效**:
   - 渐变背景
   - 装饰性网格
   - 波浪加载动画
   - 浮动图标

**使用示例**:
```typescript
import ImageDisplay from "@/components/ImageDisplay";

<ImageDisplay
  imageUrl="https://example.com/image.jpg"
  loading={false}
/>
```

**关键特性**:

1. **加载动画**:
```typescript
{loading && (
  <div className="absolute inset-0 flex flex-col items-center justify-center">
    {/* 双环旋转动画 */}
    <div className="relative mb-6">
      <div className="w-16 h-16 border-4 border-slate-200 border-t-blue-500 rounded-full animate-spin"></div>
      <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-purple-500 rounded-full animate-spin"
        style={{ animationDirection: "reverse", animationDuration: "1.5s" }}>
      </div>
    </div>

    {/* 提示文字 */}
    <div className="flex items-center space-x-2">
      <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
      <span className="text-lg font-semibold">AI 正在创作中</span>
      <Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />
    </div>
  </div>
)}
```

2. **悬停效果**:
```typescript
const [isHovered, setIsHovered] = useState(false);

<img
  src={imageUrl}
  className={`w-full h-full object-contain ${isHovered ? "scale-105" : "scale-100"}`}
  style={{
    filter: isHovered ? "brightness(1.05) contrast(1.05)" : "none",
  }}
  onClick={handlePreview}
/>
```

3. **全屏预览**:
```typescript
const [showPreview, setShowPreview] = useState(false);

{showPreview && imageUrl && (
  <ImagePreviewModal
    imageUrl={imageUrl}
    onClose={() => setShowPreview(false)}
  />
)}
```

**样式细节**:
- 容器高度：`h-96 lg:h-[700px]`（响应式）
- 圆角：`rounded-2xl`
- 边框：`border-2 border-slate-300`
- 阴影：`shadow-lg hover:shadow-xl`
- 背景：`bg-gradient-to-br from-white/50 to-slate-50/80`

---

### Workspace - 分镜工作台

**路径**: `/src/pages/Workspace.tsx`

**职责**: 提供多 Tab 切换的工作环境，展示剧集的原文、分镜、Memory 和流程控制。

**路由**: `/episode/:key?tab=xxx`

**核心功能**:
1. **Tab 切换**:
   - 支持 4 个 Tab：script、storyboard、memory、workflow
   - Tab 状态同步到 URL 参数
   - 刷新页面保持 Tab 状态

2. **URL 参数管理**:
   - 使用 `useSearchParams` 读取和更新 URL
   - 默认 Tab：`script`

3. **剧集上下文**:
   - 从 `useEpisodeStore` 获取当前剧集信息
   - 显示剧集标题和集数

**使用示例**:
```typescript
// 路由配置
<Route path="/episode/:key" element={<Workspace />} />

// 访问特定 Tab
navigate('/episode/da4ef19d?tab=storyboard');
```

**关键实现**:

1. **Tab 状态管理**:
```typescript
const [searchParams, setSearchParams] = useSearchParams();
const currentTab = searchParams.get("tab") || "script";

const handleTabChange = (tabId: string) => {
  setSearchParams({ tab: tabId });
};
```

2. **Tab 配置**:
```typescript
const tabs = [
  { id: "script", label: "原文", icon: FileText },
  { id: "storyboard", label: "分镜", icon: Film },
  { id: "memory", label: "Memory", icon: Brain },
  { id: "workflow", label: "流程控制", icon: GitBranch },
];
```

3. **Tab 内容渲染**:
```typescript
{currentTab === "script" && <ScriptTab scriptKey={key} />}
{currentTab === "storyboard" && <StoryboardTab scriptKey={key} />}
{currentTab === "memory" && <MemoryTab scriptKey={key} />}
{currentTab === "workflow" && <WorkflowTab scriptKey={key} />}
```

**样式特点**:
- Tab 栏：`border-b border-slate-200`
- 激活 Tab：`border-b-2 border-blue-600 text-blue-600`
- 未激活 Tab：`text-slate-600 hover:text-slate-900`

---

### ScriptTab - 原文 Tab

**路径**: `/src/components/tabs/ScriptTab.tsx`

**职责**: 展示剧集的原文内容（Markdown 格式）。

**核心功能**:
1. 使用 `react-markdown` 渲染 Markdown
2. 支持手动刷新
3. 数据缓存（Store）
4. 请求取消（AbortController）

**使用示例**:
```typescript
<ScriptTab scriptKey="da4ef19d-5965-41c3-a971-f17d0ce06ef7" />
```

**Markdown 样式**:
```typescript
<ReactMarkdown className="prose prose-slate max-w-none">
  {script}
</ReactMarkdown>
```

**注意**: Tailwind v4 需要在 `index.css` 中自定义 prose 样式：
```css
.prose p {
  margin-top: 1rem;
  margin-bottom: 1rem;
  line-height: 1.875;
}

.prose hr {
  margin-top: 1.25rem;
  margin-bottom: 1.25rem;
}
```

---

### MemoryTab - Memory Tab

**路径**: `/src/components/tabs/MemoryTab.tsx`

**职责**: 展示剧集的 Memory 数据（类似知识库）。

**核心功能**:
- 展示 Memory 内容
- 支持 Markdown 渲染
- 数据缓存和刷新

---

### WorkflowTab - 流程控制 Tab

**路径**: `/src/components/tabs/WorkflowTab.tsx`

**职责**: 提供剧集生成流程的控制面板（如触发分镜生成、角色生成等）。

**核心功能**:
- 流程状态显示
- 操作按钮（生成、刷新等）
- 进度跟踪

---

## 组件最佳实践

### 1. Props 类型定义

始终使用 TypeScript 接口定义 Props：

```typescript
interface MyComponentProps {
  title: string;
  count?: number;  // 可选参数
  onSubmit: (value: string) => void;  // 回调函数
  children?: React.ReactNode;  // 子元素
}

const MyComponent: React.FC<MyComponentProps> = ({ title, count = 0, onSubmit, children }) => {
  // ...
};
```

### 2. 状态管理原则

**组件内状态（useState）**:
- UI 状态（展开/折叠、悬停等）
- 临时状态（加载、错误）

**全局状态（Zustand）**:
- 跨组件共享的数据
- 需要持久化的数据
- API 响应数据

**示例**:
```typescript
// 组件内状态：折叠状态
const [collapsed, setCollapsed] = useState(false);

// 全局状态：剧集数据
const { currentEpisode, setCurrentEpisode } = useEpisodeStore();
```

### 3. 数据获取模式

**推荐模式**:
```typescript
useEffect(() => {
  // 1. 检查缓存
  const cached = getDataFromStore(id);
  if (cached) {
    setData(cached);
    return;
  }

  // 2. 无缓存时请求
  const abortController = new AbortController();
  fetchData(id, abortController.signal);

  // 3. 清理：取消请求
  return () => {
    abortController.abort();
  };
}, [id, getDataFromStore]);
```

### 4. 错误处理

统一的错误处理和展示：

```typescript
const [error, setError] = useState<string | null>(null);

try {
  const data = await apiCall(...);
  setError(null);
} catch (err) {
  if ((err as Error).name === "AbortError") {
    console.debug("Request cancelled");
    return;
  }
  console.error("Error:", err);
  setError("数据加载失败");
}

// UI 展示
{error && (
  <div className="flex items-center justify-center">
    <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
    <p className="text-red-600">{error}</p>
  </div>
)}
```

### 5. 加载状态

提供良好的加载反馈：

```typescript
{loading && (
  <div className="flex items-center justify-center">
    <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
    <p className="text-slate-600">加载中...</p>
  </div>
)}
```

### 6. 空状态

当没有数据时，提供友好的空状态：

```typescript
{data.length === 0 && (
  <div className="text-center">
    <Film className="w-16 h-16 text-slate-300 mx-auto mb-4" />
    <p className="text-slate-500">暂无数据</p>
  </div>
)}
```

### 7. 组件拆分原则

当组件超过 300 行时，考虑拆分：

**拆分策略**:
1. 提取子组件（如列表项、卡片）
2. 提取自定义 Hooks（如数据获取逻辑）
3. 提取工具函数（如数据转换）

**示例**:
```typescript
// 拆分前：StoryboardTab 有 500 行

// 拆分后：
// - StoryboardTab.tsx（主组件，200 行）
// - SceneCard.tsx（场景卡片，100 行）
// - ShotCard.tsx（镜头卡片，100 行）
// - useStoryboardData.ts（数据获取 Hook，100 行）
```

### 8. 性能优化

**使用 React.memo**:
```typescript
const SceneCard = React.memo<SceneCardProps>(({ scene, expanded, onToggle }) => {
  // ...
});
```

**使用 useMemo 缓存计算**:
```typescript
const sortedScenes = useMemo(() => {
  return scenes.sort((a, b) => a.scene_number.localeCompare(b.scene_number));
}, [scenes]);
```

**使用 useCallback 缓存回调**:
```typescript
const handleToggle = useCallback((id: string) => {
  setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
}, []);
```

### 9. 可访问性（Accessibility）

**添加语义化标签**:
```typescript
<button
  aria-label="展开场景"
  title="展开场景"
  onClick={handleToggle}
>
  <ChevronRight />
</button>
```

**键盘导航**:
```typescript
<div
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      handleToggle();
    }
  }}
>
  {/* 内容 */}
</div>
```

### 10. 样式组织

**使用 Tailwind 组合**:
```typescript
// 提取常用样式为常量
const cardStyles = "bg-white rounded-lg shadow-sm border border-slate-200 p-4";
const buttonStyles = "px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600";

<div className={cardStyles}>...</div>
<button className={buttonStyles}>提交</button>
```

**条件样式**:
```typescript
<div className={`
  base-class
  ${active ? "bg-blue-500" : "bg-slate-200"}
  ${disabled && "opacity-50 cursor-not-allowed"}
`}>
  {/* 内容 */}
</div>
```

## 组件示例

### 创建一个新的资产卡片组件

```typescript
// src/components/AssetCard.tsx
import React from "react";
import { Image as ImageIcon } from "lucide-react";

interface AssetCardProps {
  title: string;
  imageUrl: string | null;
  description?: string;
  onClick?: () => void;
}

const AssetCard: React.FC<AssetCardProps> = ({
  title,
  imageUrl,
  description,
  onClick
}) => {
  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {/* 图片区域 */}
      <div className="aspect-square bg-slate-100 flex items-center justify-center">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover"
          />
        ) : (
          <ImageIcon className="w-12 h-12 text-slate-400" />
        )}
      </div>

      {/* 信息区域 */}
      <div className="p-4">
        <h3 className="font-semibold text-slate-800 mb-1">{title}</h3>
        {description && (
          <p className="text-sm text-slate-600 line-clamp-2">{description}</p>
        )}
      </div>
    </div>
  );
};

export default AssetCard;
```

**使用示例**:
```typescript
<AssetCard
  title="角色名称"
  imageUrl="https://example.com/character.jpg"
  description="这是一个角色描述"
  onClick={() => navigate(`/character/${id}`)}
/>
```

## 总结

组件开发要点：
1. **类型安全**: 使用 TypeScript 定义所有 Props 和状态
2. **数据缓存**: 优先从 Store 读取，减少重复请求
3. **请求取消**: 使用 AbortController 避免内存泄漏
4. **错误处理**: 统一的错误展示和恢复机制
5. **性能优化**: 使用 React.memo、useMemo、useCallback
6. **可访问性**: 添加 aria 属性和键盘支持
7. **代码组织**: 组件拆分、逻辑提取、样式复用

---

**相关文档**:
- [项目结构](./project-structure.md)
- [状态管理](./state-management.md)
- [API 集成](./api-integration.md)
- [样式系统](./styling.md)
