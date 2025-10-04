# 开发者文档

本目录包含项目的开发指南、业务技术细节和工程实践文档。

## 快速入门

- [开发入门指南](getting-started.md) - 本地开发、Docker、K8s 等各种开发模式的完整指南
- [Git Hooks 和 CI/CD](git-hooks-and-ci.md) - 代码提交规范、Git Hooks 配置和 GitHub Actions 流程

## 业务技术细节

- [Google OAuth 登录](google-oauth-authentication.md) - Google OAuth 2.0 登录的完整配置和集成指南

## 文档说明

本目录下的文档主要面向：
- 🔧 **开发人员** - 快速上手项目开发，理解业务功能的技术实现
- 🚀 **运维人员** - 配置和部署相关功能
- 📚 **文档维护者** - 记录业务技术细节和最佳实践

## 文档组织原则

- 开发指南文档放在 `dev/` 根目录
- 每个独立的业务功能模块一个文档
- 包含完整的配置、使用和故障排查说明
- 提供代码示例和实际操作命令
- 保持文档与代码同步更新

## 其他文档

- [API 文档](../api/README.md) - API 接口说明和 TypeScript 类型定义
- [前端开发指南](../frontend/README.md) - 前端技术架构、组件设计和测试指南
- [Kubernetes 部署](../k8s/README.md) - K8s 完整部署指南（本地/远程）
- [项目主 README](../../README.md) - 项目概览和快速开始
