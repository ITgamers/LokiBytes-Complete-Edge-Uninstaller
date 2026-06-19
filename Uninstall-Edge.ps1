<#
.SYNOPSIS
    Fully removes Microsoft Edge (Chromium) from Windows, including the
    EdgeUpdate service/scheduled tasks and leftover files/registry keys.

.DESCRIPTION
    Microsoft only exposes a real "Uninstall" path for Edge when Windows'
    region (GeoID) is set to an EEA country, due to the Digital Markets Act.
    This script temporarily switches the system region to an EEA country so
    the same uninstall gate that EU users get is unlocked, force-uninstalls
    Edge via its own installer, then cleans up everything that normally gets
    left behind (services, scheduled tasks, registry keys, folders,
    shortcuts), and blocks Windows from silently reinstalling it.

    The Microsoft Edge WebView2 Runtime is deliberately left alone -- it is
    a separate component many third-party apps depend on independently of
    the Edge browser itself.

.PARAMETER TempRegion
    Two-letter EEA country code to switch to temporarily. Default DE (Germany).

.PARAMETER RevertRegionAfter
    If set, switches the region back to its original value after uninstalling.
    Leave unset if you want to verify removal first, then run:
        Set-WinHomeLocation -GeoId <originalGeoId>
    (the original GeoId is printed at the start of the run).

.PARAMETER SkipAutoReinstallBlock
    If set, skips writing the EdgeUpdate policy that stops Edge's own
    background updater from silently reinstalling it. Leave unset (default)
    to keep that block in place. Note that this policy only stops Edge's
    self-updater -- it cannot stop a Windows *feature* update (a full OS
    version upgrade) from re-laying-down Edge's inbox files; re-run this
    script afterward if that happens.

.NOTES
    Must be run from an elevated (Administrator) PowerShell window.
    A reboot is recommended after running.
#>

[CmdletBinding()]
param(
    [string]$TempRegion = "DE",
    [switch]$RevertRegionAfter,
    [switch]$SkipAutoReinstallBlock
)

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Warn2($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator. Right-click PowerShell -> 'Run as administrator', then re-run this script."
    exit 1
}

# EEA member GeoIDs (subset; any EEA country works for the DMA check)
$eeaGeoIds = @{
    "DE" = 94   # Germany
    "FR" = 84   # France
    "NL" = 173  # Netherlands
    "IE" = 68   # Ireland
    "IT" = 118  # Italy
    "ES" = 217  # Spain
}

if (-not $eeaGeoIds.ContainsKey($TempRegion)) {
    Write-Error "Unknown TempRegion '$TempRegion'. Valid: $($eeaGeoIds.Keys -join ', ')"
    exit 1
}

Write-Step "Recording current region"
$originalGeoId = (Get-WinHomeLocation).GeoId
Write-Host "    Current GeoId: $originalGeoId  (save this if you want to revert manually later)"

Write-Step "Switching region to $TempRegion to satisfy Microsoft's EEA/DMA uninstall gate"
Set-WinHomeLocation -GeoId $eeaGeoIds[$TempRegion]

Write-Step "Restarting Explorer so the region change propagates"
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process explorer.exe
Start-Sleep -Seconds 2

Write-Step "Closing Edge and Edge Update processes"
Get-Process msedge*, MicrosoftEdgeUpdate* -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Write-Step "Force-uninstalling Edge via its own installer (system-level)"
$systemSetups = Get-ChildItem "C:\Program Files (x86)\Microsoft\Edge\Application\*\Installer\setup.exe" -ErrorAction SilentlyContinue
if (-not $systemSetups) {
    $systemSetups = Get-ChildItem "C:\Program Files\Microsoft\Edge\Application\*\Installer\setup.exe" -ErrorAction SilentlyContinue
}
foreach ($setup in $systemSetups) {
    Write-Host "    Running: $($setup.FullName)"
    Start-Process -FilePath $setup.FullName `
        -ArgumentList "--uninstall --system-level --verbose-logging --force-uninstall" `
        -Wait -NoNewWindow -ErrorAction SilentlyContinue
}

