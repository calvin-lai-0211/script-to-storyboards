# 状态管理（Zustand）

本文档详细说明项目中的 Zustand 状态管理设计、使用方法和最佳实践。

## Zustand 简介

Zustand 是一个轻量级的 React 状态管理库，具有以下优势：

- **简洁 API**: 比 Redux 简单得多，没有 boilerplate
- **性能优越**: 使用 React.useSyncExternalStore 优化
- **TypeScript 友好**: 完整的类型推导
- **无需 Context Provider**: 直接导入使用
- **体积小**: 仅 ~1KB（gzipped）

**官方文档**: https://docs.pmnd.rs/zustand/getting-started/introduction

## Store 列表

项目中按业务模块划分了 6 个 Store：

| Store | 文件 | 职责 |
|-------|------|------|
| **useEpisodeStore** | `store/useEpisodeStore.ts` | 剧集上下文、剧本、分镜、Memory 缓存 |
| **useCharacterStore** | `store/useCharacterStore.ts` | 角色数据缓存 |
| **useSceneStore** | `store/useSceneStore.ts` | 场景数据缓存 |
| **usePropStore** | `store/usePropStore.ts` | 道具数据缓存 |
| **useStoryboardStore** | `store/useStoryboardStore.ts` | 分镜数据缓存（独立） |
| **useMemoryStore** | `store/useMemoryStore.ts` | Memory 数据缓存（独立） |

## Store 详解

### useEpisodeStore - 剧集 Store

**职责**: 管理当前剧集上下文和所有剧集列表缓存。

**数据结构**:
```typescript
interface EpisodeStore {
  // 当前剧集上下文
  currentEpisode: Partial<EpisodeData> | null;
  setCurrentEpisode: (episode: Partial<EpisodeData>) => void;

  // 数据缓存（按 key 索引）
  episodes: Record<string, EpisodeData>;
  storyboards: Record<string, StoryboardData>;
  memories: Record<string, MemoryData>;

  // 全局列表缓存
  allEpisodes: ScriptData[] | null;

  // Actions
  setEpisode: (key: string, data: EpisodeData) => void;
  setStoryboard: (key: string, data: StoryboardData) => void;
  setMemory: (key: string, data: MemoryData) => void;
  setAllEpisodes: (data: ScriptData[]) => void;

  getEpisode: (key: string) => EpisodeData | undefined;
  getStoryboard: (key: string) => StoryboardData | undefined;
  getMemory: (key: string) => MemoryData | undefined;

  clearKey: (key: string) => void;
  clearAll: () => void;
}
```

**实现细节**:
```typescript
export const useEpisodeStore = create<EpisodeStore>((set, get) => ({
  currentEpisode: null,

  setCurrentEpisode: (episode) => {
    set({ currentEpisode: episode });
  },

  episodes: {},
  storyboards: {},
  memories: {},
  allEpisodes: null,

  setEpisode: (key, data) => {
    set((state) => ({
      episodes: { ...state.episodes, [key]: data },
    }));
  },

  setStoryboard: (key, data) => {
    set((state) => ({
      storyboards: { ...state.storyboards, [key]: data },
    }));
  },

  setMemory: (key, data) => {
    set((state) => ({
      memories: { ...state.memories, [key]: data },
    }));
  },

  setAllEpisodes: (data) => {
    set({ allEpisodes: data });
  },

  getEpisode: (key) => {
    return get().episodes[key];
  },

  getStoryboard: (key) => {
    return get().storyboards[key];
  },

  getMemory: (key) => {
    return get().memories[key];
  },

  clearKey: (key) => {
    set((state) => {
      const newState = { ...state };
      delete newState.episodes[key];
      delete newState.storyboards[key];
      delete newState.memories[key];
      return newState;
    });
  },

  clearAll: () => {
    set({
      currentEpisode: null,
      episodes: {},
      storyboards: {},
      memories: {},
      allEpisodes: null,
    });
  },
}));
```

**使用示例**:

1. **设置当前剧集**:
```typescript
import { useEpisodeStore } from "@store/useEpisodeStore";

const { setCurrentEpisode } = useEpisodeStore();

// 从列表页点击剧集时
const handleScriptClick = (script: ScriptData) => {
  setCurrentEpisode({
    key: script.key,
    drama_name: script.drama_name,
    episode_number: script.episode_number,
  });
  navigate(`/episode/${script.key}`);
};
```

