# CoPaw 项目概览（详细版）

本文档面向阅读源码和二次开发的同学，基于仓库结构与核心模块，梳理 CoPaw 的整体定位、主要组件与扩展点，便于快速理解项目。

---

## 1. 项目定位

CoPaw 是一个运行在用户本地或私有环境中的个人 AI 助手。它强调：

- **多渠道接入**：可在钉钉、飞书、QQ、Discord、iMessage 等多种聊天应用中与用户交互。
- **本地可控**：配置、数据与任务在用户环境内执行与存储。
- **可扩展能力**：通过 Skills 体系和多 Agent 机制扩展能力边界。
- **自动化与定时**：支持定时任务与自动触发式工作流。

---

## 2. 核心能力概览

来自 README 与代码结构的核心能力包括：

1. **全域触达**：一个 CoPaw 可以接入多个聊天平台。
2. **由你掌控**：个性化与数据运行在你自己的环境中。
3. **多智能体协作**：多个独立 Agent 可协同完成任务。
4. **Skills 扩展**：内置技能 + 自定义技能自动加载。
5. **任务调度**：具备定时与计划任务能力。

---

## 3. 顶层目录结构

仓库主要目录如下：

```
CoPaw/
├── src/                 # Python 主代码（copaw 包）
├── console/             # 前端控制台（Vite + React）
├── website/             # 文档站点与静态文档
├── tests/               # 单元/集成测试
├── examples/            # 示例与测试工程（如 testpaw）
├── deploy/              # 部署相关（Docker 等）
├── scripts/             # 构建/安装脚本
├── README*.md           # 多语言 README
└── pyproject.toml       # Python 包与依赖配置
```

---

## 4. 后端核心模块（`src/copaw`）

### 4.1 CLI 与入口

- `src/copaw/cli/`：命令行入口及子命令。
- `src/copaw/cli/main.py`：Click 主入口，组织 `copaw init` / `copaw app` 等命令。

### 4.2 Web 与运行服务

- `src/copaw/app/`：Web 服务与运行核心
  - `channels/`：不同渠道的适配与消息处理
  - `runner/`：请求流式执行与响应
  - `multi_agent_manager.py`：多 Agent 管理与编排

### 4.3 Agent 与 Skills 系统

- `src/copaw/agents/`
  - `skills/`：内置技能（SKILL.md + 脚本/参考）
  - `skills_manager.py`：技能同步、合并与激活管理

### 4.4 模型与 Provider 管理

- `src/copaw/providers/`
  - `provider_manager.py`：内置 Provider 与默认模型定义
  - `openai_provider.py` / `anthropic_provider.py` / `gemini_provider.py` 等：各家模型接口适配
- `src/copaw/local_models/`：本地模型支持与桥接

### 4.5 配置与工作目录

- `src/copaw/config/`
  - `config.py`：配置模型
  - `utils.py`：工作目录路径规范化、浏览器路径发现
  - `context.py` / `timezone.py`：上下文与时区辅助

### 4.6 安全与防护

- `src/copaw/security/`
  - `skill_scanner/`：技能扫描与规则
  - `tool_guard/`：工具/操作安全控制

---

## 5. Skills 机制详解

Skills 是 CoPaw 的核心扩展机制，具备以下特性：

- **技能目录结构**：每个技能包含 `SKILL.md` 与脚本/参考文件。
- **内置技能路径**：`src/copaw/agents/skills/`
- **自定义技能路径**：工作目录下的 `customized_skills/`
- **激活技能路径**：工作目录下的 `active_skills/`
- **同步策略**：`skills_manager.py` 负责合并内置与自定义技能，并同步到 `active_skills`。

---

## 6. Channel 系统

Channel 负责与外部聊天平台交互：

- **BaseChannel** 统一约定消息格式与处理契约。
- **ChannelManager** 维护队列与并发消费，支持同会话消息合并与去抖。
- **注册与加载**：通过 registry 与配置确定可用渠道。

---

## 7. 模型与 Provider 体系

Provider 体系提供统一模型接入接口：

- `provider_manager.py` 中定义内置 Provider 与模型列表（`ModelInfo`）。
- 支持多家云端模型与本地模型（如 Ollama、MLX、llama.cpp）。
- 可在配置中选择提供方与模型，统一在运行层调用。

---

## 8. 配置与工作目录

配置与运行目录相关功能集中在 `src/copaw/config/`：

- **配置模型**：读取用户的配置文件与运行配置。
- **工作目录统一**：支持将历史路径迁移到当前工作目录。
- **运行状态文件**：维护心跳、任务、聊天记录等状态文件。

---

## 9. 前端控制台

前端控制台位于 `console/`，为独立的前端工程：

- 技术栈：Vite + React + Ant Design
- 用途：提供聊天 UI、配置管理、模型/频道管理等能力
- 构建产物会被后端打包并通过 Web 服务提供访问

---

## 10. 测试与质量门禁

贡献指南推荐的本地门禁如下（详见 `CONTRIBUTING*.md`）：

```bash
pip install -e ".[dev,full]"
pre-commit install
pre-commit run --all-files
pytest
```

若修改涉及 `console/` 或 `website/`，需执行：

```bash
cd console && npm run format
cd website && npm run format
```

---

## 11. 扩展与二次开发入口

常见扩展点：

1. **新增 Skill**：在工作目录 `customized_skills/` 添加技能目录。
2. **新增 Channel**：实现新的 `BaseChannel` 并注册。
3. **新增 Provider**：在 `providers/` 增加提供商适配与模型定义。

---

## 12. 相关链接

- 项目 README（中文）：`README_zh.md`
- 项目文档：<https://copaw.agentscope.io/>
- 贡献指南：`CONTRIBUTING_zh.md`

