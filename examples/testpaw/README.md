# testpaw

testpaw 是一个基于 Python 和 LangGraph 的多模块 Agent 工程，具备完整的运行入口、API、配置、多 Agent 管理、工具调用、安全扫描、频道分发、MCP 管理、记忆管理和定时任务能力。

本项目目标是提供一套可直接二次开发的工程骨架，强调以下几点：

1. 分层架构清晰，便于扩展
2. LangGraph 驱动 Agent 主流程
3. 模块化能力解耦，可独立测试
4. 全部能力通过测试验证

## 一、架构总览

testpaw 的核心分层如下：

1. cli
1. api
1. app
1. runtime
1. providers
1. channels
1. crons
1. mcp
1. memory
1. security
1. config

模块目录：

1. src/testpaw/cli
1. src/testpaw/api
1. src/testpaw/app
1. src/testpaw/agents
1. src/testpaw/runtime
1. src/testpaw/providers
1. src/testpaw/channels
1. src/testpaw/crons
1. src/testpaw/mcp
1. src/testpaw/memory
1. src/testpaw/envs
1. src/testpaw/local_models
1. src/testpaw/security
1. src/testpaw/config
1. src/testpaw/token_usage
1. src/testpaw/tokenizer
1. src/testpaw/tunnel
1. src/testpaw/approvals
1. src/testpaw/utils

## CoPaw 对照实现说明

按 CoPaw 的核心模块族，testpaw 已建立一一对应实现（轻量但可运行）：

1. agents -> src/testpaw/agents
1. app/workspace/runner 体系 -> src/testpaw/app + src/testpaw/runtime
1. channels -> src/testpaw/channels
1. crons -> src/testpaw/crons
1. mcp -> src/testpaw/mcp
1. memory -> src/testpaw/memory
1. providers -> src/testpaw/providers
1. security -> src/testpaw/security
1. config -> src/testpaw/config
1. envs -> src/testpaw/envs
1. local_models -> src/testpaw/local_models
1. token_usage -> src/testpaw/token_usage
1. tokenizer -> src/testpaw/tokenizer
1. tunnel -> src/testpaw/tunnel
1. approvals -> src/testpaw/approvals
1. utils -> src/testpaw/utils

说明：testpaw 当前是“功能等价骨架实现”，覆盖 CoPaw 的核心能力边界和扩展点，每个模块都具备可执行代码、API 路由或单元测试，不是空目录占位。

## 严格完整性审计

为了避免“目录存在但能力缺失”，testpaw 增加了契约测试：

1. CLI 对照契约：tests/unit/test_parity_contract.py
2. API 路由契约：tests/unit/test_parity_contract.py
3. 模块族存在性契约：tests/unit/test_parity_modules.py

执行：

```bash
python -m pytest -q
```

只要契约测试通过，就能保证关键模块与核心入口不会被回归破坏。

## 二、LangGraph 主流程

Agent 执行图定义在 src/testpaw/runtime/graph.py，执行路径为：

normalize -> guard -> plan -> run_tool 或 model_reply -> end

各节点职责：

1. normalize：输入标准化
1. guard：工具级安全策略检查
1. plan：选择工具路径或模型路径
1. run_tool：执行注册工具（示例包含 time 和 calc）
1. model_reply：走模型 Provider 生成回复

如果输入命中安全风险，会走阻断路径并返回拒绝响应。

## 三、核心模块说明

1. Workspace 运行单元
路径：src/testpaw/runtime/workspace.py
职责：聚合 Provider、ToolGuard、SkillScanner、Memory、Session、MCP、Channel。

2. 多 Agent 管理
路径：src/testpaw/app/multi_agent_manager.py
职责：按需创建、缓存和关闭多个 Workspace。

3. 配置管理
路径：src/testpaw/config/models.py 和 src/testpaw/config/service.py
职责：管理应用配置、Agent 配置、启用频道配置。

4. Provider 抽象
路径：src/testpaw/providers
职责：抽象模型提供层，当前默认实现为 Mock Provider，可替换为真实 LLM Provider。

5. 频道系统
路径：src/testpaw/channels
职责：统一消息分发，默认内置 console 频道。

6. 定时任务系统
路径：src/testpaw/crons
职责：增删查定时任务配置。

7. MCP 管理
路径：src/testpaw/mcp
职责：注册、查看、删除 MCP 客户端配置。

8. 记忆管理
路径：src/testpaw/memory
职责：按 session 存储和读取历史消息。

9. 安全系统
路径：src/testpaw/security/tool_guard.py 和 src/testpaw/security/skill_scanner.py
职责：输入危险词阻断、技能文本风险扫描。

## 四、API 能力

应用入口：src/testpaw/api/app.py

主要接口：

1. GET /
1. GET /health
1. POST /chat
1. POST /chat/stream
1. GET /agents
1. POST /agents/{agent_id}
1. GET /config
1. POST /config/channels
1. GET /cron/jobs
1. POST /cron/jobs
1. DELETE /cron/jobs/{job_id}
1. POST /mcp/register
1. GET /mcp/clients
1. GET /memory/{session_id}
1. GET /skills
1. POST /skills/{skill_id}/enable
1. POST /skills/{skill_id}/run
1. POST /skills/scan
1. GET /providers
1. POST /providers/activate
1. POST /providers/{provider_id}/config