2. **获取当前剧集**:
```typescript
const { currentEpisode } = useEpisodeStore();

return (
  <h1>{currentEpisode?.drama_name} - 第 {currentEpisode?.episode_number} 集</h1>
);
```

3. **缓存分镜数据**:
```typescript
const { setStoryboard, getStoryboard } = useEpisodeStore();

// 获取数据后缓存
const data = await apiCall(API_ENDPOINTS.getStoryboards(key));
setStoryboard(key, data);

// 下次直接从缓存读取
const cached = getStoryboard(key);
if (cached) {
  setScenes(cached);
  return;
}
```

4. **清理缓存**:
```typescript
const { clearKey, clearAll } = useEpisodeStore();

// 清理单个剧集的缓存
clearKey("da4ef19d-5965-41c3-a971-f17d0ce06ef7");

// 清理所有缓存（退出登录时）
clearAll();
```

---

### useCharacterStore - 角色 Store

**职责**: 缓存所有角色数据。

**数据结构**:
```typescript
interface CharacterStore {
  characters: Character[] | null;
  characterById: Record<number, Character>;

  setCharacters: (data: Character[]) => void;
  setCharacter: (id: number, data: Character) => void;
  getCharacter: (id: number) => Character | undefined;
  clearCharacters: () => void;
}
```

**使用示例**:
```typescript
const { characters, setCharacters } = useCharacterStore();

// 获取所有角色
const data = await apiCall(API_ENDPOINTS.getAllCharacters());
setCharacters(data.characters);

// 在列表中使用
{characters?.map(char => (
  <CharacterCard key={char.id} character={char} />
))}
```

---

### useSceneStore - 场景 Store

**职责**: 缓存所有场景数据。

**数据结构**:
```typescript
interface SceneStore {
  scenes: Scene[] | null;
  sceneById: Record<number, Scene>;

  setScenes: (data: Scene[]) => void;
  setScene: (id: number, data: Scene) => void;
  getScene: (id: number) => Scene | undefined;
  clearScenes: () => void;
}
```

---

### usePropStore - 道具 Store

**职责**: 缓存所有道具数据。

**数据结构**:
```typescript
interface PropStore {
  props: Prop[] | null;
  propById: Record<number, Prop>;

  setProps: (data: Prop[]) => void;
  setProp: (id: number, data: Prop) => void;
  getProp: (id: number) => Prop | undefined;
  clearProps: () => void;
}
```

---

### useStoryboardStore - 分镜 Store

**职责**: 独立缓存分镜数据（与 useEpisodeStore 分离）。

**数据结构**:
```typescript
interface StoryboardStore {
  storyboards: Record<string, Scene[]>;

  setStoryboard: (key: string, data: Scene[]) => void;
  getStoryboard: (key: string) => Scene[] | undefined;
  clearStoryboard: (key: string) => void;
  clearAll: () => void;
}
```

**使用示例**:
```typescript
const { getStoryboard, setStoryboard } = useStoryboardStore();

// 检查缓存
const cached = getStoryboard(scriptKey);
if (cached) {
  setScenes(cached);
  return;
}

// 获取数据后缓存
const data = await fetchStoryboards();
setStoryboard(scriptKey, data);
```

---

### useMemoryStore - Memory Store

**职责**: 独立缓存 Memory 数据。

**数据结构**:
```typescript
interface MemoryStore {
  memories: Record<string, MemoryData>;

  setMemory: (key: string, data: MemoryData) => void;
  getMemory: (key: string) => MemoryData | undefined;
  clearMemory: (key: string) => void;
  clearAll: () => void;
}
```

---

## 双重缓存策略

项目使用了两层缓存机制，互相配合：

### 1. RequestDeduplicator（请求去重层）

**职责**: 防止并发的相同请求。

**生命周期**: 临时缓存，请求完成即清除。

**工作原理**:
```typescript
// 第一个请求发起
const request1 = apiCall(url);

// 第二个相同请求会等待第一个请求完成
const request2 = apiCall(url);  // 不会发起新请求，而是复用 request1

// 请求完成后，缓存立即清除
```

