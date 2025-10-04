# 资产管理功能文档

本文档说明角色（Characters）、场景（Scenes）、道具（Props）三大资产模块的功能实现，包括列表展示、详情查看、图片生成等。

## 功能概述

资产管理模块提供统一的交互模式：
1. **列表页**：展示所有资产，支持图片预览、筛选和刷新
2. **详情页**：查看资产详细信息、编辑描述、生成图片
3. **异步图片生成**：调用 Jimeng 模型，通过任务队列异步处理
4. **状态管理**：使用 Zustand 缓存数据，避免重复请求

## 资产数据结构

### 角色 (Character)

```typescript
interface Character {
  id: number
  drama_name: string
  episode_number: number
  character_name: string
  image_url: string | null
  image_prompt: string
  is_key_character: boolean  // 关键角色标识
  reflection?: string
}
```

### 场景 (Scene)

```typescript
interface Scene {
  id: number
  drama_name: string
  episode_number: number
  scene_name: string
  image_url: string | null
  image_prompt: string
  is_key_scene: boolean      // 关键场景标识
  scene_brief?: string       // 场景简介
  version?: string
  shots_appeared?: string[]  // 出现的镜头
  reflection?: string
  created_at?: string
}
```

### 道具 (Prop)

```typescript
interface Prop {
  id: number
  drama_name: string
  episode_number: number
  prop_name: string
  image_url: string | null
  image_prompt: string
  reflection?: string
}
```

## 列表页功能

### 1. 角色列表 (Characters.tsx)

**路径**: `/characters`

**主要功能**：
- 卡片式展示所有角色
- 显示角色头像、姓名、剧集信息
- **关键角色标识**：使用琥珀色标签显示 `is_key_character`
- 点击卡片跳转到详情页
- 点击图片全屏预览
- 刷新按钮重新加载数据

**UI 特点**：
- 蓝色-紫色主题
- 卡片尺寸：高度 192px (h-48)
- 悬停效果：边框变蓝色，阴影增强
- 关键角色标签：`bg-amber-100 text-amber-700`

```typescript
{character.is_key_character && (
  <span className="mb-2 inline-block rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-700">
    关键角色
  </span>
)}
```

### 2. 场景列表 (Scenes.tsx)

**路径**: `/scenes`

**主要功能**：
- 卡片式展示所有场景
- 显示场景图片、名称、剧集信息
- **关键场景标识**：使用绿色标签显示 `is_key_scene`
- 点击卡片跳转到详情页
- 点击图片全屏预览
- 刷新按钮重新加载数据

**UI 特点**：
- 绿色-青色主题
- 卡片尺寸：高度 192px (h-48)
- 悬停效果：边框变绿色，阴影增强
- 关键场景标签：`bg-green-100 text-green-700`

```typescript
{scene.is_key_scene && (
  <span className="mb-2 inline-block rounded-full bg-green-100 px-2 py-1 text-xs text-green-700">
    关键场景
  </span>
)}
```

### 3. 道具列表 (Props.tsx)

**路径**: `/props`

**主要功能**：
- 卡片式展示所有道具
- 显示道具图片、名称、剧集信息
- 点击卡片跳转到详情页
- 点击图片全屏预览
- 刷新按钮重新加载数据

**UI 特点**：
- 橙色主题
- 卡片尺寸：高度 192px (h-48)
- 悬停效果：边框变橙色，阴影增强

### 通用交互模式

**图片预览**：
```typescript
const [previewImage, setPreviewImage] = useState<string | null>(null)

const handleImageClick = (e: React.MouseEvent, imageUrl: string) => {
  e.stopPropagation() // 阻止卡片点击事件
  setPreviewImage(imageUrl)
}

// 模态框全屏显示
{previewImage && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-4">
    <img src={previewImage} className="max-h-full max-w-full" />
  </div>
)}
```

**数据缓存**：
```typescript
const { allCharacters, setAllCharacters } = useCharacterStore()

useEffect(() => {
  if (allCharacters) {
    console.debug('Using cached data')
    return
  }
  fetchCharacters()
}, [allCharacters])
```

## 详情页功能

### 1. 角色详情 (CharacterViewer.tsx)

**路径**: `/character/:id`

**布局**：
- 左侧：角色肖像图片（1列）
- 右侧：角色信息（2列）
  - 角色描述（可编辑，400px 高度）
  - Reflection（只读，276px 高度）

