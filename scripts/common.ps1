Set-StrictMode -Version Latest

function Set-TeamClawUtf8 {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [Console]::InputEncoding = $utf8NoBom
    [Console]::OutputEncoding = $utf8NoBom
    Set-Variable -Name OutputEncoding -Value $utf8NoBom -Scope Global
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
}

function Get-UvCommand {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        return $uvCommand.Source
    }

    $wingetPackageRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetPackageRoot) {
        $uvExe = Get-ChildItem $wingetPackageRoot -Recurse -Filter "uv.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($uvExe) {
            return $uvExe
        }
    }

    return $null
}

function Ensure-UvInstalled {
    $uv = Get-UvCommand
    if ($uv) {
        return $uv
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "uv was not found and winget is not available. Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    }

    Write-Host "uv was not found. Installing it with winget ..."
    & $winget.Source install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        throw "uv installation failed. Please run: winget install --id astral-sh.uv -e --source winget"
    }

    $uv = Get-UvCommand
    if (-not $uv) {
        throw "uv appears to be installed, but the current session cannot see it yet. Reopen PowerShell and try again."
    }

    return $uv
}

function Get-VenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot
    )

    $pythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $pythonPath) {
        return $pythonPath
    }

    return $null
}

function Ensure-VenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot
    )

    $pythonPath = Get-VenvPython -ProjectRoot $ProjectRoot
    if (-not $pythonPath) {
        throw ".venv\Scripts\python.exe was not found. Run scripts\setup_env.ps1 first."
    }

    return $pythonPath
}

function Read-TeamClawEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }

        $key, $value = $trimmed -split "=", 2
        $values[$key.Trim()] = $value.Trim()
    }

    return $values
}

function Get-TrackedProcessId {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PidFile
    )

    if (-not (Test-Path $PidFile)) {
        return $null
    }

    $raw = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $raw) {
        return $null
    }

    $pidValue = 0
    if ([int]::TryParse($raw.Trim(), [ref]$pidValue)) {
        return $pidValue
    }

    return $null
}

function Test-TrackedProcessRunning {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PidFile
    )

    $pidValue = Get-TrackedProcessId -PidFile $PidFile
    if (-not $pidValue) {
        return $false
    }

    return [bool](Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
}

function Stop-TrackedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PidFile,
        [int]$WaitSeconds = 15
    )

    $pidValue = Get-TrackedProcessId -PidFile $PidFile
    if (-not $pidValue) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $false
    }

    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $pidValue -ErrorAction SilentlyContinue
        $deadline = (Get-Date).AddSeconds($WaitSeconds)
        while ((Get-Date) -lt $deadline) {
            if (-not (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
                break
            }
            Start-Sleep -Milliseconds 500
        }

        if (Get-Process -Id $pidValue -ErrorAction SilentlyContinue) {
            Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    return $true
}

function Start-BackgroundPythonProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot,
        [Parameter(Mandatory = $true)]
        [string]$PythonPath,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$StdOutLog,
        [Parameter(Mandatory = $true)]
        [string]$StdErrLog
    )

    $stdoutDir = Split-Path -Parent $StdOutLog
    $stderrDir = Split-Path -Parent $StdErrLog
    if ($stdoutDir) {
        New-Item -ItemType Directory -Path $stdoutDir -Force | Out-Null
    }
    if ($stderrDir) {
        New-Item -ItemType Directory -Path $stderrDir -Force | Out-Null
    }

    return Start-Process -FilePath $PythonPath `
        -ArgumentList $Arguments `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdOutLog `
        -RedirectStandardError $StdErrLog `
        -PassThru
}

function Wait-HttpEndpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Attempts = 30,
        [int]$DelaySeconds = 2
    )

    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    return $false
}

function Test-LocalPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop | Select-Object -First 1
        return [bool]$connection
    } catch {
        $matches = netstat -ano | Select-String -Pattern (":{0}\s+.*LISTENING" -f $Port)
        return [bool]$matches
    }
}
