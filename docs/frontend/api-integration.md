# API 集成

本文档详细说明项目的 API 集成架构、Service 层设计、请求去重机制和最佳实践。

## API 层架构

采用分层架构，将 API 相关逻辑集中管理：

```
组件层 (Pages/Components)
     ↓
服务层 (Services)
     ↓
客户端层 (Client)
     ↓
请求去重层 (RequestDeduplicator)
     ↓
后端 API
```

### 目录结构

```
src/api/
├── client.ts                 # API 客户端（fetch 封装）
├── endpoints.ts              # API 端点定义
├── requestDeduplicator.ts    # 请求去重管理器
├── types/                    # 类型定义
│   ├── character.ts
│   ├── scene.ts
│   ├── prop.ts
│   ├── script.ts
│   ├── storyboard.ts
│   ├── memory.ts
│   └── index.ts
├── services/                 # 服务层
│   ├── characterService.ts
│   ├── sceneService.ts
│   ├── propService.ts
│   ├── scriptService.ts
│   ├── storyboardService.ts
│   ├── memoryService.ts
│   └── index.ts
├── __tests__/                # 测试
│   ├── client.test.ts
│   ├── endpoints.test.ts
│   └── requestDeduplicator.test.ts
└── index.ts                  # 统一导出
```

---

## 核心模块

### 1. Client 层（client.ts）

**职责**: 封装 `fetch` 请求，提供统一的错误处理和认证跳转。

**核心代码**:
```typescript
import type { ApiResponse } from "./types";
import { requestDeduplicator } from "./requestDeduplicator";

// API Base URL
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Helper function for API calls with automatic request deduplication
export const apiCall = async <T = unknown>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  return requestDeduplicator.deduplicate(url, options, async () => {
    console.debug("API call:", url);

    const response = await fetch(url, {
      ...options,
      credentials: "include",  // 允许跨域发送和接收 cookie
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    const result: ApiResponse<T> = await response.json();

    // Check if API returned error (code !== 0)
    if (result.code !== 0) {
      // Handle authentication error (code 4003)
      if (result.code === 4003) {
        const authUrl = (result.data as any)?.auth_url;
        if (authUrl) {
          console.debug("Not authenticated, redirecting to login:", authUrl);
          window.location.href = authUrl;
          throw new Error(result.message || "未登录，正在跳转到登录页");
        }
      }

      throw new Error(result.message || `API error! code: ${result.code}`);
    }

    // Return the data field
    return result.data as T;
  });
};
```

**特性**:
1. **环境变量配置**: 支持通过 `VITE_API_BASE_URL` 配置 API 地址
2. **自动去重**: 集成 `requestDeduplicator`
3. **跨域支持**: `credentials: "include"` 允许发送 cookie
4. **错误处理**: 检查 `code !== 0` 并抛出错误
5. **认证跳转**: 检测 4003 错误码，自动跳转到登录页
6. **调试日志**: 使用 `console.debug` 记录请求

---

### 2. Endpoints 层（endpoints.ts）

**职责**: 集中管理所有 API 端点，支持动态参数。

