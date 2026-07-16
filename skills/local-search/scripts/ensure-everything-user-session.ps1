#Requires -Version 5.1
<#
.SYNOPSIS
    Ensure Voidtools Everything runs in the current user's interactive session,
    not just under Session 0 (LocalSystem service context).

.DESCRIPTION
    Everything's IPC (the mechanism everyfile / this skill use) is only
    reachable from processes in the SAME Windows session. When Everything is
    installed as a service, it runs under Session 0 while the user runs in
    Session 1+, and IPC calls silently fail with "not running".

    This script is IDEMPOTENT: it detects the situation, launches Everything
    in the user session if needed, and does nothing if it's already correct.

.NOTES
    Uses ProcessStartInfo + Verb='runas' pattern for admin elevation (per
    刘工's preference over Start-Process pwsh -Verb RunAs).

    Safe to invoke unattended; exits 0 when the user-session process is
    already running or was successfully started, non-zero on unrecoverable
    error.
#>

[CmdletBinding()]
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor Cyan }
}

function Write-Ok($msg) {
    if (-not $Quiet) { Write-Host "  [OK] $msg" -ForegroundColor Green }
}

function Write-Warn($msg) {
    Write-Host "  [WARN] $msg" -ForegroundColor Yellow
}

function Get-EverythingExe {
    # 1) Query the service (works whether or not Everything is running)
    try {
        $svc = Get-CimInstance Win32_Service |
               Where-Object { $_.Name -match 'verything' } |
               Select-Object -First 1
        if ($svc) {
            # PathName may include quotes and trailing "-svc" args, strip them
            $raw = $svc.PathName.Trim('"')
            $raw = ($raw -split ' -')[0].Trim('"')
            if (Test-Path $raw) { return $raw }
        }
    } catch { }

    # 2) Fall back to common install locations
    $candidates = @(
        "$env:ProgramFiles\Everything\Everything.exe",
        "${env:ProgramFiles(x86)}\Everything\Everything.exe",
        "$env:LOCALAPPDATA\Programs\Everything\Everything.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Get-CurrentSessionId {
    return (Get-Process -Id $PID).SessionId
}

function Test-EverythingInUserSession {
    $sid = Get-CurrentSessionId
    # Process name is 'Everything64' on x64, 'Everything' on x86, and
    # 'Everything-1.5a' etc. on beta builds — match with a wildcard.
    $procs = Get-Process -Name 'Everything*' -ErrorAction SilentlyContinue |
             Where-Object { $_.SessionId -eq $sid }
    return @($procs).Count -gt 0
}

# ─── Main ─────────────────────────────────────────────────────────────────

Write-Info "→ local-search: ensure Everything is in your user session"

$exe = Get-EverythingExe
if (-not $exe) {
    Write-Host "  [FAIL] Everything.exe not found. Install from https://voidtools.com" -ForegroundColor Red
    exit 1
}
Write-Info "  Found: $exe"

if (Test-EverythingInUserSession) {
    $sid = Get-CurrentSessionId
    Write-Ok "Everything already running in session $sid — nothing to do."
    exit 0
}

Write-Warn "Everything not running in your session (only in Session 0 or absent)."
Write-Info "  Launching in user session..."

# Launch WITHOUT admin — Everything itself will elevate if needed. Using a
# plain Start-Process here (no ProcessStartInfo runas) because the launch
# just needs to happen in the current session, not as admin.
try {
    Start-Process -FilePath $exe -WindowStyle Hidden
} catch {
    Write-Host "  [FAIL] Could not launch Everything: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

# Poll for readiness (up to 15 s)
$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    if (Test-EverythingInUserSession) {
        $sid = Get-CurrentSessionId
        Write-Ok "Everything is now running in session $sid."
        exit 0
    }
}

Write-Host "  [FAIL] Everything did not appear in your session within 15 s." -ForegroundColor Red
exit 3
