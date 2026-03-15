# OpenClaw Agent-to-Agent 配置指南

## 问题描述
配置 OpenClaw 的 agent-to-agent 功能，允许不同 agent 之间进行通信。

## 先前遇到的问题
1. 默认配置下，agent 只能看到自己的会话（`tools.sessions.visibility = "tree"`）
2. agent id 配置不一致：`raw_api`（下划线） vs `raw-api`（连字符）

## 解决方案

### 1. 检查当前配置
```bash
openclaw config get tools
```

### 2. 更新会话可见性（允许查看所有会话）
```bash
openclaw config patch --json '{"tools": {"sessions": {"visibility": "all"}}}'
```

### 3. 更新 agent-to-agent 允许列表
```bash
openclaw config patch --json '{"tools": {"agentToAgent": {"enabled": true, "allow": ["main", "raw-api"]}}}'
```

### 4. 验证配置
```bash
openclaw config get tools.sessions
openclaw config get tools.agentToAgent
```

### 5. 重启网关应用配置
```bash
openclaw gateway restart
```

## 快速配置命令（一行完成）
```bash
openclaw config patch --json '{"tools": {"sessions": {"visibility": "all"}, "agentToAgent": {"enabled": true, "allow": ["main", "raw-api"]}}}' && openclaw gateway restart
```

## 测试跨 agent 通信

### 方法1：使用 CLI 命令
```bash
# 发送消息到 main agent
openclaw agent --agent main --message "测试消息"
```

### 方法2：使用 sessions_send 工具
```bash
openclaw sessions send --session agent:main:main --message "测试消息"
```

### 方法3：在 agent 会话中使用工具
```json
{
  "action": "sessions_send",
  "sessionKey": "agent:main:main",
  "message": "测试消息"
}
```

## 验证命令

### 查看所有会话
```bash
openclaw sessions --all-agents
```

### 检查 agent 列表
```bash
openclaw agents list
```

### 查看会话详情
```bash
openclaw sessions list --json
```

## 关键配置要点

1. **`tools.sessions.visibility`** 必须设置为 `"all"`
   - `"tree"`：只能看到当前会话和创建的 subagent（默认）
   - `"self"`：只能看到当前会话
   - `"agent"`：能看到当前 agent 的所有会话
   - `"all"`：能看到所有 agent 的所有会话

2. **`tools.agentToAgent.allow`** 配置
   - 必须包含允许通信的 agent id
   - agent id 必须与实际 agent id 完全一致
   - 区分大小写和符号：`raw-api` ≠ `raw_api`

3. **agent id 格式**
   - 查看实际 agent id：`openclaw agents list`
   - 常见 agent id：`main`, `raw-api`, `test2`, `team1_test` 等

## 故障排除

### 错误1：Session send visibility is restricted
```bash
# 解决方案
openclaw config patch --json '{"tools": {"sessions": {"visibility": "all"}}}'
```

### 错误2：Agent-to-agent messaging denied by tools.agentToAgent.allow
```bash
# 解决方案：检查并更新允许列表
openclaw config get tools.agentToAgent
openclaw config patch --json '{"tools": {"agentToAgent": {"allow": ["main", "raw-api"]}}}'
```

### 错误3：agentId is not allowed for sessions_spawn
```bash
# 解决方案：检查允许的 agent
openclaw agents list
# 只能创建允许列表中的 agent 的 subagent
```

## 配置示例

### 完整配置示例
```json
{
  "tools": {
    "sessions": {
      "visibility": "all"
    },
    "agentToAgent": {
      "enabled": true,
      "allow": ["main", "raw-api", "test2", "team1_test"]
    }
  }
}
```

### 最小配置示例
```json
{
  "tools": {
    "sessions": {
      "visibility": "all"
    },
    "agentToAgent": {
      "enabled": true,
      "allow": ["main", "raw-api"]
    }
  }
}
```

## 注意事项

1. **安全性**：设置 `visibility="all"` 会暴露所有会话，请确保在安全环境中使用
2. **性能**：允许大量 agent 通信可能会影响性能
3. **重启要求**：配置更改后需要重启网关才能生效
4. **验证**：配置后务必使用验证命令检查配置是否正确应用

## 相关文档

- OpenClaw 官方文档：https://docs.openclaw.ai
- Agent 配置指南：https://docs.openclaw.ai/agents
- 会话管理：https://docs.openclaw.ai/sessions

---
*配置文件创建时间：2026-03-15 22:18*
*测试环境：OpenClaw 2026.3.7*
*测试结果：跨 agent 通信功能正常*