### 2. Zustand Store（数据缓存层）

**职责**: 缓存响应数据，跨组件共享。

**生命周期**: 持久缓存，直到用户刷新页面或手动清除。

**工作原理**:
```typescript
// 第一次请求：从 API 获取
const data = await apiCall(url);
setStoryboard(key, data);  // 缓存到 Store

// 第二次请求：直接从 Store 读取
const cached = getStoryboard(key);
if (cached) {
  return cached;  // 不发起网络请求
}
```

### 协同工作流程

```
组件 A 请求 → RequestDeduplicator → 发起 HTTP 请求
                      ↓
                  响应返回
                      ↓
              Store 缓存数据
                      ↓
             RequestDeduplicator 清除

组件 B 请求 → Store 缓存 → 直接返回（无网络请求）
```

**完整示例**:
```typescript
useEffect(() => {
  // 1. 先检查 Store 缓存
  const cached = getStoryboard(scriptKey);
  if (cached) {
    console.debug("Using cached storyboard");
    setScenes(cached);
    return;
  }

  // 2. 无缓存时请求（RequestDeduplicator 自动去重）
  const abortController = new AbortController();

  const fetchData = async () => {
    try {
      const data = await apiCall(API_ENDPOINTS.getStoryboards(scriptKey));

      // 3. 缓存到 Store
      setStoryboard(scriptKey, data);
      setScenes(data);
    } catch (err) {
      console.error("Error:", err);
    }
  };

  fetchData();

  // 4. 清理：取消请求
  return () => {
    abortController.abort();
  };
}, [scriptKey, getStoryboard]);
```

---

## 状态管理最佳实践

### 1. 选择器（Selector）模式

只订阅需要的状态，避免不必要的重新渲染：

```typescript
// ❌ 不推荐：订阅整个 store
const store = useEpisodeStore();

// ✅ 推荐：只订阅需要的字段
const currentEpisode = useEpisodeStore(state => state.currentEpisode);
const setCurrentEpisode = useEpisodeStore(state => state.setCurrentEpisode);
```

### 2. 避免在 Setter 中直接修改状态

```typescript
// ❌ 错误：直接修改
set((state) => {
  state.episodes[key] = data;  // 不会触发更新
  return state;
});

// ✅ 正确：创建新对象
set((state) => ({
  episodes: { ...state.episodes, [key]: data },
}));
```

### 3. 使用 get() 访问最新状态

在 action 中访问其他状态时，使用 `get()` 而非闭包：

```typescript
// ❌ 不推荐：使用闭包（可能获取到陈旧状态）
const episodes = {}; // 闭包捕获

setEpisode: (key, data) => {
  const current = episodes[key];  // 可能是旧值
  // ...
};

// ✅ 推荐：使用 get() 获取最新状态
setEpisode: (key, data) => {
  const current = get().episodes[key];  // 最新值
  // ...
};
```

### 4. useEffect 依赖数组必须包含 Getter

**重要**: Zustand store 的 getter 函数会在 store 更新时变化，必须放在依赖数组中。

```typescript
// ❌ 错误：缺少 getStoryboard 依赖
useEffect(() => {
  const cached = getStoryboard(scriptKey);
  if (cached) return;
  fetchData();
}, [scriptKey]);  // 缺少 getStoryboard

// ✅ 正确：包含所有依赖
useEffect(() => {
  const cached = getStoryboard(scriptKey);
  if (cached) return;
  fetchData();
}, [scriptKey, getStoryboard]);  // 完整依赖
```

**原因**: 如果不包含 getter，useEffect 会使用陈旧闭包，导致缓存失效。

### 5. 批量更新

使用单个 `set` 调用更新多个字段：

```typescript
// ❌ 不推荐：多次 set
setCurrentEpisode(episode);
setAllEpisodes(data);

// ✅ 推荐：单次 set
set({
  currentEpisode: episode,
  allEpisodes: data,
});
```

### 6. 清理缓存

在适当的时机清理缓存：

```typescript
// 用户退出登录时
const handleLogout = () => {
  useEpisodeStore.getState().clearAll();
  useCharacterStore.getState().clearCharacters();
  useSceneStore.getState().clearScenes();
  usePropStore.getState().clearProps();
  useStoryboardStore.getState().clearAll();
  useMemoryStore.getState().clearAll();
};

// 单个剧集数据过期时
const handleRefresh = () => {
  clearKey(scriptKey);
  fetchData();
};
```

