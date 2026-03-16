# Build Team Experience Guide

This document records the complete workflow for building a team in TeamClaw, including team creation, viewing public experts, and adding agents to a team.

---

## 1. Prerequisites

- TeamClaw services must be running (Agent, Scheduler, OASIS, Frontend)
- Check service status:
  ```bash
  bash selfskill/scripts/run.sh status
  ```
- Default ports: Agent(51200), Scheduler(51201), OASIS(51202), Frontend(51209)

---

## 2. Create a Team

### Via CLI

```bash
uv run scripts/cli.py -u <username> teams create --team-name <team_name>
```

Example:
```bash
uv run scripts/cli.py -u Xavier_01 teams create --team-name team5
```

### Via Web UI

Visit `http://127.0.0.1:51209`, click **"➕ 新建团队"** button.

### Via API

```bash
curl -X POST http://127.0.0.1:51209/teams -H 'Content-Type: application/json' -d '{"team": "<team_name>"}'
```

### List All Teams

```bash
uv run scripts/cli.py -u <username> teams list
```

---

## 3. View Public Expert List

```bash
uv run scripts/cli.py -u <username> experts list
```

### Core Public Experts (10)

| Name | Tag |
|------|-----|
| 🎨 创意专家 | `creative` |
| 🔍 批判专家 | `critical` |
| 📊 数据分析师 | `data` |
| 🎯 综合顾问 | `synthesis` |
| 📈 经济学家 | `economist` |
| ⚖️ 法学家 | `lawyer` |
| 💰 成本限制者 | `cost_controller` |
| 📊 收益规划者 | `revenue_planner` |
| 🚀 创新企业家 | `entrepreneur` |
| 🧑 普通人 | `common_person` |

### Agency Professional Experts (68)

| Category | Count | Examples |
|----------|-------|----------|
| 🎨 Design | 8 | Brand Guardian, UI Designer, UX Architect, Image Prompt Engineer... |
| ⚙️ Engineering | 11 | Senior Developer, Backend Architect, Frontend Developer, DevOps Automator, AI Engineer... |
| 📢 Marketing | 11 | Content Creator, Growth Hacker, TikTok Strategist, WeChat Official Account Manager... |
| 📦 Product | 4 | Sprint Prioritizer, Trend Researcher, Feedback Synthesizer, Behavioral Nudge Engine |
| 📋 Project Management | 5 | Senior Project Manager, Studio Producer, Experiment Tracker... |
| 🥽 Spatial Computing | 6 | visionOS Spatial Engineer, XR Immersive Developer, Metal Engineer... |
| 🔬 Specialist | 9 | Agents Orchestrator, Developer Advocate, Data Analytics Reporter... |
| 🛡️ Support | 6 | Finance Tracker, Legal Compliance Checker, Infrastructure Maintainer... |
| 🧪 Testing | 8 | API Tester, Performance Benchmarker, Accessibility Auditor... |

### Custom Experts (8)

| Name | Tag |
|------|-----|
| 场景段描述者 | `VLM` |
| 日志阅读者LLM | `LLM-log` |
| 时序判别器 | `time-series` |
| 用户画像阅读者 | `statistic` |
| 信息总结器 | `summaryfor4` |
| 子段阅读者 | `subsegment` |
| 搜索者 | `searcher` |
| 任务发布者 | `tasksender` |

---

## 4. Add Agents to a Team

TeamClaw supports **3 types** of agents:

### 4.1 Internal Agent (Lightweight)

**Add:**
```bash
uv run scripts/cli.py -u <username> internal-agents add \
  --team <team_name> \
  --data '{"session":"<session_id>","meta":{"name":"<agent_name>","tag":"<tag>"}}'
```

Example - Add a creative expert and a critical expert to team5:
```bash
# Add creative expert
uv run scripts/cli.py -u Xavier_01 internal-agents add \
  --team team5 \
  --data '{"session":"creative_s1","meta":{"name":"创意专家","tag":"creative"}}'

# Add critical expert
uv run scripts/cli.py -u Xavier_01 internal-agents add \
  --team team5 \
  --data '{"session":"critical_s1","meta":{"name":"批判专家","tag":"critical"}}'
```

**List agents in a team:**
```bash
uv run scripts/cli.py -u <username> internal-agents list --team <team_name>
```

**Update an agent:**
```bash
uv run scripts/cli.py -u <username> internal-agents update \
  --sid <session_id> --team <team_name> \
  --data '{"meta":{"name":"<new_name>"}}'
```

**Delete an agent:**
```bash
uv run scripts/cli.py -u <username> internal-agents delete \
  --sid <session_id> --team <team_name>
```

### 4.2 OpenClaw Agent

Requires OpenClaw to be installed and configured first:
```bash
uv run scripts/cli.py openclaw add --data '{"name":"<bot_name>"}'
```

### 4.3 External Agent (API-based)

Add via Web UI:
1. Go to the team page at `http://127.0.0.1:51209`
2. Click **"➕ 添加成员"**
3. Select the **External** tab
4. Fill in the API endpoint and configuration
5. Click create

---

## 5. Complete Workflow Example

Below is a complete example of building a team from scratch:

```bash
# Step 1: Create a new team
uv run scripts/cli.py -u Xavier_01 teams create --team-name team5

# Step 2: View available public experts
uv run scripts/cli.py -u Xavier_01 experts list

# Step 3: Add creative expert to the team
uv run scripts/cli.py -u Xavier_01 internal-agents add \
  --team team5 \
  --data '{"session":"creative_s1","meta":{"name":"创意专家","tag":"creative"}}'

# Step 4: Add critical expert to the team
uv run scripts/cli.py -u Xavier_01 internal-agents add \
  --team team5 \
  --data '{"session":"critical_s1","meta":{"name":"批判专家","tag":"critical"}}'

# Step 5: Verify team members
uv run scripts/cli.py -u Xavier_01 internal-agents list --team team5
```

---

## 6. Tips & Notes

- **Team name duplication**: If a team name already exists, the create command will report an error. Use `teams list` to check first.
- **Tag matching**: When adding public experts as Internal Agents, the `tag` field must match the expert's tag exactly (e.g., `creative`, `critical`).
- **Session ID**: Each agent in a team needs a unique `session` ID. Use descriptive names like `creative_s1` for easy identification.
- **Web UI alternative**: All CLI operations can also be performed through the Web UI at `http://127.0.0.1:51209`.
- **Multiple agent types**: A single team can contain a mix of Internal, OpenClaw, and External agents.