**核心代码**:
```typescript
import { API_BASE_URL } from "./client";

export const API_ENDPOINTS = {
  // Scripts endpoints
  getAllScripts: () => `${API_BASE_URL}/api/scripts`,
  getScript: (key: string) =>
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(key)}`,

  // Storyboards endpoints
  getStoryboards: (key: string) =>
    `${API_BASE_URL}/api/storyboards/${encodeURIComponent(key)}`,

  // Characters endpoints
  getAllCharacters: () => `${API_BASE_URL}/api/characters/all`,
  getCharacter: (id: string | number) => `${API_BASE_URL}/api/character/${id}`,
  getCharacters: (key: string) =>
    `${API_BASE_URL}/api/characters/${encodeURIComponent(key)}`,
  generateCharacters: () => `${API_BASE_URL}/api/characters/generate`,
  updateCharacterPrompt: (id: string | number) =>
    `${API_BASE_URL}/api/character/${id}/prompt`,
  generateCharacterImage: (id: string | number) =>
    `${API_BASE_URL}/api/character/${id}/generate-image`,

  // Scenes endpoints
  getAllScenes: () => `${API_BASE_URL}/api/scenes/all`,
  getScene: (id: string | number) => `${API_BASE_URL}/api/scene/${id}`,
  getScenes: (key: string) =>
    `${API_BASE_URL}/api/scenes/${encodeURIComponent(key)}`,
  generateScenes: () => `${API_BASE_URL}/api/scenes/generate`,

  // Props endpoints
  getAllProps: () => `${API_BASE_URL}/api/props/all`,
  getProp: (id: string | number) => `${API_BASE_URL}/api/prop/${id}`,
  generateProps: () => `${API_BASE_URL}/api/props/generate`,

  // Memory endpoints
  getEpisodeMemory: (key: string) =>
    `${API_BASE_URL}/api/memory/${encodeURIComponent(key)}`,

  // Storyboard generation
  generateStoryboard: () => `${API_BASE_URL}/api/storyboard/generate`,
};
```

**特性**:
1. **URL 编码**: 使用 `encodeURIComponent` 处理特殊字符
2. **类型安全**: 参数类型明确（`string | number`）
3. **集中管理**: 所有端点在一个文件中维护
4. **易于修改**: 修改端点时只需改一处

---

### 3. RequestDeduplicator 层（requestDeduplicator.ts）

**职责**: 防止并发的相同请求，自动合并重复请求。

**工作原理**:

1. **请求去重**: 当一个请求正在进行时，后续相同请求会等待并共享第一个请求的结果
2. **临时缓存**: 请求完成后立即清理，不缓存响应数据
3. **唯一 Key**: 基于 URL + HTTP 方法 + 请求体生成唯一 key
4. **安全机制**: 自动清理超过 5 分钟的陈旧请求

**核心代码**:
```typescript
class RequestDeduplicator {
  private pendingRequests = new Map<string, Promise<unknown>>();
  private requestTimestamps = new Map<string, number>();
  private readonly MAX_AGE_MS = 5 * 60 * 1000; // 5 minutes

  private generateKey(url: string, options?: RequestInit): string {
    const method = options?.method || 'GET';
    const body = options?.body ? JSON.stringify(options.body) : '';
    return `${method}:${url}:${body}`;
  }

  private cleanStaleRequests(): void {
    const now = Date.now();
    for (const [key, timestamp] of this.requestTimestamps.entries()) {
      if (now - timestamp > this.MAX_AGE_MS) {
        this.pendingRequests.delete(key);
        this.requestTimestamps.delete(key);
      }
    }
  }

  async deduplicate<T>(
    url: string,
    options: RequestInit | undefined,
    fetcher: () => Promise<T>
  ): Promise<T> {
    this.cleanStaleRequests();

    const key = this.generateKey(url, options);

    // If request is pending, wait for it
    if (this.pendingRequests.has(key)) {
      console.debug(`Request deduplication: reusing pending request for ${url}`);
      return this.pendingRequests.get(key) as Promise<T>;
    }

    // Create new request
    const promise = fetcher().finally(() => {
      // Clean up after request completes
      this.pendingRequests.delete(key);
      this.requestTimestamps.delete(key);
    });

    this.pendingRequests.set(key, promise);
    this.requestTimestamps.set(key, Date.now());

    return promise;
  }

  clear(): void {
    this.pendingRequests.clear();
    this.requestTimestamps.clear();
  }
}

export const requestDeduplicator = new RequestDeduplicator();
```

**使用示例**:
```typescript
// 组件 A 和组件 B 同时发起相同请求
const data1 = await apiCall(API_ENDPOINTS.getScript(key));  // 发起 HTTP 请求
const data2 = await apiCall(API_ENDPOINTS.getScript(key));  // 复用上面的请求

