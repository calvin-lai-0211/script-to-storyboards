# GitHub Actions Workflows

本目录包含项目的 CI/CD 配置。

## 📋 Workflows 说明

### 1. **CI - 持续集成** (`ci.yml`)
**触发条件**：
- Push 到 `main` 分支
- 创建 Pull Request 到 `main` 分支

**检查项目**：
- ✅ 前端测试 (54 tests)
- ✅ TypeScript 类型检查
- ✅ ESLint 代码检查
- ✅ 构建验证

**运行时间**：约 2-3 分钟

---

### 2. **PR Checks - Pull Request 检查** (`pr-checks.yml`)
**触发条件**：
- 创建/更新 Pull Request

**检查项目**：
- ✅ Pre-commit hooks 验证
- ✅ Bundle size 检查
- ✅ 生成 PR 摘要

**特点**：
- 自动生成检查摘要到 PR 页面
- 显示构建产物大小

---

### 3. **Frontend Checks - 前端专项检查** (`frontend-checks.yml`)
**触发条件**：
- Push 到 `main` 或 feature 分支
- 修改 `frontend/` 目录下的文件

**检查项目**：
- Tests, Type-check, Lint, Build

---

### 4. **Backend Checks - 后端专项检查** (`backend-checks.yml`)
**触发条件**：
- Push 到 `main` 或 feature 分支
- 修改后端代码 (`api/`, `models/`, `procedure/`, `utils/`)

**检查项目**：
- Flake8 语法检查
- Mypy 类型检查（可选）
- Python 语法验证

---

## 🚀 使用说明

### 查看 CI 状态

1. **在 PR 页面**：
   - 查看 "Checks" 标签
   - 所有检查必须通过才能合并

2. **在 Actions 页面**：
   - 访问 `https://github.com/<owner>/<repo>/actions`
   - 查看详细的运行日志

### 本地运行相同检查

```bash
# 前端检查（与 CI 相同）
cd frontend
pnpm run test:run    # 运行测试
pnpm exec tsc --noEmit  # 类型检查
pnpm run lint        # 代码检查
pnpm run build       # 构建验证
```

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
| Run tests | `npm run test:run` | 运行所有单元测试 |
| Type check | `npx tsc --noEmit` | TypeScript 类型检查 |
| Lint | `npm run lint` | ESLint 代码规范检查 |
| Build check | `npm run build` | 验证构建是否成功 |

---

## 🔧 配置文件说明

### 环境变量

**前端构建环境变量**：
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
- **Python**: 3.12 (backend)

---

## 🐛 常见问题

### Q: CI 失败但本地通过？

**可能原因**：
1. 依赖版本不一致 → 使用 `pnpm install --frozen-lockfile`
2. 环境变量缺失 → 检查 workflow 中的 `env` 配置
3. 缓存问题 → 在 Actions 页面清除缓存

### Q: 如何添加新的检查？

1. 编辑对应的 workflow 文件
2. 添加新的 step
3. 提交并测试

### Q: 如何禁用某个 workflow？

在 workflow 文件顶部添加：
```yaml
on:
  workflow_dispatch:  # 只允许手动触发
```

---

## 📚 相关文档

- [GitHub Actions 文档](https://docs.github.com/actions)
- [pnpm CI 配置](https://pnpm.io/continuous-integration)
- [Pre-commit Hooks](./.githooks/README.md)