**主要功能**：

#### 查看模式
- 显示角色名称、剧集信息
- 显示角色描述 (`image_prompt`)
- 显示 Reflection（创作提示）
- **生成图片按钮**：渐变按钮 `from-purple-500 to-pink-500`
- **编辑按钮**：进入编辑模式

#### 编辑模式
- 使用 textarea 编辑角色描述
- **保存按钮**：保存到数据库
- **取消按钮**：恢复原内容

#### 图片生成
- 点击"生成图片"按钮提交异步任务
- 显示生成状态（提交任务中 → 排队中 → 生成中 → 完成）
- 轮询间隔：3 秒
- 成功后更新图片 URL 和描述
- 失败时显示错误信息

### 2. 场景详情 (SceneViewer.tsx)

**路径**: `/scene/:id`

**布局**：
- 左侧：场景图片（1列，sticky 固定）
- 右侧：场景信息（2列）
  - 场景信息卡片（场景简介、版本、镜头列表）
  - 场景描述（可编辑，400px 高度）
  - Reflection（只读，276px 高度）

**主要功能**：

#### 场景信息展示
- 场景名称、剧集信息
- **关键场景标识**：带星标图标的琥珀色标签
- 场景简介 (`scene_brief`)
- 版本信息 (`version`)
- 出现镜头列表 (`shots_appeared`)
- 创建时间 (`created_at`)

#### 编辑和生成
- 与角色详情相同的编辑模式
- **生成图片按钮**：渐变按钮 `from-green-500 to-teal-500`
- 相同的异步图片生成流程

### 3. 道具详情 (PropViewer.tsx)

**路径**: `/prop/:id`

**布局和功能**：
- 与角色详情类似
- 橙色主题按钮

### 通用异步图片生成流程

**状态管理**：
```typescript
const [generating, setGenerating] = useState<boolean>(false)
const [generationStatus, setGenerationStatus] = useState<string>('')
const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
```

**生成流程**：

1. **提交任务**
   ```typescript
   const taskResult = await characterService.submitCharacterTask(id, promptToUse)
   setGenerationStatus('排队中...')
   ```

2. **轮询状态**（每 3 秒）
   ```typescript
   const pollInterval = 3000
   pollingIntervalRef.current = setInterval(async () => {
     const status = await characterService.getCharacterTaskStatus(id, taskId)

     if (status.status === 'QUEUED') {
       setGenerationStatus('排队中...')
     } else if (status.status === 'RUNNING') {
       setGenerationStatus('生成中...')
     } else if (status.status === 'SUCCESS') {
       // 更新图片 URL
       updateCharacter(Number(id), {
         image_url: status.image_url!,
         image_prompt: promptToUse
       })
       setGenerating(false)
     } else if (status.status === 'FAIL' || status.status === 'CANCEL') {
       alert(`生成失败: ${status.error || '未知错误'}`)
       setGenerating(false)
     }
   }, pollInterval)
   ```

3. **清理定时器**
   ```typescript
   useEffect(() => {
     return () => {
       if (pollingIntervalRef.current) {
         clearInterval(pollingIntervalRef.current)
       }
     }
   }, [])
   ```

## API 端点设计

### 角色 API (Character)

```typescript
// 列表
getAllCharacters: () => `${API_BASE_URL}/api/characters/all`
getCharacters: (key: string) => `${API_BASE_URL}/api/characters/${key}`

// 详情
getCharacter: (id) => `${API_BASE_URL}/api/character/${id}`

// 编辑
updateCharacterPrompt: (id) => `${API_BASE_URL}/api/character/${id}/prompt`

// 图片生成
submitCharacterTask: (id) => `${API_BASE_URL}/api/character/${id}/submit-task`
getCharacterTaskStatus: (id, taskId) =>
  `${API_BASE_URL}/api/character/${id}/task-status/${taskId}`
```

### 场景 API (Scene)

```typescript
// 列表
getAllScenes: () => `${API_BASE_URL}/api/scenes/all`
getScenes: (key: string) => `${API_BASE_URL}/api/scenes/${key}`

// 详情
getScene: (id) => `${API_BASE_URL}/api/scene/${id}`

// 编辑
updateScenePrompt: (id) => `${API_BASE_URL}/api/scene/${id}/prompt`

// 图片生成
submitSceneTask: (id) => `${API_BASE_URL}/api/scene/${id}/submit-task`
getSceneTaskStatus: (id, taskId) =>
  `${API_BASE_URL}/api/scene/${id}/task-status/${taskId}`
```

