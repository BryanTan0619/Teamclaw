---
name: "TeamClaw"
description: "A multi-agent orchestration platform with visual workflow (OASIS). Create and configure agents (OpenClaw/external API), orchestrate them into Teams, design workflows via visual canvas. Supports Team conversations, scheduled tasks, Telegram/QQ bots, and Cloudflare Tunnel for remote access."
user-invokable: true
compatibility:
  - "deepseek"
  - "openai"
  - "gemini"
  - "claude"
  - "anthropic"
  - "ollama"

argument-hint: "[REQUIRED] LLM_API_KEY, LLM_BASE_URL. [MODEL] If LLM_MODEL is not provided, print all available models only, let the caller or agent decide, then run configure LLM_MODEL <model>. [OPTIONAL] TTS_MODEL/TTS_VOICE, STT_MODEL/WHISPER_MODEL, OPENCLAW_*, TELEGRAM_BOT_TOKEN/QQ_APP_ID, PORT_*. [TUNNEL] PUBLIC_DOMAIN only when the user explicitly asks for public access."

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

# TeamClaw

## What Is TeamClaw

TeamClaw is a **multi-agent orchestration platform**. Core concepts:

### Team

A Team is the unit of collaboration, composed of:

| Component | Description |
|-----------|-------------|
| **Members (Agents)** | Task-executing entities, including: |
| └─ Built-in Agent | TeamClaw's lightweight agents (file management, command execution, social media) |
| └─ OpenClaw Agent | Agents from the external OpenClaw platform |
| └─ External API Agent | Any external API service (e.g. GPT-4 API) |
| **Persona (Expert Prompt)** | A special prompt that defines an Agent's identity, personality, and capabilities. In YAML/CLI the field is named `expert`, but it is essentially an **expert persona prompt** — not a separate agent. See `oasis_experts.json` for the prompt collection. |
| **Workflow** | Defines how members collaborate (sequential, parallel, conditional, loop) |

> **Public vs Private**:
> - **Public Agent/Persona**: Available outside any team; can be added to a team for use within it
> - **Private Agent/Persona**: Only available within the current team
> - **Public Workflow**: Can only use public Agents/Personas
> - **Private Workflow**: Only available within the current team; can only use agents already added to the team

### Core Capabilities

1. **Visual Agent Orchestration**
   - Compose OpenClaw Agents, built-in Agents, or any external API Agent into a "Team"
- Drag-and-drop personas on the Web UI canvas (OASIS), configure collaboration relationships
   - **Persona (Expert Prompt)**: A persona (人设) — a special prompt that defines an Agent's role and capabilities. The YAML/CLI field is named `expert` but represents an **expert persona prompt**, not a separate agent.
   - **Agent**: An entity with tools, skills, and prompts that can execute concrete tasks
   - **OpenClaw Agent**: Configurable with custom tools, skills, and prompts via OpenClaw

2. **Team Workflows**
   - Multi-agent parallel discussion/execution with aggregated conclusions
   - **State-graph orchestration**: Sequential, parallel, conditional, loop

3. **Portable Sharing**
   - Export team configurations as a compressed archive for one-click sharing
   - Import shared team configurations for quick reuse

### Built-in Lightweight Agents

TeamClaw includes **lightweight agents** (a streamlined version of OpenClaw):

| Capability | Description |
|------------|-------------|
| **File Management** | Read, write, search files |
| **Command Execution** | Execute shell commands |
| **Social Media** | Communicate with Telegram/QQ users |

- **Lighter weight**: Simpler prompts and a more focused toolset compared to OpenClaw
- **Quick start**: Works out of the box without installing OpenClaw
- **Extensible**: Custom tools and skills can be added

### Feature Overview

| Feature | Description |
|---------|-------------|
| **Team Chat** | Multi-persona parallel discussion/execution, supports 4 persona types |
| **OASIS Workflow** | Visual canvas orchestration, drives parallel agent teams |
| **Scheduled Tasks** | APScheduler-based task scheduling center |
| **Web UI** | Full chat interface with passwordless login via 127.0.0.1 |
| **Bot Integration** | Telegram / QQ Bot (optional) |
| **Public Access** | Cloudflare Tunnel (only when user explicitly requests) |

---

## Purpose

Use this skill to install, configure, and run TeamClaw locally.

For non-install background material, see:

