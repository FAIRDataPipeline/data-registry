@ECHO OFF
echo Getting Process ID

for /f "usebackq delims=" %%T in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*manage.py*runserver*' } | Select-Object -First 1 -ExpandProperty ProcessId)"`) do set "ProcessId=%%T"
if not defined ProcessId (
    echo No matching process found.
    goto :eof
)

echo Stopping ProcessId = %ProcessId%
taskkill /F /PID %ProcessId% /T 2> nul