## Web Console 页面（已内置）

启动服务后，直接打开：

```bash
http://127.0.0.1:8090/
```

页面提供三块核心能力：

1. 模型配置区：可查看 provider 列表、配置 model/base_url/api_key、切换激活 provider。
2. Skill 使用区：可查看 skills、启用/禁用技能、输入文本并执行 skill。
3. 聊天区：可直接发送消息到指定 agent 并查看返回结果。

说明：这次修复了你提到的 `{ "detail": "Not Found" }` 问题，根路径已返回控制台页面。

## Provider 说明

目前内置两个 Provider：

1. mock：离线可用，适合本地开发和测试
1. openai-compatible：OpenAI 兼容网关接入

`openai-compatible` 具备：

1. API Key 缺失时返回结构化错误前缀
1. 网络异常自动重试（指数退避）
1. Provider 激活与配置状态可落盘持久化（按 agent）

## 五、CLI 使用

CLI 入口：src/testpaw/cli/main.py

查看命令帮助：

```bash
python -m testpaw.cli.main --help
```

启动服务：

```bash
python -m testpaw.cli.main app --host 127.0.0.1 --port 8090 --log-level info
```

说明：如果你的环境 PATH 中包含脚本目录，也可直接使用 `testpaw app ...`。

## 六、快速开始

1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

2. 安装依赖

```bash
pip install -e .[dev]
```

3. 启动服务

```bash
python -m testpaw.cli.main app --host 127.0.0.1 --port 8090
```

4. 健康检查

```bash
curl http://127.0.0.1:8090/health
```

4.1 打开控制台页面

在浏览器访问 `http://127.0.0.1:8090/`，你会看到模型配置、skill 使用和聊天面板。

5. 调用聊天接口（非流式）

```bash
curl -X POST http://127.0.0.1:8090/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"default","session_id":"s1","user_id":"u1","channel":"console","text":"/calc 1+2*3"}'
```

6. 调用聊天接口（流式 SSE）

```bash
curl -N -X POST http://127.0.0.1:8090/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"default","session_id":"s1","user_id":"u1","channel":"console","text":"hello stream"}'
```

7. 常用能力接口示例

```bash
# 切换 provider
curl -X POST http://127.0.0.1:8090/providers/activate \
  -H "Content-Type: application/json" \
  -d '{"provider_id":"mock"}'

# 列出 skills
curl http://127.0.0.1:8090/skills

# 启用/禁用 skill
curl -X POST http://127.0.0.1:8090/skills/summary/enable \
  -H "Content-Type: application/json" \
  -d '{"enabled":true}'

# 运行 skill
curl -X POST http://127.0.0.1:8090/skills/summary/run \
  -H "Content-Type: application/json" \
  -d '{"text":"line1\nline2\nline3"}'

# Token 计数
curl -X POST http://127.0.0.1:8090/tokenizer/count \
  -H "Content-Type: application/json" \
  -d '{"text":"hello testpaw"}'

# Tunnel 打开与状态
curl -X POST http://127.0.0.1:8090/tunnel/open \
  -H "Content-Type: application/json" \
  -d '{"local_port":8090}'
curl http://127.0.0.1:8090/tunnel/status
```

8. 停止服务

按 `Ctrl+C` 停止前台服务进程。

## 七、运行验证（本仓库已实测）

已在本仓库环境中实测以下命令并通过：

1. `python -m testpaw.cli.main app --host 127.0.0.1 --port 8090 --log-level info`
2. `curl http://127.0.0.1:8090/health`
3. `curl -X POST http://127.0.0.1:8090/chat ...`
4. `curl -N -X POST http://127.0.0.1:8090/chat/stream ...`
5. `python -m pytest -q`

## 八、常见问题与排障

1. 命令 `testpaw` 找不到

原因：脚本安装目录不在 PATH。

处理：优先用模块方式运行。

```bash
python -m testpaw.cli.main app --host 127.0.0.1 --port 8090
```

2. 端口被占用

处理：换端口启动，例如 8091。

```bash
python -m testpaw.cli.main app --host 127.0.0.1 --port 8091
```

3. provider 切换后返回 not-configured

原因：`openai-compatible` 未配置 API Key。

处理：调用配置接口设置 `api_key` 或切回 `mock` provider。

4. SSE 无输出

处理：确保使用 `curl -N`，并确认服务未被反向代理缓冲。

## 九、测试

执行：

```bash
python -m pytest -q
```

当前测试覆盖包括：

1. LangGraph 路由分支
1. Workspace 生命周期与对话流程
1. API 主接口与模块接口
1. CLI 命令
1. 配置、多 Agent、频道、Cron、MCP、Memory、安全扫描模块

## 十、扩展建议

你可以按以下顺序扩展到生产版本：

1. 在现有 openai-compatible Provider 基础上接入你自己的网关和鉴权
1. 将 ConfigService 接入 JSON/YAML 持久化
1. 将 MemoryManager 升级为向量检索记忆
1. 增加更多频道适配器（Telegram、Discord、企业 IM）
1. 给 CronManager 增加真实调度器执行器
1. 为 MCP 增加网络连接校验与重试机制

## 十一、命名说明

本工程所有对外命名均已统一为 testpaw，包括：

1. Python 包名
1. CLI 命令名
1. README 文档名称
1. 默认配置中的 app_name