// 只发起一次 HTTP 请求，两个组件共享结果
```

**测试覆盖**: 7 个测试用例，覆盖：
- 请求去重
- 错误处理
- 并发控制
- 缓存清理
- 陈旧请求处理

---

### 4. Service 层（services/）

**职责**: 封装具体的 API 调用，提供语义化的方法名。

**scriptService 示例**:
```typescript
import { apiCall } from "../client";
import { API_ENDPOINTS } from "../endpoints";
import type { ScriptsResponse, ScriptDetail } from "../types";

export const scriptService = {
  /**
   * Get all scripts
   */
  async getAllScripts(signal?: AbortSignal): Promise<ScriptsResponse> {
    return apiCall<ScriptsResponse>(API_ENDPOINTS.getAllScripts(), { signal });
  },

  /**
   * Get script detail by key
   */
  async getScript(key: string, signal?: AbortSignal): Promise<ScriptDetail> {
    return apiCall<ScriptDetail>(API_ENDPOINTS.getScript(key), { signal });
  },
};
```

**characterService 示例**:
```typescript
export const characterService = {
  async getAllCharacters(signal?: AbortSignal): Promise<CharactersResponse> {
    return apiCall<CharactersResponse>(API_ENDPOINTS.getAllCharacters(), { signal });
  },

  async getCharacter(id: number, signal?: AbortSignal): Promise<CharacterDetail> {
    return apiCall<CharacterDetail>(API_ENDPOINTS.getCharacter(id), { signal });
  },

  async updatePrompt(id: number, prompt: string): Promise<void> {
    return apiCall(API_ENDPOINTS.updateCharacterPrompt(id), {
      method: 'POST',
      body: JSON.stringify({ image_prompt: prompt }),
    });
  },

  async generateImage(id: number, model: string = 'qwen'): Promise<void> {
    return apiCall(API_ENDPOINTS.generateCharacterImage(id), {
      method: 'POST',
      body: JSON.stringify({ model }),
    });
  },
};
```

**storyboardService 示例**:
```typescript
export const storyboardService = {
  async getStoryboards(key: string, signal?: AbortSignal): Promise<StoryboardResponse> {
    return apiCall<StoryboardResponse>(API_ENDPOINTS.getStoryboards(key), { signal });
  },

  async generate(key: string, episodeNumber: number): Promise<void> {
    return apiCall(API_ENDPOINTS.generateStoryboard(), {
      method: 'POST',
      body: JSON.stringify({ key, episode_number: episodeNumber }),
    });
  },
};
```

---

### 5. Types 层（types/）

**职责**: 定义所有 API 请求和响应的 TypeScript 类型。

**通用响应类型**:
```typescript
// types/index.ts
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}
```

**Script 类型**:
```typescript
// types/script.ts
export interface ScriptsResponse {
  scripts: ScriptItem[];
}

export interface ScriptItem {
  key: string;
  drama_name: string;
  episode_number: number;
  created_at: string;
  updated_at: string;
}

export interface ScriptDetail {
  key: string;
  drama_name: string;
  episode_number: number;
  script: string;
  created_at: string;
  updated_at: string;
}
```

**Character 类型**:
```typescript
// types/character.ts
export interface Character {
  id: number;
  character_name: string;
  character_description: string;
  image_prompt: string | null;
  image_url: string | null;
  script_key: string;
  drama_name: string;
  episode_number: number;
  created_at: string;
  updated_at: string;
}

export interface CharactersResponse {
  characters: Character[];
}

export interface CharacterDetail {
  character: Character;
}
```

**Storyboard 类型**:
```typescript
// types/storyboard.ts
export interface SubShot {
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

export interface StoryboardItem {
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
}

export interface StoryboardResponse {
  storyboards: StoryboardItem[];
}
```

---

## 错误处理

### 1. 认证错误（4003）

当 API 返回 4003 错误码时，自动重定向到登录页：

```typescript
// client.ts
if (result.code === 4003) {
  const authUrl = (result.data as any)?.auth_url;
  if (authUrl) {
    console.debug("Not authenticated, redirecting to login:", authUrl);
    window.location.href = authUrl;  // 跳转到 Google OAuth 登录
    throw new Error(result.message || "未登录，正在跳转到登录页");
  }
}
```

**响应示例**:
```json
{
  "code": 4003,
  "message": "未登录",
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
  }
}
```

### 2. 其他错误

统一抛出错误，由组件层处理：

```typescript
if (result.code !== 0) {
  throw new Error(result.message || `API error! code: ${result.code}`);
}
```

**组件中的错误处理**:
```typescript
const [error, setError] = useState<string | null>(null);

