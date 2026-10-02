# Stop the registry servers started from this install by start_fair_registry_windows.
# With no options every one of them is stopped; -p <port> (and -a <address>)
# stops only the server listening there.
param (
	[int]$p,
	[string]$a,
	[switch]$h)

if ($h) {
	Write-Host "Usage stop_fair_registry_windows.ps1 [-p <port>][-a <address>]"
	exit 0
}

$manage = [IO.Path]::GetFullPath("$PSScriptRoot\..\manage.py")

# The server's command line ends "runserver <address>:<port>"; an unset
# address or port matches any
$address = if ($a) { [regex]::Escape($a) } else { "[^:\s]*" }
$port = if ($p) { $p } else { "\d+" }
$pattern = "runserver\s+${address}:${port}\s*$"

Get-CimInstance Win32_Process | Where-Object {
	$_.CommandLine -and
	$_.CommandLine.IndexOf($manage, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
	$_.CommandLine -match $pattern
} | ForEach-Object {
	Write-Host "Stopping Process $($_.ProcessId)"
	Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