- [docs/overview.md](./docs/overview.md) — Platform overview and architecture
- [docs/cli.md](./docs/cli.md) — Complete CLI command reference
- [docs/build_team.md](./docs/build_team.md) — How to build and configure a Team (members, personas, JSON files)
- [docs/create_workflow.md](./docs/create_workflow.md) — How to create OASIS workflow YAML (graph format, persona types, examples)
- [docs/example_team.md](./docs/example_team.md) — Example Team file structure and contents
- [docs/openclaw-commands.md](./docs/openclaw-commands.md) — OpenClaw integration commands
- [docs/ports.md](./docs/ports.md) — Port configuration and management

### Team Folder Path

TeamClaw stores all team-specific data in the following path structure:

```
data/user_files/{user_id}/teams/{team_name}/
├── internal_agents.json      # Internal agent (expert) session bindings
├── external_agents.json      # External agent definitions (OpenClaw, custom API)
├── oasis_experts.json        # Persona prompt collection (人设 prompt 集合)
└── oasis/yaml/
    └── *.yaml                # Team workflow YAML files
```

**Public/Personal workflows:** `data/user_files/{user_id}/oasis/yaml/*.yaml`

> 💡 **Agent Tip:** You can directly read and modify these files instead of using CLI commands.

### Quick Reference (CLI)

**Build Team:**
```bash
# Create team
uv run scripts/cli.py teams create --team-name <TEAM>

# Add internal agent (uses public expert by tag)
uv run scripts/cli.py internal-agents add \
  --team <TEAM> \
  --data '{"session":"xyz","meta":{"name":"Name","tag":"creative"}}'

# List teams/members
uv run scripts/cli.py teams list
uv run scripts/cli.py teams members --team-name <TEAM>
```

**OpenClaw Agent (3-Step Workflow, 4th Optional):**

```bash
# Step 1: Find existing or create new OpenClaw Agent
uv run scripts/cli.py -u <user> openclaw sessions                    # List existing
uv run scripts/cli.py -u <user> openclaw sessions add \
  --agent-name <name> --backend openai --model gpt-4o ...           # Create new

# Step 2: (Optional) Update config / identity — modify runtime settings
# Similar to OpenClaw "identity" tab settings (temperature, system_prompt, etc.)
# See `docs/openclaw-commands.md` and `docs/cli.md` → 13.openclaw for full details
uv run scripts/cli.py -u <user> openclaw update-config \
  --agent-name <name> --config '{"temperature":0.7, "system_prompt":"..."}'

# Step 3: Add skeleton to team JSON
uv run scripts/cli.py -u <user> teams add-ext-member \
  --team-name <TEAM> --data '{"name":"<name>","tag":"openclaw","global_name":"<name>"}'

# Step 4: (Optional) Export backend config to JSON — see system prompt for details
# ⚡ Only needed if you need full config in JSON (for download/backup/inspection)
# ⚠️ High latency operation — calls backend OpenClaw APIs to fetch full config
# Does NOT affect runtime — only updates JSON snapshot for read/download purposes
uv run scripts/cli.py -u <user> openclaw snapshot export \
  --team-name <TEAM> --name <name>
```

**OASIS Workflow配置格式要求：**
- **Expert字段**：必须使用`tag#ext#id`格式（如：`openclaw#ext#my_new_agent`）
- **Model字段**：支持session扩展：
  - `agent:<name>` - 默认使用团队名称作为session
  - `agent:<name>:<session>` - 显式指定session名称
- **Session控制**：相同session共享上下文，不同session保持独立

> 📖 **Required Reading:**
> - `docs/openclaw-commands.md` — OpenClaw integration details
> - `docs/cli.md` → Section 13 (openclaw) — Full command reference
> - `docs/build_team.md` → Section 3.2 — When to use `export`
>
> 🔧 **Key CLI Tools:**
> - `openclaw sessions` — List/create backend sessions
> - `openclaw update-config` — Modify runtime config (identity-like settings)
> - `teams add-ext-member` — Add agent skeleton to team JSON
> - `openclaw snapshot export` — (Optional) Sync backend → JSON for snapshot/download

**Create & Run Workflow:**
```bash
# List workflows
uv run scripts/cli.py workflows list --team <TEAM>

# Save workflow from YAML
uv run scripts/cli.py oasis set-workflow \
  --team <TEAM> --name <WORKFLOW> --file <PATH_TO_YAML>

# Run workflow
uv run scripts/cli.py workflows run \
  --team <TEAM> --name <WORKFLOW> \
  --question "Task description" --max-rounds 10

# Monitor progress (get topic ID from run output)
uv run scripts/cli.py topics show --topic-id <ID>
uv run scripts/cli.py workflows conclusion --topic-id <ID>
```