try {
  const data = await apiCall(API_ENDPOINTS.getScript(key));
  setData(data);
  setError(null);
} catch (err) {
  if ((err as Error).name === "AbortError") {
    // 请求被取消，忽略
    return;
  }
  console.error("Error fetching data:", err);
  setError((err as Error).message || "数据加载失败");
}
```

---

## 请求取消

所有 Service 方法都支持 `AbortSignal` 参数，用于取消请求：

```typescript
useEffect(() => {
  const abortController = new AbortController();

  const fetchData = async () => {
    try {
      const data = await scriptService.getScript(key, abortController.signal);
      setScript(data.script);
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        console.debug("Request cancelled");
        return;
      }
      setError((err as Error).message);
    }
  };

  fetchData();

  // 组件卸载时取消请求
  return () => {
    abortController.abort();
  };
}, [key]);
```

---

## 最佳实践

### 1. 始终使用 Service 层

```typescript
// ❌ 不推荐：直接调用 apiCall
const data = await apiCall(API_ENDPOINTS.getScript(key));

// ✅ 推荐：使用 Service
const data = await scriptService.getScript(key);
```

### 2. 提供 AbortSignal

```typescript
// ✅ 推荐：支持请求取消
async getScript(key: string, signal?: AbortSignal): Promise<ScriptDetail> {
  return apiCall<ScriptDetail>(API_ENDPOINTS.getScript(key), { signal });
}
```

### 3. 类型安全

```typescript
// ✅ 明确指定泛型类型
const data = await apiCall<ScriptsResponse>(API_ENDPOINTS.getAllScripts());
```

### 4. 错误处理

```typescript
// ✅ 区分 AbortError 和其他错误
catch (err) {
  if ((err as Error).name === "AbortError") {
    return; // 忽略取消错误
  }
  console.error("Error:", err);
  setError((err as Error).message);
}
```

### 5. 调试日志

```typescript
// ✅ 使用 console.debug（方便后续删除）
console.debug("API call:", url);
console.debug("Request deduplication:", key);
```

---

## 测试

### Client 测试（6 个测试）

```typescript
describe("apiCall", () => {
  it("should make successful API call", async () => {
    // ...
  });

  it("should handle authentication error (4003)", async () => {
    // ...
  });

  it("should throw error for non-zero code", async () => {
    // ...
  });
});
```

### Endpoints 测试（20 个测试）

```typescript
describe("API_ENDPOINTS", () => {
  it("should generate correct script endpoints", () => {
    expect(API_ENDPOINTS.getAllScripts()).toBe(`${API_BASE_URL}/api/scripts`);
    expect(API_ENDPOINTS.getScript("test-key")).toBe(
      `${API_BASE_URL}/api/scripts/test-key`
    );
  });

  it("should URL encode keys with special characters", () => {
    expect(API_ENDPOINTS.getScript("key with spaces")).toContain(
      "key%20with%20spaces"
    );
  });
});
```

### RequestDeduplicator 测试（7 个测试）

```typescript
describe("RequestDeduplicator", () => {
  it("should deduplicate concurrent requests", async () => {
    // ...
  });

  it("should clean stale requests", () => {
    // ...
  });
});
```

---

## 总结

API 集成要点：
1. **分层架构**: Client → Service → Component
2. **请求去重**: 自动合并并发的相同请求
3. **认证处理**: 自动检测 4003 错误并跳转登录
4. **请求取消**: 所有方法支持 AbortSignal
5. **类型安全**: 完整的 TypeScript 类型定义
6. **测试覆盖**: 33 个单元测试（6 + 20 + 7）

---

**相关文档**:
- [架构设计](./architecture.md)
- [状态管理](./state-management.md)
- [组件开发](./components.md)
- [测试指南](./testing.md)