### 道具 API (Prop)

```typescript
// 列表
getAllProps: () => `${API_BASE_URL}/api/props/all`

// 详情
getProp: (id) => `${API_BASE_URL}/api/prop/${id}`

// 编辑
updatePropPrompt: (id) => `${API_BASE_URL}/api/prop/${id}/prompt`

// 图片生成
submitPropTask: (id) => `${API_BASE_URL}/api/prop/${id}/submit-task`
getPropTaskStatus: (id, taskId) =>
  `${API_BASE_URL}/api/prop/${id}/task-status/${taskId}`
```

### API 一致性设计

所有资产 API 遵循相同的命名规范：
- `getAll{Asset}s()`: 获取所有资产
- `get{Asset}(id)`: 获取单个资产详情
- `update{Asset}Prompt(id)`: 更新描述
- `submit{Asset}Task(id)`: 提交异步生成任务
- `get{Asset}TaskStatus(id, taskId)`: 查询任务状态

**重要说明**：
- **CDN URL 转换**：所有 API 返回的 `image_url` 已经是完整的 CDN URL（通过后端 `to_cdn_url()` 转换）
- **关键标识字段**：列表 API 包含关键标识字段：
  - 角色：`is_key_character`
  - 场景：`is_key_scene`
  - 道具：`is_key_prop`

## 服务层 (Service Layer)

### characterService.ts

```typescript
export const characterService = {
  async getAllCharacters(signal?: AbortSignal): Promise<CharactersResponse>
  async getCharacters(key: string, signal?: AbortSignal): Promise<CharactersResponse>
  async getCharacter(id: string | number, signal?: AbortSignal): Promise<Character>
  async updateCharacterPrompt(id, imagePrompt, signal?): Promise<{ character_id: number }>
  async submitCharacterTask(id, imagePrompt, signal?): Promise<{ task_id: string; status: string }>
  async getCharacterTaskStatus(id, taskId, signal?): Promise<TaskStatusResponse>
}
```

### sceneService.ts

```typescript
export const sceneService = {
  async getAllScenes(signal?: AbortSignal): Promise<ScenesResponse>
  async getScenes(key: string, signal?: AbortSignal): Promise<ScenesResponse>
  async getScene(id: string | number, signal?: AbortSignal): Promise<Scene>
  async updateScenePrompt(id, imagePrompt, signal?): Promise<{ scene_id: number }>
  async submitSceneTask(id, imagePrompt, signal?): Promise<{ task_id: string; status: string }>
  async getSceneTaskStatus(id, taskId, signal?): Promise<TaskStatusResponse>
}
```

### propService.ts

```typescript
export const propService = {
  async getAllProps(signal?: AbortSignal): Promise<PropsResponse>
  async getProp(id: string | number, signal?: AbortSignal): Promise<Prop>
  async updatePropPrompt(id, imagePrompt, signal?): Promise<{ prop_id: number }>
  async submitPropTask(id, imagePrompt, signal?): Promise<{ task_id: string; status: string }>
  async getPropTaskStatus(id, taskId, signal?): Promise<TaskStatusResponse>
}
```

### 任务状态响应类型

```typescript
interface TaskStatusResponse {
  status: 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAIL' | 'CANCEL' | 'UNKNOWN'
  image_url?: string
  error?: string
}
```

## 状态管理 (Zustand Stores)

### useCharacterStore.ts

```typescript
interface CharacterStore {
  currentCharacter: Character | null
  setCurrentCharacter: (character: Character) => void

  allCharacters: Character[] | null
  setAllCharacters: (data: Character[]) => void

  updateCharacter: (id: number, updates: Partial<Character>) => void
  clearAll: () => void
}
```

### useSceneStore.ts

```typescript
interface SceneStore {
  currentScene: Scene | null
  setCurrentScene: (scene: Scene) => void

  allScenes: Scene[] | null
  setAllScenes: (data: Scene[]) => void

  updateScene: (id: number, updates: Partial<Scene>) => void
  clearAll: () => void
}
```

### usePropStore.ts

```typescript
interface PropStore {
  currentProp: Prop | null
  setCurrentProp: (prop: Prop) => void

  allProps: Prop[] | null
  setAllProps: (data: Prop[]) => void

  updateProp: (id: number, updates: Partial<Prop>) => void
  clearAll: () => void
}
```