**⚡ Recommended: Non-blocking status check**

After running a workflow, use `topics show` to check progress **without blocking**:

```bash
# Instant snapshot — returns immediately, works for running/completed/error topics
uv run scripts/cli.py topics show --topic-id <ID>
```

This returns the current status (`discussing` / `concluded` / `error`), round progress, timeline events, and all posts produced so far. It is safe to call repeatedly as a lightweight poll.

| Method | Blocking | Use Case |
|--------|----------|----------|
| `topics show --topic-id <ID>` | ❌ No | **Recommended.** Quick status snapshot, works at any stage |
| `topics list` | ❌ No | Overview of all topics with status summary |
| `topics watch --topic-id <ID>` | ✅ Yes (SSE) | Real-time streaming, stays connected until done |
| `workflows conclusion --topic-id <ID>` | ⚠️ Semi | Polls until conclusion is ready, then returns |

> 💡 **Agent Tip:** Prefer `topics show` for programmatic checks. Avoid `topics watch` (blocking SSE) and `workflows conclusion` (polling wait) when you need non-blocking behavior.

## Agent Rules

1. Install and configure TeamClaw first. Do not spend time on unrelated feature explanations unless the user asks.
2. Ask for `LLM_API_KEY` and `LLM_BASE_URL` before starting services if they are not already configured.
3. Do not create a password user unless the user explicitly wants password-based login.
4. Do not install or configure OpenClaw unless the user explicitly asks for it.
5. Do not start Cloudflare Tunnel unless the user explicitly asks for public access.
6. On Windows, prefer the PowerShell flow. Use WSL only if the user prefers it or native Windows tooling is unsuitable.
7. If the user did not specify `LLM_MODEL`, do not auto-select and do not ask the user to choose one first.
8. When `LLM_MODEL` is missing, print all available models only, let the caller or agent read the output and decide, then run `configure LLM_MODEL <model>`.
9. If the user wants OpenAI audio features, prefer `TTS_MODEL=gpt-4o-mini-tts`, `TTS_VOICE=alloy`, and `STT_MODEL=whisper-1` unless the user explicitly asks for different audio models.

### Required Reading (Docs)

Before performing operations, read the corresponding docs:

| Operation | Read This Doc | Purpose |
|-----------|---------------|---------|
| Create/Modify Team | `docs/build_team.md` | How to configure members, personas, JSON files |
| Create/Modify Workflow | `docs/create_workflow.md` | OASIS YAML format, persona types, graph structure |
| Use CLI Commands | `docs/cli.md` | Complete CLI reference and examples |
| Understand Team Structure | `docs/example_team.md` | Example file structure and contents |
| OpenClaw Integration | `docs/openclaw-commands.md` | OpenClaw agent commands |
| Port Management | `docs/ports.md` | Port configuration and conflicts |

> **Docs Location:** `/root/.openclaw/workspace/skills/Teamclaw/docs/`

## Standard Install Flow

### Linux / macOS

```bash
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init

# If the user already specified a model:
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-xxx \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat

# If the user did not specify a model:
bash selfskill/scripts/run.sh configure LLM_API_KEY sk-xxx
bash selfskill/scripts/run.sh configure LLM_BASE_URL https://api.deepseek.com
bash selfskill/scripts/run.sh auto-model
# Print all available models only. Do not auto-select.
# The caller or agent reads the output, chooses one model,
# then runs:
bash selfskill/scripts/run.sh configure LLM_MODEL <model>

bash selfskill/scripts/run.sh start
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 setup
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure --init

# If the user already specified a model:
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure --batch LLM_API_KEY=sk-xxx LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-chat

# If the user did not specify a model:
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure LLM_API_KEY sk-xxx
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure LLM_BASE_URL https://api.deepseek.com
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 auto-model
# Print all available models only. Do not auto-select.
# The caller or agent reads the output, chooses one model,
# then runs:
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure LLM_MODEL <model>

powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 start
```

### Windows WSL Fallback

If the user wants to reuse the existing shell scripts directly:

```powershell
wsl --install -d Ubuntu
```

