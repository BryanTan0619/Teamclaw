# OpenClaw 常用配置命令速查

## 一、Agent-to-Agent 通信配置

### 1. 查看当前配置
```bash
openclaw config get tools.sessions
openclaw config get tools.agentToAgent
```

### 2. 配置会话可见性
```bash
openclaw config patch --json '{"tools": {"sessions": {"visibility": "all"}}}'
```

### 3. 配置 agent 通信白名单
```bash
openclaw config patch --json '{"tools": {"agentToAgent": {"enabled": true, "allow": ["main", "agent1"]}}}'
```

### 4. 一键配置（推荐）
```bash
openclaw config patch --json '{"tools": {"sessions": {"visibility": "all"}, "agentToAgent": {"enabled": true, "allow": ["main", "agent1"]}}}' && openclaw gateway restart
```

### 5. 验证与重启
```bash
openclaw config get tools.agentToAgent
openclaw gateway restart
```

### 6. 测试跨 agent 通信
```bash
openclaw agent --agent main --message "测试消息"
openclaw sessions --all-agents
```

---

## 二、Channel 绑定配置

### 1. 查看当前绑定
```bash
openclaw config get bindings
```

### 2. 设置绑定（推荐）
```bash
# 绑定 Telegram 到 agent1
openclaw config set bindings '[{"type": "route", "agentId": "agent1", "match": {"channel": "telegram"}}]'

# 绑定多个频道
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram"}}, {"type": "route", "agentId": "agent1", "match": {"channel": "webchat"}}]'

# 绑定特定账号
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram", "accountId": "main-bot"}}]'
```

### 3. 重启生效
```bash
openclaw gateway restart
```

### 4. 查看路由
```bash
openclaw agents list --bindings
```

---

## 三、常用命令速查表

| 用途 | 命令 |
|------|------|
| 查看绑定 | `openclaw config get bindings` |
| 设置绑定 | `openclaw config set bindings '[...]'` |
| 查看 agent 列表 | `openclaw agents list` |
| 查看路由 | `openclaw agents list --bindings` |
| 查看会话 | `openclaw sessions --all-agents` |
| 重启网关 | `openclaw gateway restart` |
| 查看日志 | `openclaw logs --tail 100` |

---

## 四、配置参数说明

### visibility 取值
- `"tree"`: 只能看到当前会话和创建的 subagent（默认）
- `"self"`: 只能看到当前会话
- `"agent"`: 能看到当前 agent 的所有会话
- `"all"`: 能看到所有 agent 的所有会话

### bindings 匹配条件
| 字段 | 说明 | 必填 |
|------|------|------|
| `type` | 固定为 `"route"` | ✅ |
| `agentId` | 目标 agent ID | ✅ |
| `channel` | 频道类型（telegram/webchat 等） | ✅ |
| `accountId` | 账号 ID | 可选 |
| `peerId` | 用户 ID | 可选 |
| `groupId` | 群组 ID | 可选 |

---

## 五、注意事项

1. **配置后需重启**：所有配置修改后需执行 `openclaw gateway restart`
2. **agent ID 格式**：区分大小写和符号，如 `agent1` ≠ `raw_api`
3. **安全性**：`visibility="all"` 会暴露所有会话，确保安全环境使用
4. **匹配优先级**：按 `bindings` 数组顺序匹配，第一个匹配生效

---

## 六、外部 Agent 配置

### 1. 查看已有 OpenClaw Agent

```bash
uv run scripts/cli.py -u <username> openclaw sessions
```

### 2. 读取 Agent 的 IDENTITY 文件

**步骤 1: 查看 agent 详情获取 workspace 路径**
```bash
uv run scripts/cli.py -u <username> openclaw detail --name <agent_name>
```

**步骤 2: 查看 workspace 中的文件列表**
```bash
uv run scripts/cli.py -u <username> openclaw workspace-files --workspace <workspace_path>
```

**步骤 3: 读取具体文件（如 IDENTITY.md）**
```bash
uv run scripts/cli.py -u <username> openclaw workspace-file-read \
  --workspace <workspace_path> \
  --filename IDENTITY.md
```

### 3. 创建新的 OpenClaw Agent

```bash
uv run scripts/cli.py -u <username> openclaw add --data '<JSON_DATA>'
```

**参数说明:**

| 参数 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | Agent 名称，全局唯一（只能包含字母、数字、下划线和连字符） |
| `workspace` | 可选 | 自定义工作区路径（不指定则自动生成） |

**示例 - 创建基础 agent:**
```bash
uv run scripts/cli.py -u Avalon_01 openclaw add --data '{"name": "my_new_agent"}'
```

**示例 - 指定自定义工作区:**
```bash
uv run scripts/cli.py -u Avalon_01 openclaw add \
  --data '{"name": "my_new_agent", "workspace": "/custom/path"}'
```

### 4. 修改 Agent 配置

```bash
uv run scripts/cli.py -u <username> openclaw update-config \
  --data '<JSON_CONFIG_WITH_AGENT_NAME>'
```

**基本配置示例：**
```bash
uv run scripts/cli.py -u Avalon_01 openclaw update-config \
  --data '{
    "agent_name": "my_new_agent",
    "temperature": 0.7,
    "model": "gpt-4o-mini"
  }'
```

**关闭所有 Tool 权限：**

使用 `tools.deny: ["*"]` 可以禁止 Agent 调用所有工具，仅保留纯文本对话能力：
```bash
uv run scripts/cli.py -u Avalon_01 openclaw update-config \
  --data '{
    "agent_name": "my_new_agent",
    "tools": {
      "deny": ["*"]
    }
  }'
```

配置说明：
- `tools.profile`: 工具配置文件路径（可选）
- `tools.alsoAllow`: 额外允许的工具列表（可选）
- `tools.deny`: 禁止的工具列表，`["*"]` 表示禁止所有工具

**验证配置：**
```bash
uv run scripts/cli.py -u Avalon_01 openclaw detail --name my_new_agent
```

### 5. 常用文件操作命令速查

| 用途 | 命令 |
|------|------|
| 查看所有 sessions | `openclaw sessions` |
| 查看 agent 详情 | `openclaw detail --name <agent_name>` |
| 查看 workspace 文件列表 | `openclaw workspace-files --workspace <path>` |
| 读取具体文件 | `openclaw workspace-file-read --workspace <path> --filename <file>` |
| 创建新 agent | `openclaw add --agent-name <name> ...` |
| 修改 agent 配置 | `openclaw update-config --agent <name> ...` |

---

## 七、注意事项

1. **配置后需重启**：所有配置修改后需执行 `openclaw gateway restart`
2. **agent ID 格式**：区分大小写和符号，如 `agent1` ≠ `raw_api`
3. **安全性**：`visibility="all"` 会暴露所有会话，确保安全环境使用
4. **匹配优先级**：按 `bindings` 数组顺序匹配，第一个匹配生效

---
*文档版本：v2.1 | 更新时间：2026-03-17*
