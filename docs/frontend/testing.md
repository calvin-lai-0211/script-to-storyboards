# 测试指南

本文档详细说明项目的测试框架、编写方法和最佳实践。

## 测试技术栈

- **Vitest**: 快速的单元测试框架（基于 Vite）
- **@testing-library/react**: React 组件测试工具
- **@testing-library/jest-dom**: DOM 断言库
- **jsdom**: 模拟浏览器环境

## 项目测试概览

### 测试覆盖情况

**总计**: 54 个测试，全部通过

| 模块 | 文件 | 测试数 | 状态 |
|------|------|--------|------|
| API Client | `api/__tests__/client.test.ts` | 6 | ✅ |
| API Endpoints | `api/__tests__/endpoints.test.ts` | 20 | ✅ |
| Request Deduplicator | `api/__tests__/requestDeduplicator.test.ts` | 7 | ✅ |
| Character Store | `store/__tests__/useCharacterStore.test.ts` | 5 | ✅ |
| Scene Store | `store/__tests__/useSceneStore.test.ts` | 4 | ✅ |
| Prop Store | `store/__tests__/usePropStore.test.ts` | 4 | ✅ |
| Episode Store | `store/__tests__/useEpisodeStore.test.ts` | 8 | ✅ |

---

## 测试配置

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.config.ts',
        '**/index.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    },
  },
});
```

### 测试设置（src/test/setup.ts）

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// 每个测试后清理
afterEach(() => {
  cleanup();
});
```

---

## 测试命令

```bash
# 运行所有测试（监听模式）
npm run test

# 运行所有测试（单次）
npm run test:run

# 运行测试 UI 界面
npm run test:ui

# 生成测试覆盖率报告
npm run test:cov
```

**覆盖率报告**: 运行 `npm run test:cov` 后，打开 `coverage/index.html` 查看详细覆盖率。

---

## 测试示例

### 1. API Client 测试

```typescript
// api/__tests__/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiCall } from '../client';

describe('apiCall', () => {
  beforeEach(() => {
    // 清理 Mock
    vi.clearAllMocks();
  });

  it('should make successful API call', async () => {
    // Mock fetch
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          code: 0,
          message: 'success',
          data: { id: 1, name: 'test' },
        }),
      })
    ) as any;

    const result = await apiCall('/api/test');

    expect(fetch).toHaveBeenCalledWith('/api/test', expect.any(Object));
    expect(result).toEqual({ id: 1, name: 'test' });
  });

  it('should handle API error (non-zero code)', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          code: 500,
          message: 'Internal Server Error',
          data: null,
        }),
      })
    ) as any;

    await expect(apiCall('/api/test')).rejects.toThrow('Internal Server Error');
  });

  it('should handle authentication error (4003)', async () => {
    // Mock window.location
    delete (window as any).location;
    (window as any).location = { href: '' };

    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          code: 4003,
          message: '未登录',
          data: { auth_url: 'https://example.com/login' },
        }),
      })
    ) as any;

    await expect(apiCall('/api/test')).rejects.toThrow();
    expect(window.location.href).toBe('https://example.com/login');
  });
});
```

### 2. Endpoints 测试

```typescript
// api/__tests__/endpoints.test.ts
import { describe, it, expect } from 'vitest';
import { API_ENDPOINTS } from '../endpoints';

describe('API_ENDPOINTS', () => {
  it('should generate correct script endpoints', () => {
    expect(API_ENDPOINTS.getAllScripts()).toBe('http://localhost:8000/api/scripts');
    expect(API_ENDPOINTS.getScript('test-key')).toBe('http://localhost:8000/api/scripts/test-key');
  });

  it('should URL encode keys with special characters', () => {
    const key = 'test key with spaces';
    const endpoint = API_ENDPOINTS.getScript(key);
    expect(endpoint).toContain('test%20key%20with%20spaces');
  });

  it('should handle Chinese characters', () => {
    const key = '测试剧本';
    const endpoint = API_ENDPOINTS.getScript(key);
    expect(endpoint).toContain(encodeURIComponent('测试剧本'));
  });
});
```

### 3. RequestDeduplicator 测试

```typescript
// api/__tests__/requestDeduplicator.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { requestDeduplicator } from '../requestDeduplicator';

describe('RequestDeduplicator', () => {
  beforeEach(() => {
    requestDeduplicator.clear();
  });

  it('should deduplicate concurrent requests', async () => {
    const mockFetcher = vi.fn(() => Promise.resolve({ data: 'test' }));

    // 并发发起 3 个相同请求
    const [result1, result2, result3] = await Promise.all([
      requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher),
      requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher),
      requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher),
    ]);

    // 只调用一次 fetcher
    expect(mockFetcher).toHaveBeenCalledTimes(1);

    // 三个请求共享结果
    expect(result1).toEqual({ data: 'test' });
    expect(result2).toEqual({ data: 'test' });
    expect(result3).toEqual({ data: 'test' });
  });

  it('should handle errors correctly', async () => {
    const mockFetcher = vi.fn(() => Promise.reject(new Error('API Error')));

    await expect(
      requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher)
    ).rejects.toThrow('API Error');
  });

  it('should clean up after request completes', async () => {
    const mockFetcher = vi.fn(() => Promise.resolve({ data: 'test' }));

    await requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher);

    // 请求完成后，新请求应该重新发起
    await requestDeduplicator.deduplicate('/api/test', undefined, mockFetcher);

    expect(mockFetcher).toHaveBeenCalledTimes(2);
  });
});
```

### 4. Zustand Store 测试