$userSetups = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Edge\Application\*\Installer\setup.exe" -ErrorAction SilentlyContinue
foreach ($setup in $userSetups) {
    Write-Host "    Running (user-level): $($setup.FullName)"
    Start-Process -FilePath $setup.FullName `
        -ArgumentList "--uninstall --verbose-logging --force-uninstall" `
        -Wait -NoNewWindow -ErrorAction SilentlyContinue
}

if (-not $systemSetups -and -not $userSetups) {
    Write-Warn2 "No setup.exe found -- Edge may already be partially removed. Continuing with cleanup anyway."
}

Write-Step "Removing Edge Update scheduled tasks"
Get-ScheduledTask -TaskName "MicrosoftEdgeUpdate*" -ErrorAction SilentlyContinue |
    Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue

Write-Step "Removing Edge Update services"
foreach ($svc in "edgeupdate", "edgeupdatem") {
    if (Get-Service $svc -ErrorAction SilentlyContinue) {
        Stop-Service $svc -Force -ErrorAction SilentlyContinue
        sc.exe delete $svc | Out-Null
    }
}

Write-Step "Removing leftover Edge directories (WebView2 Runtime is left untouched)"
$paths = @(
    "C:\Program Files (x86)\Microsoft\Edge",
    "C:\Program Files (x86)\Microsoft\EdgeCore",
    "C:\Program Files (x86)\Microsoft\EdgeUpdate",
    "C:\Program Files\Microsoft\Edge",
    "$env:LOCALAPPDATA\Microsoft\Edge",
    "$env:LOCALAPPDATA\Microsoft\EdgeUpdate"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "    Removing $p"
        Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Step "Cleaning leftover registry keys"
$regKeys = @(
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate",
    "HKLM:\SOFTWARE\Microsoft\EdgeUpdate",
    "HKLM:\SOFTWARE\Microsoft\Edge",
    "HKCU:\SOFTWARE\Microsoft\Edge",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft EdgeUpdate",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft EdgeUpdate"
)
foreach ($k in $regKeys) {
    if (Test-Path $k) {
        Write-Host "    Removing $k"
        Remove-Item $k -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Step "Removing shortcuts"
$shortcuts = @(
    "$env:PUBLIC\Desktop\Microsoft Edge.lnk",
    "$env:USERPROFILE\Desktop\Microsoft Edge.lnk",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk"
)
foreach ($s in $shortcuts) {
    if (Test-Path $s) { Remove-Item $s -Force -ErrorAction SilentlyContinue }
}

if (-not $SkipAutoReinstallBlock) {
    Write-Step "Blocking automatic Edge reinstall via Edge Update policy"
    $policyPath = "HKLM:\SOFTWARE\Policies\Microsoft\EdgeUpdate"
    New-Item -Path $policyPath -Force | Out-Null
    New-ItemProperty -Path $policyPath -Name "InstallDefault" -PropertyType DWord -Value 0 -Force | Out-Null
    New-ItemProperty -Path $policyPath -Name "Install{56EB18F8-8008-4CBD-B6D2-8C97FE7E9062}" -PropertyType DWord -Value 0 -Force | Out-Null
}
else {
    Write-Warn2 "Skipping EdgeUpdate auto-reinstall block (opted out)."
}

if ($RevertRegionAfter) {
    Write-Step "Reverting region to original GeoId ($originalGeoId)"
    Set-WinHomeLocation -GeoId $originalGeoId
    Write-Step "Restarting Explorer so the reverted region takes effect immediately"
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Start-Process explorer.exe
}
else {
    Write-Warn2 "Region left as $TempRegion. Revert anytime with: Set-WinHomeLocation -GeoId $originalGeoId"
}

Write-Step "Done. A reboot is recommended to finish removing leftover handles/services."
Write-Warn2 "Note: a future Windows feature update (OS upgrade, not Edge auto-update) can still reinstall Edge -- this script can be re-run if that happens."
