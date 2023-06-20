# Setup paramaters
param (
	[int]$p,
	[int]$port,
	[string]$a,
	[string]$address,
	[string]$s,
	[string]$settings,
	[switch]$b,
	[switch]$background,
	[switch]$h)

$FAIR_HOME = "$PSScriptRoot\..\"
Push-Location $FAIR_HOME
$FAIR_HOME = $pwd.path
Pop-Location

if ($p -ne 0) {
	if ($port -ne 0) {
		$REG_PORT = $port
	} else {
		$REG_PORT = $p
	}
} else {
	$REG_PORT = 8000
}

if ($a -ne "") {
	if ($address -ne "") {
		$REG_ADDRESS = $address
	} else {
		$REG_ADDRESS = $a
	}
} else {
	$REG_ADDRESS = "127.0.0.1"
}
if ($s -ne "") {
	if ($settings -ne "") {
		$drams = $settings
	} else {
		$drams = $s
	}
} else {
	$drams = "drams.local-settings"
}
if ($b -Or $background) {
	$REG_BACKGROUND = $true
} else {
	$REG_BACKGROUND = $false
}
if ($h) {
	Write-Host "Usage start_fair_registry_windows.ps1"
	Write-Host "[-p <port>][-a <address>][-s <DRAMS Settings>][--background]"
	exit 0
}

$FULL_ADDRESS = "${REG_ADDRESS}:${REG_PORT}"
$Env:DJANGO_SETTINGS_MODULE= "$drams"
Write-Host "Using Django Settings Module $env:DJANGO_SETTINGS_MODULE"

Push-Location $FAIR_HOME

Write-Host "Spawning Server at ${FULL_ADDRESS}"

if ($REG_BACKGROUND) {
	Start-Process pwsh -ArgumentList '-command "Start-Process ${FAIR_HOME}\venv\Scripts\python -NoNewWindow -Args ${FAIR_HOME}\manage.py runserver ${FULL_ADDRESS} -RedirectStandardError ${FAIR_HOME}\output_error.log -RedirectStandardOutput ${FAIR_HOME}\output.log"'
} else {
	Start-Process "${FAIR_HOME}\venv\Scripts\python" -Args "${FAIR_HOME}\manage.py runserver ${FULL_ADDRESS}" -RedirectStandardError "${FAIR_HOME}\output_error.log" -RedirectStandardOutput "${FAIR_HOME}\output.log"
}

Out-File -FilePath "${FAIR_HOME}\session_address.log" -InputObject $REG_ADDRESS -Encoding ASCII
Out-File -FilePath "${FAIR_HOME}\session_port.log" -InputObject $REG_PORT -Encoding ASCII

if ($REG_ADDRESS -eq "0.0.0.0") {
	Write-Host "Bound to all Addresses (0.0.0.0) setting to loopback address 127.0.0.1"
	$REG_ADDRESS = "127.0.0.1"
	$FULL_ADDRESS = "127.0.0.1:${REG_PORT}"
}

for ($count =0; $count -le 4) {
	Start-Sleep -Seconds 1
	try { 
		$Response = Invoke-WebRequest -URI "http://${FULL_ADDRESS}/api"
	} catch [System.Net.WebException] {
	
	}
	if ($Response -ne $null) {
		break
	}
}

try { 
	$Response = Invoke-WebRequest -URI "http://${FULL_ADDRESS}/api"
} catch [System.Net.WebException] {
	Write-Host "Error: $($_.Exception.Message)"
	exit 1
}
if ($Response.StatusCode -ne 200) {
	Write-Host "Error: Server Responded with $Response.StatusCode"
	exit 1
}

Write-Host "Server Started Successfully"
Start-Process "${FAIR_HOME}\venv\Scripts\python" -NoNewWindow -Args "${FAIR_HOME}\manage.py get_token" -RedirectStandardOutput "${FAIR_HOME}\token"
Write-Host "Token Available at ${FAIR_HOME}\token"

if ($REG_BACKGROUND) {
	Write-Host "Server Running in background close this window "
	Write-Host "or run stop_fair_registry_windows.ps1 to stop the server"
}

Pop-Location