### 7. DevTools 集成

在开发环境中启用 Zustand DevTools：

```typescript
import { create } from "zustand";
import { devtools } from "zustand/middleware";

export const useEpisodeStore = create(
  devtools(
    (set, get) => ({
      // store 定义
    }),
    { name: "EpisodeStore" }  // DevTools 中显示的名称
  )
);
```

**使用**: 打开 React DevTools → Components → 选择组件 → 查看 Zustand 状态。

### 8. 持久化存储（可选）

如果需要在刷新页面后保留数据，可以使用 persist 中间件：

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export const useEpisodeStore = create(
  persist(
    (set, get) => ({
      // store 定义
    }),
    {
      name: "episode-storage",  // localStorage key
      storage: createJSONStorage(() => localStorage),
    }
  )
);
```

**注意**: 项目当前未使用持久化，因为数据从 API 获取且会更新。

---

## 类型定义

### 通用类型（store/types.ts）

```typescript
// 剧集数据
export interface EpisodeData {
  key: string;
  drama_name: string;
  episode_number: number;
  script: string;
  created_at: string;
  updated_at: string;
}

// 剧本列表
export interface ScriptData {
  key: string;
  drama_name: string;
  episode_number: number;
  created_at: string;
  updated_at: string;
}

// 分镜数据
export interface StoryboardData {
  storyboards: Array<{
    id: number;
    scene_number: string;
    scene_description: string;
    shot_number: string;
    shot_description: string;
    sub_shot_number: string;
    camera_angle: string;
    characters: string[];
    scene_context: string[];
    key_props: string[];
    image_prompt: string;
    dialogue_sound: string;
    duration_seconds: number;
    notes: string;
  }>;
}

// Memory 数据
export interface MemoryData {
  memory: string;
  created_at: string;
  updated_at: string;
}
```

---

## 测试

### 单元测试示例

```typescript
// store/__tests__/useEpisodeStore.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { useEpisodeStore } from "../useEpisodeStore";

describe("useEpisodeStore", () => {
  beforeEach(() => {
    useEpisodeStore.getState().clearAll();
  });

  it("should set current episode", () => {
    const { setCurrentEpisode } = useEpisodeStore.getState();

    setCurrentEpisode({
      key: "test-key",
      drama_name: "测试剧本",
      episode_number: 1,
    });

    const { currentEpisode } = useEpisodeStore.getState();
    expect(currentEpisode).toEqual({
      key: "test-key",
      drama_name: "测试剧本",
      episode_number: 1,
    });
  });

  it("should cache and retrieve episode data", () => {
    const { setEpisode, getEpisode } = useEpisodeStore.getState();

    const testData = {
      key: "test-key",
      drama_name: "测试剧本",
      episode_number: 1,
      script: "剧本内容",
      created_at: "2025-10-04",
      updated_at: "2025-10-04",
    };

    setEpisode("test-key", testData);

    const cached = getEpisode("test-key");
    expect(cached).toEqual(testData);
  });

  it("should clear all caches", () => {
    const { setEpisode, clearAll, getEpisode } = useEpisodeStore.getState();

    setEpisode("key1", { /* ... */ });
    setEpisode("key2", { /* ... */ });

    clearAll();

    expect(getEpisode("key1")).toBeUndefined();
    expect(getEpisode("key2")).toBeUndefined();
  });
});
```

---

## 总结

Zustand 状态管理要点：
1. **按业务模块分离 Store**: 避免单个 Store 过大
2. **双重缓存策略**: RequestDeduplicator + Zustand Store
3. **使用选择器**: 只订阅需要的状态
4. **完整的依赖数组**: useEffect 必须包含 getter 函数
5. **类型安全**: 所有 Store 都有 TypeScript 类型定义
6. **测试覆盖**: 核心 Store 都有单元测试
7. **DevTools 支持**: 开发环境启用调试工具

---

**相关文档**:
- [架构设计](./architecture.md)
- [API 集成](./api-integration.md)
- [组件开发](./components.md)
- [测试指南](./testing.md)
