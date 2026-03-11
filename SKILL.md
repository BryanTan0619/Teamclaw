---
name: "TeamClaw"
description: "A high-performance Agent subsystem for complex multi-agent orchestration. It provides a visual workflow canvas (OASIS) to coordinate OpenClaw agents, automated computer use tasks, and real-time monitoring via a dedicated Web UI. Supports Telegram/QQ bot integrations and Cloudflare Tunnel for secure remote access."
user-invokable: true
compatibility:
  - "deepseek"
  - "openai"
  - "gemini"
  - "claude"
  - "anthropic"
  - "ollama"


argument-hint: "[BEFORE FIRST LAUNCH - MUST CONFIGURE] (1) LLM_API_KEY: your LLM provider API key (required). (2) LLM_BASE_URL: the base URL of your LLM provider (e.g. https://api.deepseek.com). (3) LLM_MODEL: the model name to use; if the user does NOT provide one, the agent MUST discover the newest callable chat model for the supplied API key by querying the provider and validating it with a real request before writing LLM_MODEL. [NETWORK] Requires outbound access for LLM/TTS APIs. Uses ports 51200-51209. [BOTS] Optional integrations: TELEGRAM_BOT_TOKEN, QQ_APP_ID, QQ_BOT_SECRET. [TUNNEL] Set PUBLIC_DOMAIN to enable secure Cloudflare Tunneling. Public deployment is entirely user-controlled (start-tunnel / stop-tunnel / frontend toggle). CRITICAL: Agent MUST NOT download cloudflared or start the tunnel unless the user EXPLICITLY requests it. Agent retrieves public URL via get_publicnet_info() tool (queries GET /publicnet/info), never reads .env directly."

metadata:
  version: "1.0.2"
  github: "https://github.com/Avalon-467/Teamclaw"
  ports:
    agent: 51200
    scheduler: 51201
    oasis: 51202
    frontend: 51209
  auth_methods:
    - "user_password"
    - "internal_token"
    - "chatbot_whitelist"
  integrations:
    - "openclaw"
    - "telegram"
    - "qq"
    - "cloudflare_tunnel"
---

# TeamClaw  Agent Subsystem Skill

https://github.com/Avalon-467/Teamclaw


## Introduction