```typescript
// store/__tests__/useEpisodeStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useEpisodeStore } from '../useEpisodeStore';

describe('useEpisodeStore', () => {
  beforeEach(() => {
    useEpisodeStore.getState().clearAll();
  });

  it('should set and get current episode', () => {
    const { setCurrentEpisode } = useEpisodeStore.getState();

    setCurrentEpisode({
      key: 'test-key',
      drama_name: '测试剧本',
      episode_number: 1,
    });

    const { currentEpisode } = useEpisodeStore.getState();
    expect(currentEpisode).toEqual({
      key: 'test-key',
      drama_name: '测试剧本',
      episode_number: 1,
    });
  });

  it('should cache and retrieve episode data', () => {
    const { setEpisode, getEpisode } = useEpisodeStore.getState();

    const testData = {
      key: 'test-key',
      drama_name: '测试剧本',
      episode_number: 1,
      script: '剧本内容',
      created_at: '2025-10-04',
      updated_at: '2025-10-04',
    };

    setEpisode('test-key', testData);

    const cached = getEpisode('test-key');
    expect(cached).toEqual(testData);
  });

  it('should clear specific episode cache', () => {
    const { setEpisode, clearKey, getEpisode } = useEpisodeStore.getState();

    setEpisode('key1', { /* ... */ });
    setEpisode('key2', { /* ... */ });

    clearKey('key1');

    expect(getEpisode('key1')).toBeUndefined();
    expect(getEpisode('key2')).toBeDefined();
  });

  it('should clear all caches', () => {
    const { setEpisode, setCurrentEpisode, clearAll, getEpisode, currentEpisode } = useEpisodeStore.getState();

    setCurrentEpisode({ key: 'test-key' });
    setEpisode('key1', { /* ... */ });

    clearAll();

    expect(useEpisodeStore.getState().currentEpisode).toBeNull();
    expect(getEpisode('key1')).toBeUndefined();
  });
});
```

### 5. React 组件测试（示例）

```typescript
// components/__tests__/BackButton.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import BackButton from '../BackButton';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('BackButton', () => {
  it('should render correctly', () => {
    render(
      <BrowserRouter>
        <BackButton />
      </BrowserRouter>
    );

    expect(screen.getByText('返回')).toBeInTheDocument();
  });

  it('should navigate back when clicked', () => {
    render(
      <BrowserRouter>
        <BackButton />
      </BrowserRouter>
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});
```

---

## 测试最佳实践

### 1. 测试命名

```typescript
// ✅ 清晰描述测试内容
it('should return cached data when available', () => { /* ... */ });

// ❌ 模糊的测试名称
it('test cache', () => { /* ... */ });
```

### 2. Arrange-Act-Assert 模式

```typescript
it('should add item to cart', () => {
  // Arrange: 准备测试数据
  const item = { id: 1, name: 'Test Item' };

  // Act: 执行操作
  addToCart(item);

  // Assert: 验证结果
  expect(getCart()).toContainEqual(item);
});
```

### 3. 使用 beforeEach 清理状态

```typescript
describe('MyStore', () => {
  beforeEach(() => {
    // 每个测试前清理状态
    useMyStore.getState().reset();
  });

  it('test 1', () => { /* ... */ });
  it('test 2', () => { /* ... */ });
});
```

### 4. Mock 外部依赖

```typescript
// Mock fetch
global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ data: 'test' }),
  })
) as any;

// Mock window.location
delete (window as any).location;
(window as any).location = { href: '' };

// Mock React Router
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({ id: '123' }),
}));
```

### 5. 测试错误情况

```typescript
it('should handle API error', async () => {
  global.fetch = vi.fn(() => Promise.reject(new Error('Network Error')));

  await expect(fetchData()).rejects.toThrow('Network Error');
});
```

### 6. 测试异步代码

```typescript
it('should fetch data asynchronously', async () => {
  const data = await fetchData();

  expect(data).toEqual({ id: 1, name: 'test' });
});
```

### 7. 使用 describe 分组

```typescript
describe('UserService', () => {
  describe('getUser', () => {
    it('should return user by id', () => { /* ... */ });
    it('should throw error for invalid id', () => { /* ... */ });
  });

  describe('updateUser', () => {
    it('should update user data', () => { /* ... */ });
    it('should validate input', () => { /* ... */ });
  });
});
```

---

## 覆盖率目标

### 当前覆盖率

- **API 层**: 90%+（6 + 20 + 7 = 33 个测试）
- **Store 层**: 80%+（5 + 4 + 4 + 8 = 21 个测试）
- **组件层**: 待完善

### 覆盖率要求

- **核心业务逻辑**: 100%
- **API 和 Store**: 80%+
- **UI 组件**: 60%+

---

## 常见问题

### 1. 测试超时

```typescript
// 增加超时时间
it('should handle long request', async () => {
  // ...
}, 10000); // 10 秒超时
```

### 2. Mock 失败

```typescript
// 确保在测试前清理 Mock
beforeEach(() => {
  vi.clearAllMocks();
});
```

### 3. DOM 相关错误

```typescript
// 使用 @testing-library/react 渲染组件
import { render, screen } from '@testing-library/react';

render(<MyComponent />);
expect(screen.getByText('Hello')).toBeInTheDocument();
```

---

## 总结

测试要点：
1. **Vitest**: 快速、现代的测试框架
2. **覆盖率目标**: API/Store 80%+，核心逻辑 100%
3. **测试模式**: Arrange-Act-Assert
4. **Mock 策略**: 外部依赖全部 Mock
5. **持续集成**: 所有 PR 必须通过测试

---

**相关文档**:
- [API 集成](./api-integration.md)
- [状态管理](./state-management.md)
- [代码质量](./code-quality.md)
