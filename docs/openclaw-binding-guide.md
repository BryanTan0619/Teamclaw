# OpenClaw Channel Binding 配置指南

## 经验总结

在配置 OpenClaw 的 channel 绑定时，发现了以下关键经验：

## 1. 两种配置方式的区别

### A. Agent 内部工具 API（我在用的）
```javascript
// 在 agent 会话中使用工具
{
  "action": "config.patch",
  "raw": "{\"bindings\": [...]}"
}
```

### B. 终端 CLI 命令（你在用的）
```bash
# 错误语法（会导致 unknown option '--json' 错误）
openclaw config patch --json '{"bindings": [...]}'

# 正确语法
openclaw config set bindings '[{"type": "route", "agentId": "raw-api", "match": {"channel": "telegram"}}]'
```

## 2. 正确的 CLI 命令

### 方法1：使用 `config set`（推荐，最简单）
```bash
openclaw config set bindings '[{"type": "route", "agentId": "raw-api", "match": {"channel": "telegram"}}, {"type": "route", "agentId": "main", "match": {"channel": "telegram", "accountId": "main-bot"}}]'
```

### 方法2：使用 `gateway config-patch`
```bash
openclaw gateway config-patch --json '{"bindings": [{"type": "route", "agentId": "raw-api", "match": {"channel": "telegram"}}, {"type": "route", "agentId": "main", "match": {"channel": "telegram", "accountId": "main-bot"}}]}'
```

### 方法3：使用文件方式
```bash
# 创建配置文件
echo '{"bindings": [...]}' > bindings.json

# 应用配置
openclaw config apply --file bindings.json
```

## 3. 常见错误及解决方法

### 错误1：`unknown option '--json'`
```bash
# 错误
openclaw config patch --json '{"bindings": [...]}'

# 正确
openclaw config set bindings --json '[{"bindings": [...]}]'
# 或者
openclaw gateway config-patch --json '{"bindings": [...]}'
```

### 错误2：JSON 解析错误
```bash
# 使用单引号包裹 JSON，内部双引号需要转义
openclaw config set bindings '[{\"type\": \"route\", \"agentId\": \"raw-api\", \"match\": {\"channel\": \"telegram\"}}]'

# 或者使用 JSON5 语法（推荐）
openclaw config set bindings '[{type: "route", agentId: "raw-api", match: {channel: "telegram"}}]'
```

## 4. 绑定配置示例

### 示例1：绑定 Telegram 到 raw-api
```bash
openclaw config set bindings '[{"type": "route", "agentId": "raw-api", "match": {"channel": "telegram"}}]'
```

### 示例2：绑定多个频道
```bash
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram"}}, {"type": "route", "agentId": "raw-api", "match": {"channel": "webchat"}}]'
```

### 示例3：绑定特定账号
```bash
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram", "accountId": "main-bot"}}]'
```

### 示例4：绑定特定用户
```bash
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram", "peerId": "123456789"}}]'
```

## 5. 验证配置

### 查看当前绑定
```bash
openclaw config get bindings
```

### 查看 agent 路由
```bash
openclaw agents list --bindings
```

### 重启网关使配置生效
```bash
openclaw gateway restart
```

## 6. 配置语法要点

### JSON 格式要求
```json
{
  "bindings": [
    {
      "type": "route",                    // 必须为 "route"
      "agentId": "agent-id",              // agent 的 ID
      "match": {                          // 匹配条件
        "channel": "channel-type",        // 频道类型
        "accountId": "account-id",        // 可选：账号ID
        "peerId": "user-id",              // 可选：用户ID
        "groupId": "group-id"             // 可选：群组ID
      }
    }
  ]
}
```

### 匹配条件优先级
1. 按 `bindings` 数组顺序匹配
2. 第一个匹配的规则生效
3. 可以组合多个条件

## 7. 实际测试案例

### 测试1：修改 Telegram 绑定
```bash
# 查看当前绑定
openclaw config get bindings

# 修改绑定
openclaw config set bindings '[{"type": "route", "agentId": "raw-api", "match": {"channel": "telegram"}}, {"type": "route", "agentId": "main", "match": {"channel": "telegram", "accountId": "main-bot"}}]'

# 验证修改
openclaw config get bindings
```

### 测试2：添加 Webchat 绑定
```bash
# 添加 webchat 绑定到当前 agent
openclaw config set bindings '[{"type": "route", "agentId": "raw-api", "match": {"channel": "webchat"}}]'
```

## 8. 故障排除流程

### 步骤1：检查命令语法
```bash
# 查看命令帮助
openclaw config set --help
openclaw gateway config-patch --help
```

### 步骤2：检查当前配置
```bash
openclaw config get bindings
```

### 步骤3：测试简单配置
```bash
# 先测试最简单的配置
openclaw config set bindings '[{"type": "route", "agentId": "main", "match": {"channel": "telegram"}}]'
```

### 步骤4：查看日志
```bash
openclaw logs --tail 50
```

## 9. 最佳实践

1. **先备份**：修改前先查看当前配置
2. **简单开始**：先测试最简单的绑定
3. **逐步复杂**：逐步添加更多匹配条件
4. **及时验证**：每次修改后立即验证
5. **查看日志**：关注配置更改和重启日志

## 10. 关键命令速查

| 用途 | 命令 |
|------|------|
| 查看绑定 | `openclaw config get bindings` |
| 设置绑定 | `openclaw config set bindings '[...]'` |
| 网关配置 | `openclaw gateway config-patch --json '{}'` |
| 查看路由 | `openclaw agents list --bindings` |
| 重启网关 | `openclaw gateway restart` |
| 查看日志 | `openclaw logs --tail 100` |

## 总结

1. **Agent 内部**使用工具 API，**终端**使用 CLI 命令
2. CLI 命令中，`config set` 比 `config patch` 更直接
3. JSON 参数需要正确转义或使用 JSON5 语法
4. 配置更改后需要重启网关生效
5. 始终验证配置是否正确应用

---
*文档创建时间：2026-03-16 01:36*
*测试环境：OpenClaw 2026.3.7*
*已验证命令：`openclaw config set bindings`*