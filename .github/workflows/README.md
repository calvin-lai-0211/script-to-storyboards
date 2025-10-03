# GitHub Actions Workflows

本目录包含项目的 CI/CD 配置。

## 📋 Workflow 说明

### **CI - 持续集成** (`ci.yml`)

**触发条件**：
- Push 到 `main` 分支
- 创建/更新 Pull Request 到 `main` 分支

**检查项目**：
- ✅ 前端测试 (54 tests)
- ✅ TypeScript 类型检查
- ✅ ESLint 代码检查
- ✅ 构建验证
- ✅ 覆盖率上传（可选）

**并发控制**：
- 同一 PR 的多次 push 会自动取消之前的运行
- 避免重复执行，节省资源

**运行时间**：约 2-3 分钟

---

## 🚀 使用说明

### 查看 CI 状态

1. **在 PR 页面**：
   - 查看 "Checks" 标签
   - 所有检查必须通过才能合并

2. **在 Actions 页面**：
   - 访问 `https://github.com/calvin-lai-0211/script-to-storyboards/actions`
   - 查看详细的运行日志

### 本地运行相同检查

```bash
# 前端检查（与 CI 完全相同）
cd frontend
pnpm run test:run         # 运行测试
pnpm exec tsc --noEmit    # 类型检查
pnpm run lint             # 代码检查
pnpm run build            # 构建验证
```

### 并发控制

- ✅ **同一 PR 多次 push**：自动取消旧的运行，只执行最新的
- ✅ **不同 PR**：并行执行，互不影响
- ✅ **节省资源**：避免重复检查

### 跳过 CI（紧急情况）

在 commit 消息中添加 `[skip ci]` 或 `[ci skip]`：

```bash
git commit -m "docs: update README [skip ci]"
```

⚠️ **不推荐**：跳过 CI 可能导致未检测到的问题

---

## 📊 CI 检查对应关系

| CI 检查 | 本地 Pre-commit Hook | 说明 |
|---------|---------------------|------|
| Run tests | `pnpm run test:run` | 运行所有单元测试 |
| Type check | `pnpm exec tsc --noEmit` | TypeScript 类型检查 |
| Lint | `pnpm run lint` | ESLint 代码规范检查 |
| Build check | `pnpm run build` | 验证构建是否成功 |

---

## 🔧 配置文件说明

### 并发控制

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

- 同一 PR 的新 push 会取消旧的运行
- 基于 PR 号或 ref 进行分组

### 环境变量

```yaml
env:
  VITE_API_BASE_URL: http://localhost:8001
```

### 缓存策略

- **Node modules**: 使用 pnpm 缓存
- **依赖锁定**: 使用 `--frozen-lockfile` 确保一致性

### 运行环境

- **OS**: Ubuntu Latest
- **Node**: 20.x
- **pnpm**: 8.x

---

## 🐛 常见问题

### Q: 为什么会有多个 workflow 同时运行？

**答**：已优化！现在使用并发控制：
- 同一 PR 的多次 push 会自动取消旧的运行
- 只保留最新的检查

### Q: CI 失败但本地通过？

**可能原因**：
1. 依赖版本不一致 → 使用 `pnpm install --frozen-lockfile`
2. 环境变量缺失 → 检查 workflow 中的 `env` 配置
3. 缓存问题 → 在 Actions 页面清除缓存

### Q: 如何查看正在运行的检查？

1. 访问 PR 页面的 "Checks" 标签
2. 点击具体的检查查看实时日志
3. 失败时会显示详细的错误信息

### Q: 如何重新运行失败的检查？

在 PR 页面点击 "Re-run jobs" 按钮

---

## 📚 相关文档

- [GitHub Actions 文档](https://docs.github.com/actions)
- [pnpm CI 配置](https://pnpm.io/continuous-integration)
- [Pre-commit Hooks](../../.githooks/README.md)
- [并发控制文档](https://docs.github.com/en/actions/using-jobs/using-concurrency)