### updateAsset 方法实现

所有 Store 都实现了 `update{Asset}` 方法，用于部分更新：

```typescript
updateCharacter: (id, updates) => {
  set((state) => ({
    allCharacters: state.allCharacters
      ? state.allCharacters.map((c) => (c.id === id ? { ...c, ...updates } : c))
      : null,
    currentCharacter:
      state.currentCharacter && state.currentCharacter.id === id
        ? { ...state.currentCharacter, ...updates }
        : state.currentCharacter
  }))
}
```

**使用场景**：
- 图片生成成功后更新 `image_url`
- 编辑描述后更新 `image_prompt`

**示例**：
```typescript
updateCharacter(Number(id), {
  image_url: status.image_url!,
  image_prompt: promptToUse
})
```

## UI 设计规范

### 主题配色

| 资产   | 主题色           | 渐变色                                    | 按钮色               |
| ------ | ---------------- | ----------------------------------------- | -------------------- |
| 角色   | 蓝色-紫色        | `from-blue-500 to-purple-500`             | `from-purple-500 to-pink-500` (生成) |
| 场景   | 绿色-青色        | `from-green-500 to-teal-500`              | `from-green-500 to-teal-500` (生成)  |
| 道具   | 橙色             | `from-orange-500 to-red-500`              | `from-orange-500 to-red-500` (生成)  |

### 卡片设计

**共同特点**：
- 圆角：`rounded-xl`
- 边框：`border border-slate-200`
- 悬停边框：主题色 `border-{color}-400`
- 悬停阴影：`hover:shadow-xl`
- 图片高度：`h-48` (192px)
- 过渡动画：`transition-all duration-300`

**图片悬停效果**：
```typescript
<div className="relative h-48 w-full overflow-hidden">
  <img className="transition-transform duration-300 group-hover:scale-110" />
  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10">
    <Search className="opacity-0 group-hover:opacity-80" />
  </div>
</div>
```

### 详情页布局

**响应式网格**：
```typescript
<div className="grid items-start gap-6 lg:grid-cols-3">
  <div className="lg:col-span-1">  {/* 图片 */}
  <div className="lg:col-span-2">  {/* 信息 */}
</div>
```

**场景特殊布局**（Sticky 固定）：
```typescript
<div className="lg:sticky lg:top-6 lg:col-span-1">
  <ImageDisplay />
</div>
```

### 按钮状态

**生成按钮**：
```typescript
<button
  disabled={generating}
  className="flex items-center space-x-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 text-white shadow-md transition-all duration-200 hover:from-purple-600 hover:to-pink-600 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
>
  <Wand2 className="h-4 w-4" />
  <span>{generating ? generationStatus : '生成图片'}</span>
</button>
```

**编辑按钮**：
```typescript
<button className="flex items-center space-x-2 rounded-lg bg-blue-50 px-4 py-2 text-blue-700 transition-colors duration-200 hover:bg-blue-100">
  <Edit className="h-4 w-4" />
  <span>编辑</span>
</button>
```

## 异步图片生成后端架构

详细架构请参考 [异步图片生成文档](../dev/async-image-generation.md)。

### 核心组件

1. **ai_tasks 表**：存储任务状态
2. **TaskProcessor**：后台处理器，轮询任务队列
3. **JimengT2IRH**：调用 RunningHub API
4. **AITaskManager**：任务管理工具类

### 任务流程

```
前端提交任务
    ↓
创建 ai_tasks 记录 (PENDING)
    ↓
TaskProcessor 轮询
    ↓
提交到 RunningHub (SUBMITTED)
    ↓
轮询 RunningHub 状态 (QUEUED → RUNNING)
    ↓
下载图片 → 上传 R2 → 更新数据库 (SUCCESS)
    ↓
前端轮询获取结果
```

### 状态流转

```
PENDING → SUBMITTED → QUEUED → RUNNING → SUCCESS
   ↓          ↓          ↓         ↓
FAILED ← ─────┴──────────┴─────────┘
   ↓
TIMEOUT (超过30分钟)
   ↓
重试 (retry_count < max_retries)
```

## 最佳实践

### 1. 错误处理

