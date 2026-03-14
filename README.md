# TeamClaw

![TeamClaw Poster](docs/poster.png)

OpenAI-compatible AI agent system with a built-in multi-expert orchestration engine.

## Install via AI Code CLI (Recommended)

Open any AI coding assistant such as Codex, Cursor, Claude Code, or a similar tool, then use this prompt:

```text
Clone https://github.com/Avalon-467/Teamclaw.git and read the SKILL.md inside, then install TeamClaw.
```

The agent should then:

1. Clone the repository
2. Read `SKILL.md`
3. Set up the runtime
4. Ask for the required LLM configuration
5. Start the local services

## Manual Quick Start

### Linux / macOS

```bash
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-xxx \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat
bash selfskill/scripts/run.sh start
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 setup
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 configure --init
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 configure --batch LLM_API_KEY=sk-xxx LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-chat
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 start
```

Default local Web UI:

- [http://127.0.0.1:51209](http://127.0.0.1:51209)

## Docs

- [docs/windows.md](./docs/windows.md) - native PowerShell and WSL setup
- [docs/overview.md](./docs/overview.md) - product overview and capabilities
- [docs/cli.md](./docs/cli.md) - CLI usage
- [docs/ports.md](./docs/ports.md) - port map
- [docs/poster.png](./docs/poster.png) - poster image

## License

[LICENSE](./LICENSE)
