[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
. (Join-Path $projectRoot "scripts\common.ps1")

Set-TeamClawUtf8

& (Join-Path $projectRoot "scripts\setup_env.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$python = Ensure-VenvPython -ProjectRoot $projectRoot
$envPath = Join-Path $projectRoot "config\.env"

Push-Location $projectRoot
try {
    if (-not (Test-Path $envPath)) {
        & $python "selfskill\scripts\configure.py" "--init"
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    $envValues = Read-TeamClawEnvFile -Path $envPath
    $apiKey = if ($envValues.ContainsKey("LLM_API_KEY")) { $envValues["LLM_API_KEY"] } else { "" }
    if ([string]::IsNullOrWhiteSpace($apiKey) -or $apiKey -eq "your_api_key_here") {
        Write-Host "config/.env exists, but LLM_API_KEY is still missing."
        Write-Host "Run this first:"
        Write-Host "  powershell -ExecutionPolicy Bypass -File .\selfskill\scripts\run.ps1 configure --batch LLM_API_KEY=<your-key> LLM_BASE_URL=<base-url> LLM_MODEL=<model>"
        exit 0
    }

    & (Join-Path $projectRoot "selfskill\scripts\run.ps1") "start"
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
