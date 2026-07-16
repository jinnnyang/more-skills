<#
.SYNOPSIS
    Install / refresh the local-search CLI as a uv tool (editable).

.DESCRIPTION
    Idempotent: safe to re-run after pulling changes. --force refreshes the
    venv contents without disturbing the CLI on PATH.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$SkillDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Write-Host "-> Installing local-search from $SkillDir" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  [FAIL] uv not found. Install from https://astral.sh/uv" -ForegroundColor Red
    exit 1
}

& uv tool install --editable $SkillDir --force
Write-Host ""

Write-Host "-> Verifying" -ForegroundColor Cyan
& local-search --version
Write-Host ""
try { & local-search doctor } catch { }
Write-Host ""
Write-Host "OK Done. Run 'local-search --help' to see commands." -ForegroundColor Green