This first step must be run in an elevated PowerShell window. If the current shell is not Administrator, WSL installation and Windows feature checks will fail.

Then inside WSL:

```bash
sudo apt update
sudo apt install -y curl git python3 python3-venv python3-pip rsync
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Prefer a Linux-side copy instead of running directly from /mnt/c.
# This avoids slower virtualenv behavior and shell-script CRLF issues.
mkdir -p ~/TeamClaw-wsl
rsync -a --delete \
  --exclude .git \
  --exclude .venv \
  --exclude logs \
  --exclude __pycache__ \
  /mnt/c/Users/<user>/Downloads/BorisGuo6.github.io/TeamClaw/ \
  ~/TeamClaw-wsl/

cd ~/TeamClaw-wsl
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh start
```

If native Windows TeamClaw is already running on the same machine, keep WSL in a separate copy with its own `.env` and ports. Do not point both installs at the same writable working tree and expect shared runtime state.

## Required Configuration

These keys are required before first start:

| Key | Purpose | Default |
|---|---|---|
| `LLM_API_KEY` | Provider API key | - |
| `LLM_BASE_URL` | OpenAI-compatible base URL | `https://api.deepseek.com` |
| `LLM_MODEL` | Model name | `deepseek-chat` |

When `LLM_MODEL` is not given by the user:

1. Configure `LLM_API_KEY`
2. Configure `LLM_BASE_URL`
3. Run `auto-model`
4. Print the available model list only
5. Let the caller or agent choose one model from the output
6. Run `configure LLM_MODEL <model>`

## Optional Audio Configuration

These are optional, but they matter if the user expects voice input or read-aloud:

| Key | Purpose | Recommended for OpenAI |
|---|---|---|
| `TTS_MODEL` | Text-to-speech model | `gpt-4o-mini-tts` |
| `TTS_VOICE` | Voice preset for TTS | `alloy` |
| `STT_MODEL` | Speech-to-text model for voice input | `whisper-1` |

Notes:

- `Whisper` / `STT_MODEL` is for speech-to-text only. It does not power read-aloud.
- TeamClaw read-aloud uses the `/tts` path.
- TeamClaw voice input now tries speech-to-text first, then only falls back to raw multimodal audio if transcription is unavailable.

## Startup Expectations

After `start`, these four services should come up:

| Service | Port variable | Default port | Purpose |
|---|---|---|---|
| Agent | `PORT_AGENT` | `51200` | OpenAI-compatible API and core agent backend |
| Scheduler | `PORT_SCHEDULER` | `51201` | Scheduled task runner |
| OASIS | `PORT_OASIS` | `51202` | Workflow and discussion engine |
| Frontend | `PORT_FRONTEND` | `51209` | Web UI |

Useful checks:

- `bash selfskill/scripts/run.sh status`
- `powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 status`
- `GET http://127.0.0.1:<PORT_AGENT>/v1/models`
- Open the Web UI at `http://127.0.0.1:<PORT_FRONTEND>`

## Tested Installation Notes

These notes come from a full Windows installation that was verified locally.

- On some Windows machines, the default ports `51200`, `51201`, `51202`, and `51209` fall inside Windows excluded port ranges. The PowerShell entrypoints now auto-remap them to a safe set and write the new values into `config/.env`.
- Because of that remap, the correct local URL is always `http://127.0.0.1:<PORT_FRONTEND>`, not a hardcoded `http://127.0.0.1:51209`.
- On Windows, all PowerShell entrypoints and all MCP subprocesses must use `.venv\Scripts\python.exe`. Relying on the system `python` command or App Execution Alias can break startup.
- `scripts/start.ps1` should run headless. Otherwise `chatbot/setup.py` may block startup in non-interactive PowerShell runs.
- `gpt-5.4` has been tested successfully with `LLM_BASE_URL=https://api.openai.com/` and TeamClaw's `/v1/chat/completions` endpoint.
- OpenAI audio has also been tested successfully with `TTS_MODEL=gpt-4o-mini-tts`, `TTS_VOICE=alloy`, and `STT_MODEL=whisper-1`.
- `auto-model` is for discovery only. It should print the model list, and the caller or agent should pick one model explicitly afterward.
- If WSL is not already installed, the first WSL setup step requires Administrator privileges on Windows before the Linux-side TeamClaw install can be tested.
- For WSL installs, a Linux-side copy such as `~/TeamClaw-wsl` is more reliable than running from `/mnt/c/...`.
- If a WSL copy was created from an older Windows checkout and shell scripts fail with `$'\\r': command not found`, re-copy after the `.gitattributes` fix or convert the copied `*.sh` files to LF line endings.
- On some WSL setups, Windows host access to TeamClaw does not forward cleanly through `127.0.0.1`. When that happens, use the WSL VM IP shown by `status` or `start`, for example `http://172.x.x.x:51209`.
- On WSL IP access from Windows, the request is not treated as local `127.0.0.1`, so passwordless login does not apply. Create a password user first if the user needs to log in from Windows through the WSL IP.
- If native Windows TeamClaw and WSL TeamClaw run at the same time, they must use different copies and different ports.

