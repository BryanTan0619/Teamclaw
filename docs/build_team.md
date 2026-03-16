# Build Team via CLI (Quick Reference)

> This document provides a quick reference for building a team using TeamClaw CLI, focusing on core commands without trial-and-error details.

---

## 1. Prerequisites

- TeamClaw services must be running (Agent, Scheduler, OASIS, Frontend)
- Check service status:
  ```bash
  bash selfskill/scripts/run.sh status
  ```
- Default ports: Agent(51200), Scheduler(51201), OASIS(51202), Frontend(51209)

---

## 2. Team Management

### 2.1 Create a Team

```bash
uv run scripts/cli.py teams create --team-name <TEAM_NAME>
```

Example:
```bash
uv run scripts/cli.py teams create --team-name demo_team
```

### 2.2 List All Teams

```bash
uv run scripts/cli.py teams list
```

### 2.3 View Team Details

```bash
uv run scripts/cli.py teams show --team-name <TEAM_NAME>
```

### 2.4 View Team Members

```bash
uv run scripts/cli.py teams members --team-name <TEAM_NAME>
```

Output example:
```
Team Name: demo_team
Members (1):
- name: my_new_agent, global_name: my_new_agent, type: ext
```

---

## 3. Agent Management

TeamClaw supports **3 types** of agents: Internal, OpenClaw, and External.

### 3.1 Internal Agent (Lightweight)

**Add an Internal Agent:**
```bash
uv run scripts/cli.py internal-agents add \
  --team <TEAM_NAME> \
  --data '{"session":"<SESSION_ID>","meta":{"name":"<AGENT_NAME>","tag":"<TAG>"}}'
```

Example - Add a creative expert:
```bash
uv run scripts/cli.py internal-agents add \
  --team demo_team \
  --data '{"session":"creative_s1","meta":{"name":"创意专家","tag":"creative"}}'
```

**List Internal Agents in a Team:**
```bash
uv run scripts/cli.py internal-agents list --team <TEAM_NAME>
```

**Update an Internal Agent:**
```bash
uv run scripts/cli.py internal-agents update \
  --sid <SESSION_ID> --team <TEAM_NAME> \
  --data '{"meta":{"name":"<NEW_NAME>"}}'
```

**Delete an Internal Agent:**
```bash
uv run scripts/cli.py internal-agents delete \
  --sid <SESSION_ID> --team <TEAM_NAME>
```

### 3.2 OpenClaw Agent

**Add an OpenClaw Agent:**
```bash
uv run scripts/cli.py openclaw add --data '{"name":"<BOT_NAME>"}'
```

### 3.3 External Agent (API-based)

**Add an External Member:**
```bash
uv run scripts/cli.py teams add-ext-member \
  --team-name <TEAM_NAME> \
  --data '{
    "name": "<MEMBER_NAME>",
    "global_name": "<GLOBAL_NAME>",
    "type": "external",
    "meta": {
      "description": "<DESCRIPTION>",
      "emoji": "<EMOJI>",
      "disabled": false
    }
  }'
```

**Note**: 
- `name` and `global_name` are required fields. Keep them consistent to point to the same entity.
- **Important**: When adding an OpenClaw agent, the `tag` field should be set to `"openclaw"` (recommended). This allows the system to correctly identify and route requests to the appropriate ACP (Agent Communication Protocol) handler. Other possible values include `codex`, but `openclaw` is the recommended tag for OpenClaw agents.

Example (adding OpenClaw agent `my_new_agent` to a team):
```bash
uv run scripts/cli.py teams add-ext-member \
  --team-name demo_team \
  --data '{
    "name": "my_new_agent",
    "global_name": "my_new_agent",
    "type": "external",
    "tag": "openclaw",
    "meta": {
      "description": "My newly created OpenClaw agent for testing",
      "emoji": "🤖",
      "disabled": false
    }
  }'
```

---

## 4. Create Custom Expert

When public experts don't meet your needs, you can create custom experts for your team.

### 4.1 Create a Custom Expert