TeamClaw is an OpenClaw-like multi-agent sub-platform with a built-in lightweight agent (similar to OpenClaw's), featuring computer use capabilities and social platform integrations (e.g., Telegram). It can run independently without blocking the main agent, or be directly controlled by an OpenClaw agent to orchestrate the built-in OASIS collaboration platform. It also supports exposing the frontend to the public internet via Cloudflare, enabling remote visual multi-agent workflow programming from mobile devices or any browser.

TeamClaw is a versatile AI Agent service providing:

- **Conversational Agent**: A LangGraph-based multi-tool AI assistant supporting streaming/non-streaming conversations
- **OASIS Forum**: A multi-expert parallel discussion/execution engine for orchestrating multiple agents
- **Scheduled Tasks**: An APScheduler-based task scheduling center
- **Frontend Web UI**: A complete chat interface

## Skill Scripts

All scripts are located in `selfskill/scripts/`, invoked uniformly via the `run.sh` entry point, **all non-interactive**.

```
selfskill/scripts/
 run.sh          # Main entry (start/stop/status/setup/add-user/configure)
 adduser.py      # Non-interactive user creation
 configure.py    # Non-interactive .env configuration management
```

## Quick Start

All commands are executed in the project root directory.

**Three-step launch flow: `setup` → `configure` → `start`**

### 1. First Deployment

```bash
# Install dependencies
bash selfskill/scripts/run.sh setup

# Check and install OpenClaw (recommended — enables visual workflow orchestration)
bash selfskill/scripts/run.sh check-openclaw
# If OpenClaw is not installed, this will:
#   1. Check if Node.js ≥ 22 is available
#   2. ASK the user for confirmation before installing
#   3. Run: npm install -g openclaw@latest --ignore-scripts
#      (--ignore-scripts avoids node-llama-cpp build failure when cmake is missing)
#   4. Verify openclaw is in PATH (npm global bin may need to be added)
#   5. Guide user to run: openclaw onboard (interactive wizard for initial setup)
#   6. Auto-detect OpenClaw gateway port and configure OPENCLAW_API_URL
# If OpenClaw is already installed, it will show the current version and auto-configure.

# Initialize configuration file
bash selfskill/scripts/run.sh configure --init

# Configure LLM (required — at minimum LLM_API_KEY and LLM_BASE_URL)
# If the user specifies a model name, set all three:
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat

# If the user does NOT specify a model name, set key + URL, then auto-detect:
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com
bash selfskill/scripts/run.sh auto-model
# → Queries /v1/models API, prints available models for the agent to choose
# Then set the chosen model:
# bash selfskill/scripts/run.sh configure LLM_MODEL <chosen-model>

# ⚠️ Create user account (REQUIRED — without this you CANNOT log in to the Web UI or call API)
# ⚠️ AGENT: You MUST ASK the user for their desired username and password BEFORE running this command!
#    Do NOT use default/example credentials like "admin/admin123" or "system/MySecurePass123".
#    Example prompt: "Please provide the username and password you'd like to use for the TeamClaw Web UI."
bash selfskill/scripts/run.sh add-user <username> <password>
```

> ⚠️ **You MUST create at least one user account before starting the service!**
> - **AGENT MUST ask the user** for their preferred username and password. Do NOT invent credentials.
> - The Web UI login page requires username + password.
> - All API calls require `Authorization: Bearer <user_id>:<password>` (or `INTERNAL_TOKEN:<user_id>`).
> - If you skip this step, you will be locked out of the entire system.
> - You can create multiple users. The first argument is the username, the second is the password.

### 2. Start / Stop / Status

```bash
bash selfskill/scripts/run.sh start     # Start in background
bash selfskill/scripts/run.sh status    # Check status
bash selfskill/scripts/run.sh stop      # Stop service
```

### 3. Chatbot (Telegram/QQ) — Startup Differences

| Component | How it starts | Configuration needed | Notes |
|-----------|--------------|---------------------|-------|
| **Telegram Bot** | **Requires manual setup** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS` in `.env` | `launcher.py` calls `chatbot/setup.py` which has an **interactive menu** (`input()`). In headless/background mode this will **block**. To avoid blocking, configure the bot tokens in `.env` beforehand and start the bot separately: `nohup python chatbot/telegrambot.py > logs/telegrambot.log 2>&1 &` |
| **QQ Bot** | **Requires manual setup** | `QQ_APP_ID`, `QQ_BOT_SECRET`, `QQ_BOT_USERNAME` in `.env` | Same as Telegram — interactive setup will block in headless mode. Start separately: `nohup python chatbot/QQbot.py > logs/qqbot.log 2>&1 &` |

> ⚠️ **Important for Agent/headless usage**: The `chatbot/setup.py` script contains interactive `input()` prompts. When `launcher.py` runs in the background (via `run.sh start`), if `chatbot/setup.py` exists it will be called and **block indefinitely** waiting for user input. To prevent this:
> 1. Either remove/rename `chatbot/setup.py` before starting, OR
> 2. Pre-configure all bot tokens in `.env` and start bots independently (bypassing `setup.py`).

### 4. Configuration Management

```bash
# View current configuration (sensitive values masked)
bash selfskill/scripts/run.sh configure --show

# Set a single item
bash selfskill/scripts/run.sh configure PORT_AGENT 51200

# Batch set
bash selfskill/scripts/run.sh configure --batch TTS_MODEL=gemini-2.5-flash-preview-tts TTS_VOICE=charon
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `LLM_API_KEY` | LLM API key (**required**) |  |
| `LLM_BASE_URL` | LLM API URL | `https://api.deepseek.com` |
| `LLM_MODEL` | Model name | `deepseek-chat` |
| `LLM_PROVIDER` | Provider (google/anthropic/deepseek/openai, auto-inferred) | Auto |
| `LLM_VISION_SUPPORT` | Vision support (auto-inferred) | Auto |
| `PORT_AGENT` | Agent main service port (optional, has default) | `51200` |
| `PORT_SCHEDULER` | Scheduled task port (optional, has default) | `51201` |
| `PORT_OASIS` | OASIS forum port (optional, has default) | `51202` |
| `PORT_FRONTEND` | Web UI port (optional, has default) | `51209` |
| `TTS_MODEL` | TTS model (optional) |  |
| `TTS_VOICE` | TTS voice (optional) |  |
| `INTERNAL_TOKEN` | Internal communication secret (**auto-generated on first startup, no manual config needed**) | Auto |

## Ports & Services

| Port | Service |
|------|---------|
| 51200 | AI Agent main service |
| 51201 | Scheduled tasks |
| 51202 | OASIS forum |
| 51209 | Web UI |

## API Authentication

### Method 1: User Authentication

```
Authorization: Bearer <user_id>:<password>
```

### Method 2: Internal Token (for inter-service calls, recommended)

```
Authorization: Bearer <INTERNAL_TOKEN>:<user_id>
```

`INTERNAL_TOKEN` is auto-generated on first startup; view it via `configure --show-raw`.

## Core API

**Base URL**: `http://127.0.0.1:51200`

### Chat (OpenAI-compatible)

```
POST /v1/chat/completions
Authorization: Bearer <token>

{"model":"mini-timebot","messages":[{"role":"user","content":"Hello"}],"stream":true,"session_id":"my-session"}
```

### System Trigger (internal call)

```
POST /system_trigger
X-Internal-Token: <INTERNAL_TOKEN>

{"user_id":"system","text":"Please execute a task","session_id":"task-001"}
```

### Cancel Session

```
POST /cancel

{"user_id":"<user_id>","session_id":"<session_id>"}
```


## OASIS Four Operating Modes (Default: Discussion Mode)

> 📖 **Dedicated OASIS usage guide (especially for OpenClaw agent integration)**: [OASIS_GUIDE.md](./OASIS_GUIDE.md)

> The "four modes" are two orthogonal switches:
> - **Discussion vs Execution**: Determines whether expert output is "forum-style discussion/voting" or "workflow-style execution/deliverables".
> - **Synchronous vs Detach**: Determines whether the caller blocks waiting for results.

### 1) Discussion Mode vs Execution Mode

**Discussion Mode (discussion=true, default)**
- Purpose: Multiple experts provide different perspectives, pros/cons analysis, clarify disputes, and can form consensus.
- Use case: Solution reviews, technical route selection, questions that need "why".

**Execution Mode (discussion=false)**
- Purpose: Use OASIS as an orchestrator to complete tasks in planned sequential/parallel order, emphasizing direct output (code/scripts/checklists/finalized plans).
- Use case: Delivery tasks with clear objectives that don't need debate.

### 2) Synchronous Mode vs Detach Mode

**Detach (detach=true, default)**
- Behavior: Returns `topic_id` immediately, continues running/discussing in the background; later use `check_oasis_discussion(topic_id)` to track progress and results.
- Use case: Most tasks, especially multi-round/multi-expert/long-running/tool-calling tasks.

**Synchronous (detach=false)**
- Behavior: After calling `post_to_oasis`, waits for completion and returns the final result directly.
- Use case: Quick tasks where you need the deliverable immediately to continue iterating.

### 3) Auto-selection Rules (Recommended Default Strategy)

When not explicitly specified, the following default strategy is recommended:

1. **Default = Discussion + Detach**
   - `discussion=true`
   - `detach=true`

2. Switch to **Execution Mode** when these signals appear:
   - "Give me the final version / copy-pasteable / executable script / just conclusions no discussion"
   - "Generate SOP / checklist / table step by step and finalize"

3. Switch to **Synchronous Mode** when these signals appear:
   - "Wait for the result / I need it now / give me the answer directly"
   - Quick single-round tasks where the deliverable is needed immediately

### 4) Four Combinations Quick Reference

| Combination | Parameters | Returns | Use Case |
|---|---|---|---|
| Discussion + Detach **(default)** | discussion=true, detach=true | topic_id, check later | Decision/review/collect opinions |
| Discussion + Sync | discussion=true, detach=false | See discussion & conclusion on the spot | Quick discussion needing immediate result |
| Execution + Detach | discussion=false, detach=true | topic_id, check later | Long execution/complex pipelines |
| Execution + Sync | discussion=false, detach=false | Direct deliverables | Generate code/plans/checklists |


## OASIS Four Agent Types

OASIS supports **four types of agents**, distinguished by the `name` format in `schedule_yaml`:

| # | Type | Name Format | Engine Class | Description |
|---|------|-------------|--------------|-------------|
| 1 | **Direct LLM** | `tag#temp#N` | `ExpertAgent` | Stateless single LLM call. Each round reads all posts  one LLM call  publish + vote. No cross-round memory. `tag` maps to preset expert name/persona, `N` is instance number (same expert can have multiple copies). |
| 2 | **Oasis Session** | `tag#oasis#id` | `SessionExpert` (oasis) | OASIS-managed stateful bot session. `tag` maps to preset expert, persona injected as system prompt on first round. Bot retains conversation memory across rounds (incremental context). `id` can be any string; new ID auto-creates session on first use. |
| 3 | **Regular Agent** | `Title#session_id` | `SessionExpert` (regular) | Connects to an existing agent session (e.g., `Assistant#default`, `Coder#my-project`). No identity injectionthe session's own system prompt defines the agent. Suitable for bringing personal bot sessions into discussions. |
| 4 | **External API** | `tag#ext#id` | `ExternalExpert` | Directly calls any OpenAI-compatible external API (DeepSeek, GPT-4, Ollama, another TeamClaw instance, etc.). Does not go through local agent. External service assumed stateful. Supports custom request headers via YAML `headers` field. | Classic use case: connecting to OpenClaw agent |

### Session ID Format

```
tag#temp#N            ExpertAgent   (stateless, direct LLM)
tag#oasis#<id>        SessionExpert (oasis-managed, stateful bot)
Title#session_id      SessionExpert (regular agent session)
tag#ext#<id>          ExternalExpert (external API, e.g. OpenClaw agent)
```

**Special Suffix:**
- Appending `#new` to the end of any session name forces creation of a **brand new session** (ID replaced with random UUID, ensuring no reuse):
  - `creative#oasis#abc#new`  `#new` stripped, ID replaced with UUID
  - `Assistant#my-session#new`  Same processing

**Oasis Session Conventions:**
- Oasis sessions are identified by `#oasis#` in `session_id` (e.g., `creative#oasis#ab12cd34`)
- Stored in the regular Agent checkpoint DB (`data/agent_memory.db`), no separate storage
- Auto-created on first use, no pre-creation needed
- `tag` part maps to preset expert configuration to find persona

### YAML Example

```yaml
version: 1
plan:
  # Type 1: Direct LLM (stateless, fast)
  - expert: "creative#temp#1"
  - expert: "critical#temp#2"

  # Type 2: Oasis session (stateful, with memory)
  - expert: "data#oasis#analysis01"
  - expert: "synthesis#oasis#new#new"   # Force new session

  # Type 3: Regular agent session (your existing bot)
  - expert: "Assistant#default"
  - expert: "Coder#my-project"

  # Type 4: External API (DeepSeek, GPT-4, etc.)
  - expert: "deepseek#ext#ds1"

  # Type 4: OpenClaw External API (local Agent service)
  # When model matches "agent:<name>:<session>", CLI is used first:
  #   openclaw agent --agent "main" --session-id "test1" --message "..."
  # Falls back to HTTP API if CLI unavailable
  - expert: "coder#ext#oc1"
    api_url: "http://127.0.0.1:23001/v1/chat/completions"
    api_key: "****"
    model: "agent:main:test1"    # agent:<agent_name>:<session> → triggers CLI priority

  # Parallel execution
  - parallel:
      - expert: "creative#temp#1"
        instruction: "Analyze from innovation perspective"
      - expert: "critical#temp#2"
        instruction: "Analyze from risk perspective"

  # All experts speak + manual injection
  - all_experts: true
  - manual:
      author: "Moderator"
      content: "Please focus on feasibility"
```

### DAG Mode — Dependency-Driven Parallel Execution

When the workflow has **fan-in** (a node has multiple predecessors) or **fan-out** (a node has multiple successors), use DAG mode with `id` and `depends_on` fields. The engine maximizes parallelism — each node starts as soon as all its dependencies are satisfied.

**DAG YAML Example:**

```yaml
version: 1
repeat: false
plan:
  - id: research
    expert: "creative#temp#1"                # Root — starts immediately
  - id: analysis
    expert: "critical#temp#1"                # Root — runs in PARALLEL with research
  - id: synthesis
    expert: "synthesis#temp#1"
    depends_on: [research, analysis]         # Fan-in: waits for BOTH to complete
  - id: review
    expert: "data#temp#1"
    depends_on: [synthesis]                  # Runs after synthesis
```

**DAG Rules:**
- Every step **must** have a unique `id` field.
- `depends_on` is a list of step ids that must complete before this step starts. Omit for root nodes.
- The graph **must** be acyclic (no circular dependencies).
- Steps with no dependency relationship run in parallel automatically.
- The visual Canvas auto-detects fan-in/fan-out and generates DAG format.
- `manual` steps can also have `id`/`depends_on`.

### External API (Type 4) Detailed Configuration

Type 4 external agents support additional configuration fields in YAML steps:

```yaml
version: 1
plan:
  - expert: "#ext#analyst"
    api_url: "https://api.deepseek.com"          # Required: External API base URL (auto-completes to /v1/chat/completions)
    api_key: "****"                               # Optional: API key for the external service
    model: "deepseek-chat"                        # Optional: Model name, default gpt-3.5-turbo
    headers:                                      # Optional: Custom HTTP headers (key-value dict)
      X-Custom-Header: "value"
```

> 🔒 **API Key Security**: Set `api_key: "****"` (or omit it) to use a masked key. Plaintext keys also work (backward compatible).
**Configuration Field Description:**

| Field | Required | Description |
|-------|----------|-------------|
| `api_url` |  | External API address, auto-completes path to `/v1/chat/completions` |
| `api_key` |  | API key for the external service. Use `****` mask or plaintext. |
| `model` |  | Default `gpt-3.5-turbo` |
| `headers` |  | Any key-value dict, merged into HTTP request headers |

**OpenClaw-specific Configuration:**

OpenClaw is a locally running OpenAI-compatible Agent service. The frontend orchestration panel will **auto-fill** `api_url` when dragging in an OpenClaw expert, no manual input needed.

> ** Note:**
> - **Path Convention**: `./agents/main/sessions/sessions.json` is a common path structure for OpenClaw agent sessions.
> - **Session Management**: Accessing session information is a necessary process for OpenClaw agent orchestration, enabling multi-agent workflow coordination and visual canvas operations.

**OpenClaw `model` Field Format:**

```
agent:<agent_name>:<session_name>
```

- `agent_name`: Agent name in OpenClaw, usually `main`
- `session_name`: Session name, e.g., `test1`, `default`, etc. **You can enter a non-existent session name to auto-create**

Examples:
- `agent:main:default`  Use main agent's default session
- `agent:main:test1`  Use main agent's test1 session (auto-created if not exists)
- `agent:main:code-review`  Use main agent's code-review session

**OpenClaw CLI Priority:**

When the `model` field matches `agent:<agent_name>:<session_id>`, the system **automatically** uses the OpenClaw CLI as the preferred invocation method:
```
openclaw agent --agent "<agent_name>" --session-id "<session_id>" --message "<message>"
```
If the `openclaw` CLI is not available in PATH or the CLI call fails, it **falls back** to the standard HTTP API (using the `api_url` and `x-openclaw-session-key` header). This ensures both maximum reliability and simplicity — no extra headers needed when CLI is available.

**Request Header Assembly Logic (HTTP fallback):**
Final request headers = `Content-Type: application/json` + `Authorization: Bearer <api_key>` (if present) + all key-value pairs from YAML `headers`.

**`x-openclaw-session-key` — Deterministic OpenClaw Session Routing (HTTP mode):**

When CLI is unavailable and falling back to HTTP API, the `x-openclaw-session-key` HTTP header is the **key mechanism** for routing requests to a specific, deterministic OpenClaw session. Without this header, OpenClaw may not correctly associate the request with the intended session.

- The frontend orchestration panel **automatically** sets this header when you drag an OpenClaw session onto the canvas.
- When writing YAML manually or calling the API programmatically, you **must** include this header in the `headers` field to ensure session determinism.

```yaml
# Example: Connecting to a specific OpenClaw session
- expert: "coder#ext#oc1"
  api_url: "http://127.0.0.1:18789"
  api_key: "****"
  model: "agent:main:my-session"
  headers:
    x-openclaw-session-key: "agent:main:my-session"   # ← This header determines the exact OpenClaw session
```

> The value of `x-openclaw-session-key` should match the `model` field's session identifier (format: `agent:<agent_name>:<session_name>`). This ensures the external request is routed to the correct OpenClaw agent session, maintaining conversation continuity and state.

---

## Using OASIS Server Independently

The OASIS Server (port 51202) can be **used independently of the Agent main service**. External scripts, other services, or manual curl can directly operate all OASIS features without going through MCP tools or Agent conversations.

**Independent Use Scenarios:**
- Initiate multi-expert discussions/executions from external scripts
- Debug workflow orchestration
- Integrate OASIS as a microservice into other systems
- Manage experts, sessions, workflows, and other resources

**Prerequisites:**
- OASIS service is running (`bash selfskill/scripts/run.sh start` starts all services simultaneously)
- All endpoints use `user_id` parameter for user isolation (no Authorization header needed)

**API Overview:**

| Function | Method | Path |
|----------|--------|------|
| List experts | GET | `/experts?user_id=xxx` |
| Create custom expert | POST | `/experts/user` |
| Update/delete custom expert | PUT/DELETE | `/experts/user/{tag}` |
| List oasis sessions | GET | `/sessions/oasis?user_id=xxx` |
| Save workflow | POST | `/workflows` |
| List workflows | GET | `/workflows?user_id=xxx` |
| YAML  Layout | POST | `/layouts/from-yaml` |
| Create discussion/execution | POST | `/topics` |
| View discussion details | GET | `/topics/{topic_id}?user_id=xxx` |
| Get conclusion (blocking) | GET | `/topics/{topic_id}/conclusion?user_id=xxx&timeout=300` |
| SSE real-time stream | GET | `/topics/{topic_id}/stream?user_id=xxx` |
| Cancel discussion | DELETE | `/topics/{topic_id}?user_id=xxx` |
| List all topics | GET | `/topics?user_id=xxx` |

> These endpoints share the same backend implementation as MCP tools, ensuring consistent behavior.

---

### OASIS Discussion/Execution

```
POST http://127.0.0.1:51202/topics

{"question":"Discussion topic","user_id":"system","max_rounds":3,"discussion":true,"schedule_file":"...","schedule_yaml":"...","callback_url":"http://127.0.0.1:51200/system_trigger","callback_session_id":"my-session"}
```

Prefer using schedule_yaml to avoid repeated YAML input; this is the absolute path to the YAML workflow file, usually under /XXXXX/TeamClaw/data/user_files/username.

### Externally Participating in OASIS Server via curl (Complete Methods)

The OASIS Server (port 51202), in addition to being called by MCP tools, also supports direct curl operations for external scripts or debugging. All endpoints use `user_id` parameter for user isolation.

#### 1. Expert Management
```bash
# List all experts (public + user custom)
curl 'http://127.0.0.1:51202/experts?user_id=xinyuan'

# Create custom expert
curl -X POST 'http://127.0.0.1:51202/experts/user' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","name":"Product Manager","tag":"pm","persona":"You are an experienced product manager skilled in requirements analysis and product planning","temperature":0.7}'

# Update custom expert
curl -X PUT 'http://127.0.0.1:51202/experts/user/pm' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","persona":"Updated expert description"}'

# Delete custom expert
curl -X DELETE 'http://127.0.0.1:51202/experts/user/pm?user_id=xinyuan'
```

#### 2. Session Management
```bash
# List OASIS-managed expert sessions (sessions containing #oasis#)
curl 'http://127.0.0.1:51202/sessions/oasis?user_id=xinyuan'
```

#### 3. Workflow Management
```bash
# List user's saved workflows
curl 'http://127.0.0.1:51202/workflows?user_id=xinyuan'

# Save workflow (auto-generate layout)
curl -X POST 'http://127.0.0.1:51202/workflows' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","name":"trio_discussion","schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","description":"Trio discussion","save_layout":true}'
```

#### 4. Layout Generation
```bash
# Generate layout from YAML
curl -X POST 'http://127.0.0.1:51202/layouts/from-yaml' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","yaml_source":"version:1\nplan:\n - expert: \"creative#temp#1\"","layout_name":"trio_layout"}'
```

#### 5. Discussion/Execution
```bash
# Create discussion topic (synchronous, wait for conclusion)
curl -X POST 'http://127.0.0.1:51202/topics' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","question":"Discussion topic","max_rounds":3,"schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","discussion":true}'

# Create discussion topic (async, returns topic_id)
curl -X POST 'http://127.0.0.1:51202/topics' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","question":"Discussion topic","max_rounds":3,"schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","discussion":true,"callback_url":"http://127.0.0.1:51200/system_trigger","callback_session_id":"my-session"}'

# View discussion details
curl 'http://127.0.0.1:51202/topics/{topic_id}?user_id=xinyuan'

# Get discussion conclusion (blocking wait)
curl 'http://127.0.0.1:51202/topics/{topic_id}/conclusion?user_id=xinyuan&timeout=300'

# Cancel discussion
curl -X DELETE 'http://127.0.0.1:51202/topics/{topic_id}?user_id=xinyuan'

# List all discussion topics
curl 'http://127.0.0.1:51202/topics?user_id=xinyuan'
```

#### 6. Real-time Stream
```bash
# SSE real-time update stream (discussion mode)
curl 'http://127.0.0.1:51202/topics/{topic_id}/stream?user_id=xinyuan'
```

**Storage Locations:**
- Workflows (YAML): `data/user_files/{user}/oasis/yaml/{file}.yaml` (canvas layouts are converted from YAML in real-time, no longer stored as separate layout JSON)
- User custom experts: `data/oasis_user_experts/{user}.json`
- Discussion records: `data/oasis_topics/{user}/{topic_id}.json`

**Note:** These endpoints share the same backend implementation as MCP tools `list_oasis_experts`, `add_oasis_expert`, `update_oasis_expert`, `delete_oasis_expert`, `list_oasis_sessions`, `set_oasis_workflow`, `list_oasis_workflows`, `yaml_to_layout`, `post_to_oasis`, `check_oasis_discussion`, `cancel_oasis_discussion`, `list_oasis_topics`, ensuring consistent behavior.

## Example Configuration Reference

Below is an actual running configuration example (sensitive info redacted):

```bash
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx4c74 \
  LLM_BASE_URL=https://deepseek.com \
  LLM_MODEL=deepseek-chat \
  LLM_VISION_SUPPORT=true \
  TTS_MODEL=gemini-2.5-flash-preview-tts \
  TTS_VOICE=charon \
  PORT_AGENT=51200 \
  PORT_SCHEDULER=51201 \
  PORT_OASIS=51202 \
  PORT_FRONTEND=51209 \
  OPENAI_STANDARD_MODE=false
bash selfskill/scripts/run.sh add-user system <your-password>
```

Output after `configure --show`:

```
  PORT_SCHEDULER=51201
  PORT_AGENT=51200
  PORT_FRONTEND=51209
  PORT_OASIS=51202
  OASIS_BASE_URL=http://127.0.0.1:51202
  INTERNAL_TOKEN=f1aa****57e7          # Auto-generated, do not leak
  LLM_API_KEY=sk-7****4c74
  LLM_BASE_URL=https://deepseek.com
  LLM_MODEL=deepseek-chat
  LLM_VISION_SUPPORT=true
  TTS_MODEL=gemini-2.5-flash-preview-tts
  TTS_VOICE=charon
  OPENAI_STANDARD_MODE=false
```

> Note: `INTERNAL_TOKEN` is auto-generated on first startup; `PUBLIC_DOMAIN` is auto-written by the tunnel; no manual configuration needed.

## Typical Usage Flow

```bash
cd /home/avalon/TeamClaw

# First-time configuration
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch LLM_API_KEY=sk-xxx LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-chat
# ⚠️ ASK the user for username and password first!
bash selfskill/scripts/run.sh add-user <username> <password>

# Start
bash selfskill/scripts/run.sh start

# Call API
curl -X POST http://127.0.0.1:51200/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <username>:<password>" \
  -d '{"model":"mini-timebot","messages":[{"role":"user","content":"Hello"}],"stream":false,"session_id":"default"}'

# Stop
bash selfskill/scripts/run.sh stop
```

## Important Notes

- All skill scripts are in `selfskill/scripts/`, not affecting original project functionality
- Process management via PID files, `start` supports idempotent calls
- Do not leak `INTERNAL_TOKEN`
- Log path: `logs/launcher.log`

- Be sure to tell users how to open the visual interface and how to log in to the account for discussions
- The OpenClaw session file path can be inferred from the example path and current skill path. If you are an OpenClaw agent, be sure to complete the full OpenClaw-related configuration

---
---

# TeamClaw  Agent  Skill



## 

TeamClaw  OpenClaw  Agent  OpenClaw  Agent computer use  Telegram agent  OpenClaw agent  OASIS  Agent  Cloudflare  Agent 

TeamClaw  AI Agent 

- ** Agent** LangGraph  AI /
- **OASIS **/ Agent 
- **** APScheduler 
- ** Web UI**

## Skill 

 `selfskill/scripts/` `run.sh` ****

```
selfskill/scripts/
 run.sh          # start/stop/status/setup/add-user/configure
 adduser.py      # 
 configure.py    #  .env 
```

## 



****`setup`  `configure`  `start`

### 1. 

```bash
# 
bash selfskill/scripts/run.sh setup

# 检测并安装 OpenClaw（推荐 — 启用可视化工作流编排）
bash selfskill/scripts/run.sh check-openclaw
# 如果 OpenClaw 未安装，此命令会：
#   1. 检测 Node.js ≥ 22 是否可用
#   2. 询问用户确认后再安装
#   3. 执行: npm install -g openclaw@latest --ignore-scripts
#     （--ignore-scripts 避免 node-llama-cpp 因缺少 cmake 编译失败）
#   4. 验证 openclaw 在 PATH 中可用（npm 全局 bin 路径可能需要手动添加）
#   5. 引导用户运行: openclaw onboard（交互式向导完成初始配置）
#   6. 自动探测 OpenClaw gateway 端口并配置 OPENCLAW_API_URL
# 如果 OpenClaw 已安装，会显示版本信息并自动配置。

# 
bash selfskill/scripts/run.sh configure --init

#  LLM（至少需要 LLM_API_KEY 和 LLM_BASE_URL）
# 如果用户指定了模型名称，直接设置三项：
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat

# 如果用户没有指定模型名称，设置 key + URL 后自动检测：
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com
bash selfskill/scripts/run.sh auto-model
# → 查询 /v1/models 接口，打印可用模型列表，由 agent 选择
# 然后设置选定的模型：
# bash selfskill/scripts/run.sh configure LLM_MODEL <选定的模型>

# 
# ⚠️ AGENT：执行此命令前，必须先询问用户想要的用户名和密码！
#    禁止使用默认凭据（如 admin/admin123 或 system/MySecurePass123）。
#    示例提示："请告诉我你想为 TeamClaw Web UI 设置的用户名和密码。"
bash selfskill/scripts/run.sh add-user <username> <password>
```

### 2. //

```bash
bash selfskill/scripts/run.sh start     # 
bash selfskill/scripts/run.sh status    # 
bash selfskill/scripts/run.sh stop      # 
```

### 3. 

```bash
# 
bash selfskill/scripts/run.sh configure --show

# 
bash selfskill/scripts/run.sh configure PORT_AGENT 51200

# 
bash selfskill/scripts/run.sh configure --batch TTS_MODEL=gemini-2.5-flash-preview-tts TTS_VOICE=charon
```

## 

|  |  |  |
|--------|------|--------|
| `LLM_API_KEY` | LLM API **** |  |
| `LLM_BASE_URL` | LLM API  | `https://api.deepseek.com` |
| `LLM_MODEL` |  | `deepseek-chat` |
| `LLM_PROVIDER` | google/anthropic/deepseek/openai |  |
| `LLM_VISION_SUPPORT` |  |  |
| `PORT_AGENT` | Agent 主服务端口（可选，有默认值） | `51200` |
| `PORT_SCHEDULER` | 定时任务端口（可选，有默认值） | `51201` |
| `PORT_OASIS` | OASIS 论坛端口（可选，有默认值） | `51202` |
| `PORT_FRONTEND` | Web UI 端口（可选，有默认值） | `51209` |
| `TTS_MODEL` | TTS 模型（可选） |  |
| `TTS_VOICE` | TTS 声音（可选） |  |
| `INTERNAL_TOKEN` | 内部通信密钥（**首次启动自动生成，无需手动配置**） | 自动 |

## 

|  |  |
|------|------|
| 51200 | AI Agent  |
| 51201 |  |
| 51202 | OASIS  |
| 51209 | Web UI |

## API 

###  1

```
Authorization: Bearer <user_id>:<password>
```

###  2 Token

```
Authorization: Bearer <INTERNAL_TOKEN>:<user_id>
```

`INTERNAL_TOKEN`  `configure --show-raw` 

##  API

**Base URL**: `http://127.0.0.1:51200`

### OpenAI 

```
POST /v1/chat/completions
Authorization: Bearer <token>

{"model":"mini-timebot","messages":[{"role":"user","content":""}],"stream":true,"session_id":"my-session"}
```

### 

```
POST /system_trigger
X-Internal-Token: <INTERNAL_TOKEN>

{"user_id":"system","text":"","session_id":"task-001"}
```

### 

```
POST /cancel

{"user_id":"<user_id>","session_id":"<session_id>"}
```


## OASIS 

> 📖 **专注 OASIS 使用的独立指引文档（尤其是 OpenClaw agent 集成）**: [OASIS_GUIDE.md](./OASIS_GUIDE.md)

> ""
> - ** vs **"/""/("> - ** vs detach**

### 1)  vs 

**discussion=true**
- 
- ""

**discussion=false**
-  OASIS ////
- 

### 2)  vs detach

**detach=true**
-  `topic_id`/ `check_oasis_discussion(topic_id)` 
- 

**detach=false**
-  `post_to_oasis` 
- /

### 3) 



1. ** =  + **
   - `discussion=true`
   - `detach=true`

2.  ****
   - " /  /  / "
   - " SOP /  / "

3.  ****
   - " /  /  / "
   - /

### 4) 

|  |  |  |  |
|---|---|---|---|
|  +  **()** | discussion=true, detach=true | topic_id | // |
|  +  | discussion=true, detach=false |  | / |
|  +  | discussion=false, detach=true | topic_id | / |
|  +  | discussion=false, detach=false |  | // |


## OASIS 

OASIS  **** `schedule_yaml`  `name` 

| # |  | Name  |  |  |
|---|------|-----------|--------|------|
| 1 | **Direct LLM** | `tag#temp#N` | `ExpertAgent` |  LLM    LLM    + `tag` /`N`  |
| 2 | **Oasis Session** | `tag#oasis#id` | `SessionExpert` (oasis) | OASIS  bot session`tag`  system promptBot `id`  ID  session |
| 3 | **Regular Agent** | `Title#session_id` | `SessionExpert` (regular) |  agent session `#default``Coder#my-project`session  system prompt  agent bot session  |
| 4 | **External API** | `tag#ext#id` | `ExternalExpert` |  OpenAI  APIDeepSeekGPT-4Ollama TeamClaw  agent YAML `headers`  | openclaw agent

### Session ID 

```
tag#temp#N            ExpertAgent   (, LLM)
tag#oasis#<id>        SessionExpert (oasis, bot)
Title#session_id      SessionExpert (agent session)
tag#ext#<id>          ExternalExpert (APIopenclaw agent)
```

****
-  session  `#new` ** session**ID  UUID
  - `creative#oasis#abc#new`  `#new` ID  UUID
  - `#my-session#new`  

**Oasis session **
- Oasis session  `session_id`  `#oasis#`  `creative#oasis#ab12cd34`
-  Agent checkpoint DB`data/agent_memory.db`
- 
- `tag` 

### YAML 

```yaml
version: 1
plan:
  # Type 1: Direct LLM
  - expert: "creative#temp#1"
  - expert: "critical#temp#2"

  # Type 2: Oasis session
  - expert: "data#oasis#analysis01"
  - expert: "synthesis#oasis#new#new"   # session

  # Type 3: Regular agent sessionbot
  - expert: "#default"
  - expert: "Coder#my-project"

  # Type 4: External APIDeepSeek, GPT-4
  - expert: "deepseek#ext#ds1"

  # Type 4: OpenClaw External API Agent 
  # model 匹配 "agent:<name>:<session>" 时优先使用 CLI 调用：
  #   openclaw agent --agent "main" --session-id "test1" --message "..."
  # CLI 不可用时自动回退到 HTTP API
  - expert: "coder#ext#oc1"
    api_url: "http://127.0.0.1:23001/v1/chat/completions"
    api_key: "****"
    model: "agent:main:test1"    # agent:<agent_name>:<session> → 触发 CLI 优先调用

  # 
  - parallel:
      - expert: "creative#temp#1"
        instruction: ""
      - expert: "critical#temp#2"
        instruction: ""

  #  + 
  - all_experts: true
  - manual:
      author: ""
      content: ""
```

### DAG 模式 — 依赖驱动的并行执行

当工作流存在 **fan-in**（一个节点有多个前驱）或 **fan-out**（一个节点有多个后继）时，使用带 `id` 和 `depends_on` 字段的 DAG 模式。引擎会最大化并行——每个节点在所有依赖完成后立即启动，无需等待无关节点。

**DAG YAML 示例：**

```yaml
version: 1
repeat: false
plan:
  - id: research
    expert: "creative#temp#1"                # 根节点 — 立即启动
  - id: analysis
    expert: "critical#temp#1"                # 根节点 — 与 research 并行运行
  - id: synthesis
    expert: "synthesis#temp#1"
    depends_on: [research, analysis]         # Fan-in：等待两者都完成
  - id: review
    expert: "data#temp#1"
    depends_on: [synthesis]                  # synthesis 完成后执行
```

**DAG 规则：**
- 每个步骤**必须**有唯一的 `id` 字段。
- `depends_on` 是该步骤启动前必须完成的步骤 id 列表。根节点不需要此字段。
- 图**必须**无环（禁止循环依赖）。
- 没有依赖关系的步骤自动并行执行。
- 可视化画布自动检测 fan-in/fan-out 并生成 DAG 格式。
- `manual` 步骤同样支持 `id`/`depends_on`。

### External API (Type 4) 

Type 4  agent  YAML 

```yaml
version: 1
plan:
  - expert: "#ext#analyst"
    api_url: "https://api.deepseek.com"          #  API  base URL /v1/chat/completions
    api_key: "****"                               # Optional: API key for the external service
    model: "deepseek-chat"                        #  gpt-3.5-turbo
    headers:                                      #  HTTP key-value 
      X-Custom-Header: "value"
```

> 🔒 **API Key 安全机制**：YAML 中设置 `api_key: "****"`（或完全省略）即可使用掩码。如果写入明文密钥，也能正常工作（向后兼容）。

****

|  |  |  |
|------|------|------|
| `api_url` |  |  API  `/v1/chat/completions` |
| `api_key` |  | API key，支持 `****` 掩码或明文密钥 |
| `model` |  |  `gpt-3.5-turbo` |
| `headers` |  |  key-value  HTTP  |

**OpenClaw **

OpenClaw  OpenAI  Agent  OpenClaw **** `api_url`

> ** 说明：**
> - **Path Convention**: `./agents/main/sessions/sessions.json` 是 OpenClaw agent sessions 的常用路径结构。
> - **Session Management**: 获取 session 信息是 OpenClaw agent 编排的必要过程，用于多 agent 工作流协调和可视化画布操作。

**OpenClaw  `model` **

```
agent:<agent_name>:<session_name>
```

- `agent_name`OpenClaw  agent  `main`
- `session_name` `test1``default` ** session **


- `agent:main:default`   main agent  default session
- `agent:main:test1`   main agent  test1 session
- `agent:main:code-review`   main agent  code-review session

**OpenClaw CLI 优先调用：**

当 `model` 字段匹配 `agent:<agent_name>:<session_id>` 格式时，系统**自动优先**使用 OpenClaw CLI 调用：
```
openclaw agent --agent "<agent_name>" --session-id "<session_id>" --message "<message>"
```
如果 `openclaw` CLI 不在 PATH 中或 CLI 调用失败，则**自动回退**到标准 HTTP API（使用 `api_url` 和 `x-openclaw-session-key` header）。这确保了最大的可靠性和简洁性 —— 当 CLI 可用时无需额外配置 headers。

**请求头组装逻辑（HTTP 回退模式）：**
最终请求头 = `Content-Type: application/json` + `Authorization: Bearer <api_key>` + YAML `headers` 中的所有键值对。

**`x-openclaw-session-key` —— OpenClaw 确定性 Session 路由（HTTP 模式）：**

当 CLI 不可用而回退到 HTTP API 时，`x-openclaw-session-key` HTTP header 是**将请求路由到指定 OpenClaw session 的关键机制**。缺少此 header，OpenClaw 可能无法正确关联到目标 session。

- 前端编排面板在拖拽 OpenClaw session 到画布时会**自动设置**此 header。
- 手动编写 YAML 或通过 API 调用时，**必须**在 `headers` 字段中包含此 header 以确保 session 的确定性。

```yaml
# 示例：连接到指定的 OpenClaw session
- expert: "coder#ext#oc1"
  api_url: "http://127.0.0.1:18789"
  api_key: "****"
  model: "agent:main:my-session"
  headers:
    x-openclaw-session-key: "agent:main:my-session"   # ← 此 header 决定了目标 OpenClaw session
```

> `x-openclaw-session-key` 的值应与 `model` 字段的 session 标识符一致（格式：`agent:<agent_name>:<session_name>`）。这确保外部请求被路由到正确的 OpenClaw agent session，保持对话连续性和状态。

---

##  OASIS Server

OASIS Server 51202** Agent ** curl  OASIS  MCP  Agent 

****
- /
-  workflow 
-  OASIS 
- workflow 

****
- OASIS `bash selfskill/scripts/run.sh start` 
-  `user_id`  Authorization header

**API **

|  |  |  |
|------|------|------|
|  | GET | `/experts?user_id=xxx` |
|  | POST | `/experts/user` |
| / | PUT/DELETE | `/experts/user/{tag}` |
|  oasis sessions | GET | `/sessions/oasis?user_id=xxx` |
|  workflow | POST | `/workflows` |
|  workflows | GET | `/workflows?user_id=xxx` |
| YAML  Layout | POST | `/layouts/from-yaml` |
| / | POST | `/topics` |
|  | GET | `/topics/{topic_id}?user_id=xxx` |
|  | GET | `/topics/{topic_id}/conclusion?user_id=xxx&timeout=300` |
| SSE  | GET | `/topics/{topic_id}/stream?user_id=xxx` |
|  | DELETE | `/topics/{topic_id}?user_id=xxx` |
|  | GET | `/topics?user_id=xxx` |

>  MCP 

---

### OASIS /

```
POST http://127.0.0.1:51202/topics

{"question":"","user_id":"system","max_rounds":3,"discussion":true,"schedule_file":"...","schedule_yaml":"...","callback_url":"http://127.0.0.1:51200/system_trigger","callback_session_id":"my-session"}
```

schedule_yamlyamlyaml/XXXXX/TeamClaw/data/user_files/username

###  curl  OASIS 

OASIS  51202 MCP  curl  `user_id` 

#### 1. 
```bash
#  + 
curl 'http://127.0.0.1:51202/experts?user_id=xinyuan'

# 
curl -X POST 'http://127.0.0.1:51202/experts/user' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","name":"","tag":"pm","persona":"","temperature":0.7}'

# 
curl -X PUT 'http://127.0.0.1:51202/experts/user/pm' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","persona":""}'

# 
curl -X DELETE 'http://127.0.0.1:51202/experts/user/pm?user_id=xinyuan'
```

#### 2. 
```bash
#  OASIS  #oasis#  session
curl 'http://127.0.0.1:51202/sessions/oasis?user_id=xinyuan'
```

#### 3. Workflow 
```bash
#  workflows
curl 'http://127.0.0.1:51202/workflows?user_id=xinyuan'

#  workflow layout
curl -X POST 'http://127.0.0.1:51202/workflows' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","name":"trio_discussion","schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","description":"","save_layout":true}'
```

#### 4. Layout 
```bash
#  YAML  layout
curl -X POST 'http://127.0.0.1:51202/layouts/from-yaml' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","yaml_source":"version:1\nplan:\n - expert: \"creative#temp#1\"","layout_name":"trio_layout"}'
```

#### 5. /
```bash
# 
curl -X POST 'http://127.0.0.1:51202/topics' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","question":"","max_rounds":3,"schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","discussion":true}'

#  topic_id
curl -X POST 'http://127.0.0.1:51202/topics' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"xinyuan","question":"","max_rounds":3,"schedule_yaml":"version:1\nplan:\n - expert: \"creative#temp#1\"","discussion":true,"callback_url":"http://127.0.0.1:51200/system_trigger","callback_session_id":"my-session"}'

# 
curl 'http://127.0.0.1:51202/topics/{topic_id}?user_id=xinyuan'

# 
curl 'http://127.0.0.1:51202/topics/{topic_id}/conclusion?user_id=xinyuan&timeout=300'

# 
curl -X DELETE 'http://127.0.0.1:51202/topics/{topic_id}?user_id=xinyuan'

# 
curl 'http://127.0.0.1:51202/topics?user_id=xinyuan'
```

#### 6. 
```bash
# SSE 
curl 'http://127.0.0.1:51202/topics/{topic_id}/stream?user_id=xinyuan'
```

****
- Workflows (YAML): `data/user_files/{user}/oasis/yaml/{file}.yaml` YAML  layout JSON
- : `data/oasis_user_experts/{user}.json`
- : `data/oasis_topics/{user}/{topic_id}.json`

****  MCP  `list_oasis_experts``add_oasis_expert``update_oasis_expert``delete_oasis_expert``list_oasis_sessions``set_oasis_workflow``list_oasis_workflows``yaml_to_layout``post_to_oasis``check_oasis_discussion``cancel_oasis_discussion``list_oasis_topics` 

## 



```bash
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx4c74 \
  LLM_BASE_URL=https://deepseek.com \
  LLM_MODEL=deepseek-chat \
  LLM_VISION_SUPPORT=true \
  TTS_MODEL=gemini-2.5-flash-preview-tts \
  TTS_VOICE=charon \
  PORT_AGENT=51200 \
  PORT_SCHEDULER=51201 \
  PORT_OASIS=51202 \
  PORT_FRONTEND=51209 \
  OPENAI_STANDARD_MODE=false
bash selfskill/scripts/run.sh add-user system <your-password>
```

 `configure --show` 

```
  PORT_SCHEDULER=51201
  PORT_AGENT=51200
  PORT_FRONTEND=51209
  PORT_OASIS=51202
  OASIS_BASE_URL=http://127.0.0.1:51202
  INTERNAL_TOKEN=f1aa****57e7          # 
  LLM_API_KEY=sk-7****4c74
  LLM_BASE_URL=https://deepseek.com
  LLM_MODEL=deepseek-chat
  LLM_VISION_SUPPORT=true
  TTS_MODEL=gemini-2.5-flash-preview-tts
  TTS_VOICE=charon
  OPENAI_STANDARD_MODE=false
```

> `INTERNAL_TOKEN` `PUBLIC_DOMAIN`  tunnel 

## 

```bash
cd /home/avalon/TeamClaw

# 
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch LLM_API_KEY=sk-xxx LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-chat
# ⚠️ 必须先询问用户想要的用户名和密码！
bash selfskill/scripts/run.sh add-user <username> <password>

# 
bash selfskill/scripts/run.sh start

#  API
curl -X POST http://127.0.0.1:51200/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <username>:<password>" \
  -d '{"model":"mini-timebot","messages":[{"role":"user","content":""}],"stream":false,"session_id":"default"}'

# 
bash selfskill/scripts/run.sh stop
```

## 

-  skill  `selfskill/scripts/`
-  PID `start` 
- `INTERNAL_TOKEN` 
- : `logs/launcher.log`

- 
- openclaw session fileskillopenclaw agentopenclaw

---

## ⚠️ Before First Launch — Required Configuration

Before starting TeamClaw for the first time, the following environment variables **must** be configured. Without them the service will not function correctly.

### 1. LLM Configuration (Required)

> ⚠️ **LLM API ≠ OpenClaw API — They are two completely separate sets of credentials!**
>
> - `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` → Your **LLM provider** (DeepSeek, OpenAI, Google, etc.). Used for the built-in Agent's conversations and OASIS experts.
>
> Do **NOT** mix them up. They point to different services, use different keys, and serve different purposes.

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | Your LLM provider's API key. **This is mandatory.** | `sk-xxxxxxxxxxxxxxxx` |
| `LLM_BASE_URL` | Base URL of your LLM provider's API endpoint. | `https://api.deepseek.com` |
| `LLM_MODEL` | The model name to use. **If not specified, auto-detected.** | `deepseek-chat` / `gpt-4o` / `gemini-2.5-flash` |

> ⚠️ **If the user does not specify `LLM_MODEL`**: the agent MUST auto-detect it instead of guessing. Use the supplied API key and base URL to list provider models, choose the newest plausible chat model, then confirm it with a real completion request before writing `LLM_MODEL` into `config/.env`.

```bash
# Option A: User specifies model name
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat

# Option B: Auto-detect model (when user doesn't specify)
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com
bash selfskill/scripts/run.sh auto-model
# → Lists available models; agent reads the output and picks one
bash selfskill/scripts/run.sh configure LLM_MODEL <chosen-model>
```

> 💡 **`auto-model` behavior**: Calls the API's `/v1/models` endpoint and prints all available models. It does **not** auto-select or write to `.env` — the AI agent reads the printed list, picks the most suitable model (preferring general chat models over reasoning-only models), and sets it via `configure LLM_MODEL <model>`. This avoids hardcoding model preferences that quickly become outdated as providers update their offerings.

### 2. OpenClaw Auto-Detection & Installation (Required for Visual Workflow)

> ⚠️ **AGENT BEHAVIOR**: When the user wants to use OpenClaw features (visual workflow orchestration, multi-agent canvas, etc.), the agent MUST:
> 1. First check if OpenClaw is installed: `which openclaw`
> 2. If NOT installed → **ASK the user for confirmation** before proceeding with installation
> 3. If confirmed → follow the installation steps below
> 4. After installation → auto-configure `OPENCLAW_API_URL` and sync API key with TeamClaw's `LLM_API_KEY`
> 5. If the user declines → skip OpenClaw installation, TeamClaw will still work (just without OpenClaw orchestration features)

**Detection & Installation Flow:**

```bash
# Step 1: Check if OpenClaw is already installed
bash selfskill/scripts/run.sh check-openclaw
```

**If OpenClaw is NOT installed, the agent should:**

```bash
# Step 2: Verify Node.js ≥ 22 is available (required by OpenClaw)
node --version  # Must be v22.x.x or higher

# If Node.js is not installed or version < 22:
#   Option A (recommended): Download pre-built binary
#     curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz -o /tmp/node22.tar.xz
#     tar -xf /tmp/node22.tar.xz -C /tmp
#     export PATH="/tmp/node-v22.14.0-linux-x64/bin:$PATH"
#   Option B: Via nvm
#     nvm install 22 && nvm use 22

# Step 3: Install OpenClaw globally (ONLY after user confirmation!)
# ⚠️ MUST use --ignore-scripts to avoid node-llama-cpp build failure (requires cmake/xpm)
npm install -g openclaw@latest --ignore-scripts

# Step 4: Ensure openclaw is in PATH
# npm global bin path may not be in PATH by default
# Check with: npm bin -g   (e.g., /root/.npm/node_modules/bin)
# If not in PATH, add it:
export PATH="$(npm bin -g 2>/dev/null || npm prefix -g)/bin:$PATH"

# Step 5: Verify installation
openclaw --version

# Step 6: Run the onboarding wizard (interactive — user must complete this)
openclaw onboard --install-daemon
# The wizard guides through: gateway setup, workspace config, channel pairing, skills

# Step 7: Auto-configure TeamClaw's OpenClaw integration
bash selfskill/scripts/run.sh check-openclaw
# This will now detect the installed OpenClaw and auto-configure:
#   - OPENCLAW_API_URL (from openclaw config get gateway.port)
#   - OPENCLAW_SESSIONS_FILE (from openclaw workspace path)
```

**API Key Sync Strategy:**

TeamClaw and OpenClaw maintain **separate API key configurations** — they serve different purposes:
- `LLM_API_KEY` → TeamClaw's built-in Agent conversations and OASIS experts
- `OPENCLAW_GATEWAY_TOKEN` → Authentication for OpenClaw Gateway API (HTTP fallback mode)

The `check-openclaw` command will:
1. Auto-detect `OPENCLAW_API_URL` via `openclaw config get gateway.port`
2. Auto-detect `OPENCLAW_GATEWAY_TOKEN` from OpenClaw's configuration
3. Auto-detect `OPENCLAW_SESSIONS_FILE` from OpenClaw's workspace path
4. **Initialize workspace with default templates** (if files don't exist)
5. Write all detected values to TeamClaw's `config/.env`

> 💡 **Note**: OpenClaw agents are primarily invoked via CLI (`openclaw agent --agent <name> --message <msg>`), which does not require API keys. The `OPENCLAW_GATEWAY_TOKEN` is only used as a fallback when CLI is unavailable.
>
> ⚠️ **OpenClaw token caveat (important)**: on newer OpenClaw versions, `openclaw config get gateway.auth.token` may return the masked placeholder `__OPENCLAW_REDACTED__` instead of the real token. Treat that value as masked output, not a usable credential. If the Dashboard says `gateway token missing`, prefer `openclaw dashboard --no-open` and open the tokenized URL it prints, or read the real token from `~/.openclaw/openclaw.json` → `gateway.auth.token`. Never write `__OPENCLAW_REDACTED__` into TeamClaw's `.env`.

**Default Workspace Templates:**

The `check-openclaw` command automatically creates the following files in the OpenClaw workspace (`~/.openclaw/workspace`) if they don't exist. These follow the OpenClaw community's recommended workspace structure:

| File | Purpose |
|------|---------|
| `BOOTSTRAP.md` | First-run initialization guide — asks user for name, role, timezone |
| `SOUL.md` | **Core file** — defines AI behavior, principles, communication style |
| `IDENTITY.md` | AI name, type, role, and personality traits |
| `AGENTS.md` | Multi-agent collaboration config with TeamClaw integration |
| `TOOLS.md` | Available tools and usage rules |
| `USER.md` | User profile, timezone, preferences (updated via BOOTSTRAP) |
| `HEARTBEAT.md` | Scheduled and recurring tasks |
| `MEMORY.md` | Long-term memory for workspace context |

OpenClaw loads all these files as agent context on every execution. **Existing files are never overwritten** — only missing files are created.

To re-initialize templates manually:
```bash
python selfskill/scripts/configure_openclaw.py --init-workspace
# Or specify a custom workspace path:
python selfskill/scripts/configure_openclaw.py --init-workspace /path/to/workspace
```

### 3. OpenClaw Integration (Required for visual workflow orchestration)

> ⚠️ **Reminder: OpenClaw API is NOT the same as LLM API above!**
>
> The `OPENCLAW_*` variables below point to your **locally running OpenClaw service**, not to an external LLM provider. They have completely different URLs, keys, and purposes.

These variables are used for the OASIS visual Canvas to orchestrate OpenClaw agents (**all auto-detected by default**):

### 3. Cloudflare Tunnel (Optional — for remote access)

Public network deployment is **entirely user-controlled** — the system will NEVER expose ports to the public internet without explicit user action.

> **⚠️ CRITICAL RULE FOR AGENTS**: The agent MUST NOT download `cloudflared`, start the tunnel, or execute any public-network-related commands on its own initiative. These actions are ONLY allowed when the user **explicitly** requests them (e.g., "start the tunnel", "enable public access"). The agent should NEVER proactively suggest or auto-start public deployment.

There are three ways to start/stop the tunnel:

| Method | How |
|--------|-----|
| **CLI (via skill script)** | `bash selfskill/scripts/run.sh start-tunnel` / `stop-tunnel` / `tunnel-status` |
| **Frontend UI** | Settings panel → "🌐 Public Tunnel" section → click Start/Stop button |
| **Agent (explicit user request ONLY)** | User explicitly asks the agent to start the tunnel → agent runs `bash selfskill/scripts/run.sh start-tunnel` |

When the tunnel starts, `cloudflared` is **auto-downloaded** if not present, and `PUBLIC_DOMAIN` is automatically written to `.env`. Note: the download and startup of `cloudflared` only happen upon explicit user instruction — the agent must never trigger this autonomously.

**How agents/bots obtain the public URL** (without reading `.env` directly):

- **Agent**: calls the MCP tool `get_publicnet_info()`, which queries `GET /publicnet/info` on the OASIS server.
- **Telegram Bot**: user sends `/tunnel` command, bot queries `GET /publicnet/info` and replies with the public URL.
- **Direct API**: `curl http://127.0.0.1:51202/publicnet/info` — returns JSON with tunnel status and public domain.

---

## ⚠️ 首次启动前 — 必须配置项

首次启动 TeamClaw 之前，以下环境变量**必须**配置完毕，否则服务无法正常运行。

### 1. LLM 配置（必填）

> ⚠️ **LLM API ≠ OpenClaw API —— 这是两组完全不同的配置！**
>
> - `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` → 你的 **LLM 服务商**（DeepSeek、OpenAI、Google 等）。用于内置 Agent 对话和 OASIS 专家调用。
>
> **切勿混淆！** 它们指向不同的服务，使用不同的密钥，用途完全不同。

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM 服务商的 API 密钥，**必填项**。 | `sk-xxxxxxxxxxxxxxxx` |
| `LLM_BASE_URL` | LLM 服务商的 API 基础地址。 | `https://api.deepseek.com` |
| `LLM_MODEL` | 使用的模型名称。**用户未指定时自动检测。** | `deepseek-chat` / `gpt-4o` / `gemini-2.5-flash` |

> ⚠️ **如果用户没有指定 `LLM_MODEL`**：Agent 不得猜测或直接套示例默认值。必须使用用户提供的 API key 和 base URL 先列出可用模型，选择最新且合理的对话模型，再用一次真实请求验证可调用后，才写入 `config/.env`。

```bash
# 方式 A：用户指定了模型名称
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat

# 方式 B：自动检测模型（用户未指定模型时使用）
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-your-key \
  LLM_BASE_URL=https://api.deepseek.com
bash selfskill/scripts/run.sh auto-model
# → 列出可用模型列表；agent 阅读输出并选择一个
bash selfskill/scripts/run.sh configure LLM_MODEL <选定的模型>
```

> 💡 **`auto-model` 工作原理**：调用 API 的 `/v1/models` 端点，打印所有可用模型列表。它**不会**自动选择或写入 `.env` —— AI agent 阅读打印的列表，选择最合适的模型（优先选择通用聊天模型而非纯推理模型），然后通过 `configure LLM_MODEL <模型名>` 设置。这样避免了硬编码模型偏好导致随厂商更新而过时的问题。

### 2. OpenClaw 自动检测与安装（使用可视化工作流时必需）

> ⚠️ **Agent 行为规范**：当用户需要使用 OpenClaw 功能（可视化工作流编排、多 Agent 画布等）时，Agent 必须：
> 1. 先检测 OpenClaw 是否已安装：`which openclaw`
> 2. 如果未安装 → **必须先询问用户确认**再进行安装
> 3. 用户确认后 → 按以下步骤安装
> 4. 安装完成后 → 自动配置 `OPENCLAW_API_URL`，并与 TeamClaw 的 `LLM_API_KEY` 同步 API 密钥
> 5. 用户拒绝 → 跳过安装，TeamClaw 仍可正常使用（仅无法使用 OpenClaw 编排功能）

**检测与安装流程：**

```bash
# 步骤 1：检测 OpenClaw 是否已安装
bash selfskill/scripts/run.sh check-openclaw
```

**如果 OpenClaw 未安装，Agent 应执行：**

```bash
# 步骤 2：确认 Node.js ≥ 22 可用（OpenClaw 的前置依赖）
node --version  # 必须是 v22.x.x 或更高版本

# 如果 Node.js 未安装或版本 < 22：
#   方式 A（推荐）：下载预编译二进制
#     curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz -o /tmp/node22.tar.xz
#     tar -xf /tmp/node22.tar.xz -C /tmp
#     export PATH="/tmp/node-v22.14.0-linux-x64/bin:$PATH"
#   方式 B：通过 nvm
#     nvm install 22 && nvm use 22

# 步骤 3：全局安装 OpenClaw（必须用户确认后再执行！）
# ⚠️ 必须使用 --ignore-scripts 避免 node-llama-cpp 编译失败（需要 cmake/xpm）
npm install -g openclaw@latest --ignore-scripts

# 步骤 4：确保 openclaw 在 PATH 中
# npm 全局 bin 路径可能不在默认 PATH 中
# 检查方法: npm bin -g   （如 /root/.npm/node_modules/bin）
# 如果不在 PATH 中，手动添加:
export PATH="$(npm bin -g 2>/dev/null || npm prefix -g)/bin:$PATH"

# 步骤 5：验证安装
openclaw --version

# 步骤 6：运行初始化向导（交互式 — 用户需完成此步骤）
openclaw onboard --install-daemon
# 向导将引导完成：gateway 设置、workspace 配置、channel 配对、skills 安装

# 步骤 7：自动配置 TeamClaw 的 OpenClaw 集成
bash selfskill/scripts/run.sh check-openclaw
# 此时会检测到已安装的 OpenClaw 并自动配置：
#   - OPENCLAW_API_URL（从 openclaw config get gateway.port 获取）
#   - OPENCLAW_SESSIONS_FILE（从 openclaw workspace 路径获取）
```

**API 密钥同步策略：**

TeamClaw 和 OpenClaw 使用**独立的 API 密钥配置** —— 用途不同：
- `LLM_API_KEY` → TeamClaw 内置 Agent 对话和 OASIS 专家调用
- `OPENCLAW_GATEWAY_TOKEN` → OpenClaw Gateway API 认证（HTTP 回退模式时使用）

`check-openclaw` 命令会自动：
1. 通过 `openclaw config get gateway.port` 探测 `OPENCLAW_API_URL`
2. 从 OpenClaw 配置中探测 `OPENCLAW_GATEWAY_TOKEN`
3. 从 OpenClaw workspace 路径探测 `OPENCLAW_SESSIONS_FILE`
4. **初始化 workspace 默认模板**（仅在文件不存在时创建）
5. 将所有探测到的值写入 TeamClaw 的 `config/.env`

> 💡 **提示**：OpenClaw agent 主要通过 CLI 调用（`openclaw agent --agent <name> --message <msg>`），无需 API 密钥。`OPENCLAW_GATEWAY_TOKEN` 仅在 CLI 不可用时作为 HTTP 回退的认证凭据。
>
> ⚠️ **OpenClaw token 特别说明**：较新的 OpenClaw 版本里，`openclaw config get gateway.auth.token` 可能只会返回脱敏占位符 `__OPENCLAW_REDACTED__`，这不是可用 token。遇到 Dashboard 报 `gateway token missing` 时，优先执行 `openclaw dashboard --no-open`，使用它输出的带 token 链接；或者从 `~/.openclaw/openclaw.json` 的 `gateway.auth.token` 读取真实 token。绝不能把 `__OPENCLAW_REDACTED__` 写入 TeamClaw 的 `.env`。

**Workspace 默认模板：**

`check-openclaw` 命令会自动在 OpenClaw workspace（`~/.openclaw/workspace`）中创建以下文件（如果不存在）。模板遵循 OpenClaw 社区推荐的 workspace 结构：

| 文件 | 用途 |
|------|------|
| `BOOTSTRAP.md` | 首次运行初始化引导 — 询问用户名称、角色、时区等 |
| `SOUL.md` | **核心文件** — 定义 AI 行为准则、沟通风格、安全规则 |
| `IDENTITY.md` | AI 名称、类型、角色和性格特征 |
| `AGENTS.md` | 多 Agent 协作配置，含 TeamClaw 集成说明 |
| `TOOLS.md` | 可用工具列表和使用规则 |
| `USER.md` | 用户资料、时区、偏好（通过 BOOTSTRAP 或手动更新） |
| `HEARTBEAT.md` | 定时/周期任务（会话后、每日、每周） |
| `MEMORY.md` | 长期记忆，保存用户偏好和重要决策 |

OpenClaw 每次执行都会加载这些文件作为 agent 上下文。**已存在的文件不会被覆盖** — 只创建缺失的文件。

手动重新初始化模板：
```bash
python selfskill/scripts/configure_openclaw.py --init-workspace
# 或指定自定义 workspace 路径:
python selfskill/scripts/configure_openclaw.py --init-workspace /path/to/workspace
```

### 3. OpenClaw 集成配置（使用可视化编排时必填）

> ⚠️ **再次提醒：OpenClaw API 和上面的 LLM API 不是同一个东西！**
>
> 下面的 `OPENCLAW_*` 变量指向你 **本地运行的 OpenClaw 服务**，而非外部 LLM 服务商。它们的 URL、密钥和用途完全不同。

### 3. Cloudflare Tunnel（可选 — 用于远程访问）

公网部署**完全由用户控制** —— 系统绝不会在未经用户明确操作的情况下将端口暴露到公网。

> **⚠️ Agent 关键规则**：Agent **禁止**主动下载 `cloudflared`、启动隧道或执行任何公网部署相关命令。这些操作**仅在用户明确指令**下才允许执行（如"启动隧道"、"开启公网访问"）。Agent 绝不能自行建议或自动启动公网部署。

启动/停止隧道有三种方式：

| 方式 | 操作 |
|------|------|
| **命令行（skill 脚本）** | `bash selfskill/scripts/run.sh start-tunnel` / `stop-tunnel` / `tunnel-status` |
| **前端 UI** | Settings 面板 → "🌐 公网隧道" 区域 → 点击启动/停止按钮 |
| **Agent（仅限用户明确指令）** | 用户明确要求启动隧道 → agent 执行 `bash selfskill/scripts/run.sh start-tunnel` |

启动隧道时，如本地未安装 `cloudflared`，会**自动下载**。隧道建立后 `PUBLIC_DOMAIN` 自动写入 `.env`。注意：`cloudflared` 的下载和启动仅在用户明确指令下发生 —— agent 绝不能自主触发。

**Agent / Bot 如何获取公网地址**（不直接读 `.env`）：

- **Agent**：调用 MCP tool `get_publicnet_info()`，内部请求 OASIS 服务的 `GET /publicnet/info` 接口。
- **Telegram Bot**：用户发送 `/tunnel` 命令，bot 直接查询 `GET /publicnet/info` 并回复公网地址。
- **直接 API 调用**：`curl http://127.0.0.1:51202/publicnet/info` —— 返回 JSON 格式的隧道状态和公网域名。

```json
// GET /publicnet/info 返回示例
{
  "tunnel": {"running": true, "pid": 12345, "public_domain": "https://xxx.trycloudflare.com"},
  "ports": {"frontend": "51209", "oasis": "51202"}
}
```
