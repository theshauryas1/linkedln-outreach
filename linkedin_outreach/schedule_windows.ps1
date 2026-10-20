# PowerShell Script to register LinkedIn Outreach in Windows Task Scheduler
$TaskName = "LinkedInOutreachDaily"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath = Join-Path $ScriptDir "run_outreach.bat"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Registering Windows Task Scheduler Job: $TaskName" -ForegroundColor Cyan
Write-Host "  Schedule: Daily at 9:00 AM" -ForegroundColor Cyan
Write-Host "  Target: $BatPath" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "[INFO] Task '$TaskName' already exists. Unregistering previous version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`""
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily LinkedIn Outreach Automation Agent (9:00 AM)"

Write-Host "`n[SUCCESS] Task '$TaskName' registered successfully!" -ForegroundColor Green
Write-Host "The outreach pipeline will automatically execute every morning at 9:00 AM." -ForegroundColor Green