**Command:**
```bash
uv run scripts/cli.py experts add \
  --tag <EXPERT_TAG> \
  --expert-name "<EXPERT_DISPLAY_NAME>" \
  --persona "<PERSONA_DESCRIPTION>" \
  --temperature <TEMPERATURE_VALUE> \
  [--team <TEAM_NAME>]
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--tag` | Yes | Unique identifier for the expert (e.g., `coder`, `architect`) |
| `--expert-name` | Yes | Display name with emoji (e.g., `"💻 代码专家"`) |
| `--persona` | Yes | System prompt defining the expert's role, skills, and behavior |
| `--temperature` | Yes | Creativity level (0.0-1.0), lower = more deterministic |
| `--team` | No | Associate expert with a specific team (optional) |

**Example - Create a coder expert:**
```bash
uv run scripts/cli.py experts add \
  --tag coder \
  --expert-name "💻 代码专家" \
  --persona "You are an expert programmer proficient in multiple programming languages. You write clean, efficient, and well-documented code. You follow best practices, design patterns, and coding standards. You can debug complex issues, optimize performance, and provide code reviews." \
  --temperature 0.3
```

**Example - Create an architect expert for a specific team:**
```bash
uv run scripts/cli.py experts add \
  --tag architect \
  --expert-name "🏗️ 架构师" \
  --persona "You are an experienced software architect with deep expertise in system design, microservices, cloud-native architecture, and scalability patterns. You provide high-level technical guidance and help teams make informed decisions about technology stacks." \
  --temperature 0.4 \
  --team demo_team
```

### 4.2 Add Custom Expert to Team

After creating a custom expert, add it as an Internal Agent:

```bash
uv run scripts/cli.py internal-agents add \
  --team <TEAM_NAME> \
  --data '{"session":"<SESSION_ID>","meta":{"name":"<AGENT_NAME>","tag":"<EXPERT_TAG>"}}'
```

**Example:**
```bash
uv run scripts/cli.py internal-agents add \
  --team demo_team \
  --data '{"session":"architect_s1","meta":{"name":"🏗️ 架构师","tag":"architect"}}'
```

---

## 6. View Public Expert List

```bash
uv run scripts/cli.py experts list
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

## 7. Complete Workflow Example

Below is a complete example of building a team from scratch:

```bash
# Step 1: Create a new team
uv run scripts/cli.py teams create --team-name demo_team

# Step 2: View available public experts
uv run scripts/cli.py experts list

# Step 3: Add Internal Agent (creative expert)
uv run scripts/cli.py internal-agents add \
  --team demo_team \
  --data '{"session":"creative_s1","meta":{"name":"创意专家","tag":"creative"}}'

# Step 4: Add Internal Agent (critical expert)
uv run scripts/cli.py internal-agents add \
  --team demo_team \
  --data '{"session":"critical_s1","meta":{"name":"批判专家","tag":"critical"}}'

# Step 5: Add External Member (OpenClaw agent)
uv run scripts/cli.py teams add-ext-member \
  --team-name demo_team \
  --data '{
    "name": "my_new_agent",
    "global_name": "my_new_agent",
    "type": "external",
    "meta": {
      "description": "My newly created OpenClaw agent for testing",
      "emoji": "🤖",
      "disabled": false
    }
  }'

# Step 6: Verify team members
uv run scripts/cli.py teams members --team-name demo_team
```

---

## 8. Tips & Notes

- **Team name duplication**: If a team name already exists, the create command will report an error. Use `teams list` to check first.
- **Tag matching**: When adding public experts as Internal Agents, the `tag` field must match the expert's tag exactly (e.g., `creative`, `critical`).
- **Session ID**: Each Internal Agent in a team needs a unique `session` ID. Use descriptive names like `creative_s1` for easy identification.
- **Multiple agent types**: A single team can contain a mix of Internal, OpenClaw, and External agents.
- **Required fields for External Members**: `name` and `global_name` are required. Keep them consistent to point to the same entity.

---

## 8. Summary

The core workflow for building a TeamClaw team using CLI is:
**Create Team → Add Members (Internal/OpenClaw/External) → Verify**.

All operations are based on `scripts/cli.py`, ensure execution under `uv run` environment.