## Common Operations

### Linux / macOS

```bash
bash selfskill/scripts/run.sh status
bash selfskill/scripts/run.sh stop
bash selfskill/scripts/run.sh configure --show
bash selfskill/scripts/run.sh add-user <username> <password>
bash selfskill/scripts/run.sh auto-model
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 status
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 stop
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 configure --show
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 add-user <username> <password>
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 auto-model
```

## Defaults and Notes

- Default local Web UI is `http://127.0.0.1:51209`, but Windows may auto-switch it to another local port. Check `PORT_FRONTEND` in `config/.env` or run `status`.
- Local `127.0.0.1` access supports passwordless login.
- WSL IP access from Windows should usually use password login, not passwordless login.
- Password users are optional.
- OpenClaw, bots, and tunnel setup are optional and should be user-driven.
- The frontend is the only user-facing service that should normally be opened directly in a browser. The other ports are internal service endpoints unless the user is intentionally calling APIs.

## Optional Commands

### OpenClaw

```bash
bash selfskill/scripts/run.sh check-openclaw
```

```powershell
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 check-openclaw
```

**Configuring OpenClaw Agent in OASIS Canvas:**
- Drag an OpenClaw persona onto the canvas
- **Expert field format**: `tag#ext#id` (必须使用short name格式，如：`openclaw#ext#my_new_agent`)
- **Model format**: `agent:<agent_name>` 或 `agent:<agent_name>:<session_name>`
- **Examples**: 
  - `agent:main:default` (显式指定session)
  - `agent:my_new_agent` (默认使用团队名称作为session)

**关键配置要求：**
- expert字段（人设标识）必须使用`tag#ext#id`格式（tag可以是openclaw、codex等）
- model字段支持session扩展，相同session共享上下文，不同session保持独立

### Tunnel

> ⚠️ Agent MUST NOT start the tunnel automatically. Only start when the user explicitly requests it.

```bash
bash selfskill/scripts/run.sh start-tunnel
bash selfskill/scripts/run.sh stop-tunnel
```

```powershell
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 start-tunnel
powershell -ExecutionPolicy Bypass -File selfskill/scripts/run.ps1 stop-tunnel
```

---

## Usage

Beyond the Web visual frontend, **users can also interact directly with the Agent using this Skill** by issuing operational commands.
The Agent should use CLI tools and strictly follow user instructions.
- Configure LLM, create users, start services
- Create and manage teams, orchestrate workflows
- Initiate discussions, execute tasks

Note: Prefer CLI tools over Web UI for agent operations.

### CLI Service Status Check

After starting services (or when troubleshooting), use the `status` command to quickly check all three core services:

```bash
uv run scripts/cli.py status
```

Example output:
```
📊 Service Status:

  ✅ Agent         :51200  OK
  ✅ OASIS         :51202  OK
  ✅ Frontend      :51209  OK
```

- **Agent** (`:51200`) — Chat engine, handles chat/sessions/tools
- **OASIS** (`:51202`) — Workflow engine, handles topics/experts/workflows
- **Frontend** (`:51209`) — Web UI frontend, provides visual interface

> If a service shows ❌ unreachable, try restarting with `bash selfskill/scripts/run.sh start`.

### List Teams

```bash
uv run scripts/cli.py -u <username> teams list
```

### View Full Team Info

Use `teams info` to aggregate and display all information for a team (members, personas, workflows, topics) in one shot:

```bash
uv run scripts/cli.py -u <username> teams info --team-name <team_name>
```

> This command does not map to a single API endpoint — it combines multiple API calls and formats the output.

> For the complete command reference, see [docs/cli.md](./docs/cli.md)