**提交任务失败**：
```typescript
try {
  const taskResult = await characterService.submitCharacterTask(id, promptToUse)
} catch (err) {
  console.error('Error submitting task:', err)
  alert('提交任务失败，请检查网络或稍后重试。')
  setGenerating(false)
}
```

**轮询失败**：
```typescript
try {
  const status = await characterService.getCharacterTaskStatus(id, taskId)
} catch (pollErr) {
  console.error('Error polling status:', pollErr)
  // 不中断轮询，避免网络抖动影响
}
```

**任务失败**：
```typescript
if (status.status === 'FAIL' || status.status === 'CANCEL') {
  clearInterval(pollingIntervalRef.current)
  alert(`生成失败: ${status.error || '未知错误'}`)
  setGenerating(false)
}
```

### 2. 性能优化

**缓存策略**：
```typescript
// 使用 Zustand store 缓存列表数据
const { allCharacters, setAllCharacters } = useCharacterStore()

useEffect(() => {
  if (allCharacters) {
    console.debug('Using cached data')
    return
  }
  fetchCharacters()
}, [allCharacters])
```

**请求去重**：
```typescript
// apiCall 自动去重并发请求
const data1 = await apiCall(API_ENDPOINTS.getCharacter(id))
const data2 = await apiCall(API_ENDPOINTS.getCharacter(id)) // 复用上面的请求
```

**轮询间隔**：
- 3 秒间隔：平衡实时性和服务器压力
- 避免频繁请求造成性能问题

### 3. 用户体验

**生成状态反馈**：
- 提交任务中...
- 排队中...
- 生成中...
- 完成！

**防止重复提交**：
```typescript
<button disabled={generating}>
  {generating ? generationStatus : '生成图片'}
</button>
```

**编辑保护**：
```typescript
const handleCancelEdit = () => {
  setIsEditingPrompt(false)
  setEditedPrompt(characterData?.image_prompt || '')
}
```

**内存泄漏防护**：
```typescript
useEffect(() => {
  return () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }
  }
}, [])
```

## 一致性设计总结

### 三大资产的共同点

| 功能       | 角色 | 场景 | 道具 |
| ---------- | ---- | ---- | ---- |
| 列表展示   | ✅   | ✅   | ✅   |
| 图片预览   | ✅   | ✅   | ✅   |
| 详情查看   | ✅   | ✅   | ✅   |
| 编辑描述   | ✅   | ✅   | ✅   |
| 异步生成   | ✅   | ✅   | ✅   |
| 状态缓存   | ✅   | ✅   | ✅   |
| API 一致性 | ✅   | ✅   | ✅   |

### 差异化设计

| 特性           | 角色                 | 场景                           | 道具       |
| -------------- | -------------------- | ------------------------------ | ---------- |
| 主题色         | 蓝色-紫色            | 绿色-青色                      | 橙色       |
| 关键标识       | `is_key_character`   | `is_key_scene`                 | 无         |
| 特有字段       | 无                   | `scene_brief`, `shots_appeared` | 无         |
| 详情页布局     | 普通                 | Sticky 固定图片                | 普通       |
| 生成按钮渐变   | purple-500 to pink-500 | green-500 to teal-500          | orange-500 to red-500 |

## 后续优化建议

### 功能增强
1. **批量操作**：支持批量生成图片
2. **图片版本管理**：支持查看历史生成的图片
3. **图片编辑**：集成 img2img 功能，支持图片微调
4. **预设模板**：提供常见描述模板
5. **AI 辅助**：使用 LLM 优化描述文本

### 性能优化
1. **虚拟滚动**：列表页数据量大时使用虚拟滚动
2. **图片懒加载**：列表页图片懒加载
3. **分页加载**：支持分页或无限滚动
4. **WebSocket**：实时推送生成结果，替代轮询

### 用户体验
1. **进度条**：显示图片生成的具体进度
2. **批量生成队列**：支持队列管理
3. **快捷键**：支持键盘快捷键操作
4. **搜索过滤**：支持按名称、剧集搜索

## 相关文档

- [异步图片生成架构](../dev/async-image-generation.md) - 后端任务处理架构
- [API 集成指南](./api-integration.md) - API 客户端和服务层
- [状态管理](./state-management.md) - Zustand store 设计
- [组件设计](./components.md) - 组件分类和使用
- [项目结构](./project-structure.md) - 目录组织

---

**最后更新**: 2025-10-05
**文档版本**: 1.0.0
