# Windows Installation Options

`TeamClaw` 现在提供两条 Windows 路径：

1. 原生 PowerShell
2. WSL（直接复用现有 `sh` 脚本）

之所以补这份文档，是因为某些分发环境会过滤 `.bat` 文件，所以这里改为提供 `ps1` 入口。

## Option A: Native PowerShell

适合不想装 WSL、或者需要在纯 Windows 环境里直接启动 TeamClaw 的场景。

### 1. Install dependencies

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_env.ps1
```

这个脚本会：

- 检查并安装 `uv`（如果本机还没有）
- 创建 `.venv`
- 安装 `config/requirements.txt`

### 2. Initialize config

```powershell
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 configure --init
```

### 3. Fill in required LLM settings

```powershell
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 configure --batch `
  LLM_API_KEY=sk-xxx `
  LLM_BASE_URL=https://api.deepseek.com `
  LLM_MODEL=deepseek-chat
```

### 4. Start services

```powershell
powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 start
```

启动后访问：

- Web UI: [http://127.0.0.1:51209](http://127.0.0.1:51209)

本机 `127.0.0.1` 访问默认支持免密登录，所以不是必须先创建密码用户。

### 5. Optional commands

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\adduser.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\tunnel.ps1
```

## Option B: WSL

适合想继续直接使用仓库里现成 `sh` 脚本的人，也适合已经在 WSL 里维护 `node` / `bash` 工具链的人。

### 1. Install WSL

在管理员 PowerShell 中执行：

```powershell
wsl --install -d Ubuntu
```

安装完成后重启系统，打开 Ubuntu。

### 2. Install base packages in Ubuntu

```bash
sudo apt update
sudo apt install -y curl git python3 python3-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

如果你后续还要用 `OpenClaw`，建议再补上 Node.js 22+。

### 3. Enter the TeamClaw project

如果项目放在 Windows 盘，可以直接进入挂载路径：

```bash
cd /mnt/c/Users/e1344681/Downloads/BorisGuo6.github.io/TeamClaw
```

也可以在 WSL 内重新 clone 一份仓库。

### 4. Run the existing shell workflow

```bash
bash selfskill/scripts/run.sh setup
bash selfskill/scripts/run.sh configure --init
bash selfskill/scripts/run.sh configure --batch \
  LLM_API_KEY=sk-xxx \
  LLM_BASE_URL=https://api.deepseek.com \
  LLM_MODEL=deepseek-chat
bash selfskill/scripts/run.sh start
```

### 5. Access from Windows

WSL 中启动的本地服务通常可以直接从 Windows 浏览器访问：

- [http://127.0.0.1:51209](http://127.0.0.1:51209)

## Recommendation

- 如果你想要最少依赖、最贴近当前 Windows 桌面环境，优先用 PowerShell。
- 如果你想最大化复用现有 `bash` / `node` 生态，优先用 WSL。
- 如果你要继续做 `OpenClaw` 相关的 CLI 或 daemon 集成，WSL 往往更省心。
