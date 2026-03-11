#!/usr/bin/env python3
"""
OpenClaw 自动探测与配置工具。

检测本地 OpenClaw 安装状态，自动探测 gateway 端口、sessions 文件路径、
API token 等配置，并写入 TeamClaw 的 config/.env。

用法:
    python selfskill/scripts/configure_openclaw.py --auto-detect       # 自动探测并配置（含 workspace 初始化）
    python selfskill/scripts/configure_openclaw.py --status            # 仅显示检测状态
    python selfskill/scripts/configure_openclaw.py --init-workspace    # 仅初始化 workspace 默认模板
"""

import json
import os
import shutil
import subprocess
import sys

# 复用 configure.py 的配置写入逻辑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ENV_PATH = os.path.join(PROJECT_ROOT, "config", ".env")

# 添加到 sys.path 以便复用 configure.py
sys.path.insert(0, SCRIPT_DIR)
try:
    from configure import set_env_with_validation, read_env
except ImportError:
    # Fallback: 直接实现最小版本
    def read_env():
        if not os.path.exists(ENV_PATH):
            return [], {}
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        kvs = {}
        for line in lines:
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                kvs[k.strip()] = v.strip()
        return lines, kvs

    def set_env_with_validation(key, value):
        lines, _ = read_env()
        key_found = False
        new_lines = []
        for line in lines:
            s = line.strip()
            if s.startswith(f"{key}=") or s.startswith(f"# {key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)
        if not key_found:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={value}\n")
        os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ {key}={value[:20]}{'...' if len(value) > 20 else ''}")
        return True


def run_cmd(cmd, timeout=15):
    """运行命令并返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "command not found"
    except subprocess.TimeoutExpired:
        return -2, "", "timeout"
    except Exception as e:
        return -3, "", str(e)


def detect_openclaw_bin():
    """检测 openclaw 可执行文件路径"""
    oc_bin = shutil.which("openclaw")
    if oc_bin:
        return oc_bin

    # 尝试通过 npm bin -g 找到全局安装路径
    try:
        result = subprocess.run(
            ["npm", "bin", "-g"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            npm_bin = result.stdout.strip()
            candidate = os.path.join(npm_bin, "openclaw")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    # 尝试通过 npm prefix -g 找到全局安装路径
    try:
        result = subprocess.run(
            ["npm", "prefix", "-g"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            npm_prefix = result.stdout.strip()
            candidate = os.path.join(npm_prefix, "bin", "openclaw")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    # 常见位置
    for path in [
        os.path.expanduser("~/.npm/node_modules/bin/openclaw"),
        os.path.expanduser("~/.npm-global/bin/openclaw"),
        "/usr/local/bin/openclaw",
    ]:
        if os.path.isfile(path):
            return path
    return None


def detect_gateway_port():
    """探测 OpenClaw gateway 端口"""
    rc, out, err = run_cmd(["openclaw", "config", "get", "gateway.port"])
    if rc == 0:
        for line in out.splitlines():
            port = line.strip()
            if port.isdigit():
                return int(port)
    return None


def detect_gateway_token():
    """探测 OpenClaw gateway token"""
    # 尝试从 OpenClaw 配置中获取
    rc, out, err = run_cmd(["openclaw", "config", "get", "gateway.auth.token"])
    if rc == 0 and out.strip():
        token = out.strip()
        # 过滤掉 banner 行，只取有效值
        for line in token.splitlines():
            line = line.strip()
            if line and not line.startswith("openclaw") and not line.startswith("="):
                return line
    return None


def detect_workspace_path():
    """探测 OpenClaw workspace 路径"""
    rc, out, err = run_cmd(["openclaw", "config", "get", "agents.defaults.workspace"])
    if rc == 0 and out.strip():
        for line in out.splitlines():
            line = line.strip()
            if line and os.path.sep in line:
                return line

    # 默认路径
    default_ws = os.path.expanduser("~/.openclaw/workspace")
    if os.path.isdir(default_ws):
        return default_ws

    return None


def detect_sessions_file():
    """探测 OpenClaw sessions.json 文件路径"""
    # 尝试从 openclaw 的配置目录找
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".openclaw", "agents", "main", "sessions", "sessions.json"),
        os.path.join(home, ".moltbot", "agents", "main", "sessions", "sessions.json"),
        "/projects/.moltbot/agents/main/sessions/sessions.json",
        "/projects/.openclaw/agents/main/sessions/sessions.json",
    ]

    # 也检查 openclaw config 获取的 workspace 上级目录
    workspace = detect_workspace_path()
    if workspace:
        parent = os.path.dirname(workspace)  # ~/.openclaw
        candidates.insert(0, os.path.join(parent, "agents", "main", "sessions", "sessions.json"))

    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


def auto_detect_and_configure():
    """自动探测 OpenClaw 配置并写入 .env"""
    oc_bin = detect_openclaw_bin()
    if not oc_bin:
        print("❌ OpenClaw 未安装，无法自动配置")
        print("   请先运行: bash selfskill/scripts/run.sh check-openclaw")
        return False

    print(f"📍 OpenClaw 路径: {oc_bin}")

    # 获取版本信息
    rc, out, _ = run_cmd([oc_bin, "--version"])
    if rc == 0:
        print(f"📌 版本: {out.splitlines()[0] if out else 'unknown'}")

    changes = 0

    # 1. 探测 gateway 端口 → OPENCLAW_API_URL
    print("\n🔍 探测 Gateway 端口...")
    port = detect_gateway_port()
    if port:
        api_url = f"http://127.0.0.1:{port}/v1/chat/completions"
        print(f"   Gateway 端口: {port}")
        set_env_with_validation("OPENCLAW_API_URL", api_url)
        changes += 1
    else:
        # 检查 .env 是否已有配置
        _, kvs = read_env()
        if "OPENCLAW_API_URL" in kvs:
            print(f"   ⚠️ 无法自动探测 gateway 端口，保留现有配置: {kvs['OPENCLAW_API_URL']}")
        else:
            print("   ⚠️ 无法自动探测 gateway 端口")
            print("   提示: 确保 OpenClaw gateway 正在运行 (openclaw gateway)")
            print("   或手动配置: bash selfskill/scripts/run.sh configure OPENCLAW_API_URL http://127.0.0.1:18789/v1/chat/completions")

    # 2. 探测 gateway token → OPENCLAW_GATEWAY_TOKEN
    print("\n🔍 探测 Gateway Token...")
    token = detect_gateway_token()
    if token:
        display = token[:4] + "****" + token[-4:] if len(token) > 8 else "****"
        print(f"   Token: {display}")
        set_env_with_validation("OPENCLAW_GATEWAY_TOKEN", token)
        changes += 1
    else:
        _, kvs = read_env()
        if "OPENCLAW_GATEWAY_TOKEN" in kvs:
            print("   ⚠️ 无法自动探测 token，保留现有配置")
        else:
            print("   ℹ️ 未检测到 gateway token（CLI 模式下通常不需要）")

    # 3. 探测 sessions 文件 → OPENCLAW_SESSIONS_FILE
    print("\n🔍 探测 Sessions 文件...")
    sessions_file = detect_sessions_file()
    if sessions_file:
        print(f"   Sessions: {sessions_file}")
        set_env_with_validation("OPENCLAW_SESSIONS_FILE", sessions_file)
        changes += 1
    else:
        _, kvs = read_env()
        if "OPENCLAW_SESSIONS_FILE" in kvs:
            print(f"   ⚠️ 未找到 sessions.json，保留现有配置: {kvs['OPENCLAW_SESSIONS_FILE']}")
        else:
            print("   ⚠️ 未找到 sessions.json 文件")
            print("   提示: 首次运行 openclaw onboard 后会自动创建")

    # 总结
    print(f"\n{'=' * 50}")
    if changes > 0:
        print(f"✅ 已自动配置 {changes} 项 OpenClaw 集成参数")
        print(f"📁 配置已写入: {ENV_PATH}")
    else:
        print("ℹ️ 未检测到新的配置变更")

    print("\n💡 OpenClaw 集成要点：")
    print("   • OpenClaw Agent 优先通过 CLI 调用（无需额外配置）")
    print("   • HTTP 回退模式需要 OPENCLAW_API_URL + OPENCLAW_GATEWAY_TOKEN")
    print("   • 前端画布需要 OPENCLAW_SESSIONS_FILE 来加载 Agent sessions")

    # 4. 初始化 workspace 默认模板
    init_workspace_templates()

    return True


# --------------- Workspace 模板初始化 ---------------

# OpenClaw 8 个核心文件的默认模板
_WORKSPACE_TEMPLATES = {
    "BOOTSTRAP.md": """\
# BOOTSTRAP

This is the first run of the agent.

Your task is to learn who you are and who the user is.

## Steps

1. Ask the user their preferred name.
2. Ask what kind of assistant you should be (coding, research, general, etc.).
3. Ask their timezone and primary goals.
4. Write the answers to:
   - IDENTITY.md (your name, role, traits)
   - USER.md (user profile and preferences)
   - SOUL.md (update behavior rules based on user needs)

## Guidelines

- Ask one question at a time.
- Keep the conversation natural and concise.
- Do not overwhelm the user.
- Respect existing file content — merge, don't overwrite.

Once finished, you may remove this file or leave it as a record.
""",
    "SOUL.md": """\
# SOUL — Who You Are

You are a practical, efficient AI assistant.

## Core Principles

1. **Start with the answer.** Give the result first, then explain if needed.
2. **Be helpful, not verbose.** Respect the user's time.
3. **Prefer action over explanation.** If you can do it, do it.
4. **Admit uncertainty.** Say "I don't know" rather than guessing.

## Communication Style

- Clear and direct
- Structured with headings and lists when helpful
- Professional but friendly
- No filler phrases ("Great question!", "I'd be happy to help", "Certainly!")

## Thinking Rules

Before answering:

1. Read USER.md for user context and preferences.
2. Check MEMORY.md for relevant past interactions.
3. Determine if tools are needed before writing code.

## Safety Rules

Never execute destructive commands without explicit confirmation:

- Deleting files or directories
- Running unknown shell scripts
- Modifying system configurations
- Force-pushing to git remotes
- Operations that cannot be undone

Always ask for confirmation first.

## Decision Making

When multiple solutions exist:

1. Choose the simplest approach that works.
2. Briefly mention alternatives if they have significant trade-offs.
3. Prefer well-tested, standard solutions over clever hacks.

## Collaboration

This agent may be orchestrated by TeamClaw (multi-agent workflow system).
When receiving tasks from TeamClaw:

- Follow the task instructions precisely.
- Return structured results when possible.
- Use `[oasis reply start]` and `[oasis reply end]` tags when requested.
""",
    "IDENTITY.md": """\
# IDENTITY

Name: Atlas

Type: Personal AI Assistant

Role: A technical AI assistant that helps the user with coding,
research, automation, and problem-solving.

Traits:

- Analytical — breaks problems into clear steps
- Pragmatic — favors working solutions over perfect ones
- Efficient — minimizes unnecessary output
- Curious — explores context before jumping to conclusions

Emoji: 🦞
""",
    "AGENTS.md": """\
# AGENTS

This workspace supports multi-agent collaboration.

## Primary Agent

**main** (default)
- Role: General-purpose assistant
- Handles: coding, research, automation, Q&A

## TeamClaw Integration

This agent can be orchestrated by TeamClaw for multi-agent workflows.
TeamClaw communicates via CLI (`openclaw agent --agent main --message ...`)
or HTTP gateway as fallback.

When working within a TeamClaw workflow:

- You may receive tasks from an orchestrator agent.
- Follow instructions precisely and return structured output.
- Use `[oasis reply start]...[oasis reply end]` tags when the caller expects them.

## Adding More Agents

Use the OpenClaw CLI to add specialized agents:

```
openclaw agents add <name> --workspace <path> --non-interactive
```

Or use TeamClaw's frontend to create and manage agents visually.
""",
    "TOOLS.md": """\
# TOOLS

You may use tools when needed. Choose the simplest tool for the task.

## Available Tools

**shell**
Run safe local commands (ls, cat, grep, git, etc.).
Avoid destructive operations without confirmation.

**python**
Use for calculations, data processing, or scripting.

**file_ops**
Read, write, and manage files in the workspace.

**web_search**
Use when information may be outdated or unknown.

## Rules

1. Choose the simplest tool that solves the problem.
2. Briefly explain why a tool is being used if not obvious.
3. Never run dangerous commands (rm -rf, format, etc.) without asking.
4. Prefer reading files before modifying them.
5. When writing code, include error handling.

## Tool Selection Priority

1. Direct answer from knowledge → no tool needed
2. File operation → file_ops
3. Computation or data → python
4. System task → shell
5. Unknown or outdated info → web_search
""",
    "USER.md": """\
# USER

Name: User

Timezone: Asia/Shanghai

## Preferences

- Concise, actionable answers
- Technical depth when needed
- Code examples over lengthy explanations
- Chinese (简体中文) for conversation when preferred

## Interests

- AI agents and multi-agent systems
- Software development and automation
- Machine learning and model training
- DevOps and infrastructure

## Notes

- This file is updated during BOOTSTRAP or manually.
- The agent should adapt behavior based on these preferences.
""",
    "HEARTBEAT.md": """\
# HEARTBEAT

Scheduled and recurring tasks.

## After Each Conversation

- Update MEMORY.md with important decisions or preferences.
- Note any unfinished tasks.

## Daily

- Summarize key interactions if the day was active.
- Check for pending tasks in MEMORY.md.

## Weekly

- Review recurring patterns and suggest optimizations.
- Clean up outdated entries in MEMORY.md.

## Priority

Always prioritize user commands over background tasks.
Never interrupt active work for scheduled tasks.
""",
    "MEMORY.md": """\
# MEMORY

Long-term memory for this workspace.

## What to Remember

- User preferences and working style
- Important decisions and their rationale
- Recurring workflows and shortcuts
- Project-specific context

## Current Notes

- Initial setup via TeamClaw auto-configuration.
- Workspace initialized with default templates.

---

*Update this file as you learn more about the user and their workflow.*
""",
}


def init_workspace_templates(workspace_path: str | None = None):
    """初始化 OpenClaw workspace 默认模板文件。

    只在文件不存在时创建，不会覆盖已有文件。
    """
    if workspace_path is None:
        workspace_path = detect_workspace_path()

    if not workspace_path:
        # 使用默认路径
        workspace_path = os.path.expanduser("~/.openclaw/workspace")

    # 确保目录存在
    os.makedirs(workspace_path, exist_ok=True)

    created = []
    skipped = []

    for filename, content in _WORKSPACE_TEMPLATES.items():
        filepath = os.path.join(workspace_path, filename)
        if os.path.exists(filepath):
            skipped.append(filename)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            created.append(filename)

    # 输出结果
    print(f"\n🏠 Workspace 模板初始化: {workspace_path}")
    if created:
        print(f"   ✅ 新建 {len(created)} 个文件: {', '.join(created)}")
    if skipped:
        print(f"   ⏭️  跳过 {len(skipped)} 个已存在文件: {', '.join(skipped)}")
    if not created and not skipped:
        print("   ℹ️ 无需初始化")

    return workspace_path


def show_status():
    """显示 OpenClaw 检测状态"""
    oc_bin = detect_openclaw_bin()
    print("=== OpenClaw 集成状态 ===")
    print()

    if not oc_bin:
        print("❌ OpenClaw: 未安装")
        print("   安装: bash selfskill/scripts/run.sh check-openclaw")
        return

    rc, out, _ = run_cmd([oc_bin, "--version"])
    version = out.splitlines()[0] if out and rc == 0 else "unknown"
    print(f"✅ OpenClaw: {version}")
    print(f"   路径: {oc_bin}")

    port = detect_gateway_port()
    if port:
        print(f"✅ Gateway 端口: {port}")
    else:
        print("⚠️ Gateway 端口: 未检测到（gateway 可能未运行）")

    token = detect_gateway_token()
    if token:
        display = token[:4] + "****" + token[-4:] if len(token) > 8 else "****"
        print(f"✅ Gateway Token: {display}")
    else:
        print("ℹ️ Gateway Token: 未配置（CLI 模式不需要）")

    sessions = detect_sessions_file()
    if sessions:
        print(f"✅ Sessions 文件: {sessions}")
    else:
        print("⚠️ Sessions 文件: 未找到")

    # 检查 .env 中的配置
    _, kvs = read_env()
    print()
    print("--- TeamClaw .env 中的 OpenClaw 配置 ---")
    for key in ["OPENCLAW_API_URL", "OPENCLAW_GATEWAY_TOKEN", "OPENCLAW_SESSIONS_FILE"]:
        val = kvs.get(key, "（未配置）")
        if key == "OPENCLAW_GATEWAY_TOKEN" and val and val != "（未配置）":
            val = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
        print(f"  {key} = {val}")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--auto-detect":
        auto_detect_and_configure()
    elif cmd == "--status":
        show_status()
    elif cmd == "--init-workspace":
        ws = sys.argv[2] if len(sys.argv) > 2 else None
        init_workspace_templates(ws)
    else:
        print(f"未知参数: {cmd}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
