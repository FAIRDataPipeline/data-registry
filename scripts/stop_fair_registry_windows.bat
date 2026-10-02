@ECHO OFF
rem Stop the registry servers started from this install by start_fair_registry_windows.
rem With no options every one of them is stopped; -p PORT (and -a ADDRESS) stops
rem only the server listening there. stop_fair_registry_windows.ps1 does the work.
setlocal

rem The script's folder must be read before any shift, which moves argument 0 too
set "SCRIPT_DIR=%~dp0"
set PORT=
set ADDRESS=

:readargs
if "%~1" == "" goto stop
if "%~1" == "-h" (
    echo Usage stop_fair_registry_windows.bat [-p ^<port^>][-a ^<address^>]
    exit /b 0
)
if "%~1" == "-p" (
    if "%~2" == "" goto missing
    set "PORT=%~2"
    shift
    shift
    goto readargs
)
if "%~1" == "-a" (
    if "%~2" == "" goto missing
    set "ADDRESS=%~2"
    shift
    shift
    goto readargs
)
echo Invalid option %~1 see -h
exit /b 1

:missing
echo Option %~1 needs a value, see -h
exit /b 1

:stop
set STOP_ARGS=
if defined PORT set "STOP_ARGS=-p %PORT%"
if defined ADDRESS set "STOP_ARGS=%STOP_ARGS% -a %ADDRESS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop_fair_registry_windows.ps1" %STOP_ARGS%
exit /b %ERRORLEVEL%
