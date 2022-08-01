Write-Host "Getting Process ID"
$pids = Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%manage.py runserver%'" | Select-Object ProcessId

Foreach ($current_pid in $pids) {
	Write-Host "Stopping Process $current_pid"
	Stop-Process -Id $current_pid.ProcessId -ErrorAction SilentlyContinue
}