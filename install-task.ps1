param([string]$At = '09:00')
$ErrorActionPreference = 'Stop'
$when = [datetime]::ParseExact($At, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$scriptPath = Join-Path $PSScriptRoot 'checkin.py'
if (!(Test-Path -LiteralPath $pythonPath)) { throw '请先运行 setup.ps1' }
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'session.json'))) { throw '请先运行 checkin.py login' }
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument ('"' + $scriptPath + '" run') -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $when
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'AbleSci-Daily-Checkin' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description '科研通每日签到，日志保存在程序目录 logs' -Force | Out-Null
Write-Host "已设置每天本机时间 $At 运行；需电脑开机且当前 Windows 用户已登录。"
