@echo off

set prevwd=%cd%

:: Test for curl
goto :DOES_CURL_EXIST

:DOES_CURL_EXIST
curl -V >NUL 2>&1 && (goto :CURL_DOES_EXIST) || (goto :CURL_DOES_NOT_EXIST)

:CURL_DOES_NOT_EXIST
echo CURL is not installed or not located in your system path, please ensure it is installed an in the system path
goto :EOF

:CURL_DOES_EXIST
:: Show CURL Version
for /f "delims=" %%V in ('curl -V') do @set ver=%%V
echo curl, %ver% is installed, continuing...

set FAIR_HOME="%~dp0\..\"

:: Resolve Absolute Filepath
pushd %FAIR_HOME%
	set FAIR_HOME=%CD%\
popd

if not exist "%FAIR_HOME%venv\Scripts\" (
	echo VENV Direcory does not exist, did you install using local_registry.bat?
	exit /b 1
)

set /a PORT=8000
set ADDRESS=127.0.0.1
set /a BACKGROUND=0
set DRAMS=drams.local-settings

:readargs
rem if %1 is blank, we are finished
if not "%1" == "" (
    echo Reading Parameter %1...

	if "%1" == "-p" (
		if "%2" == "" (
			echo No Port Provided.
			exit /b 1
		)
		set /a PORT=%2
		shift
	)
	if "%1" == "-a" (
		if "%2" == "" (
			echo No Address Provided.
			exit /b 1
		)
		set ADDRESS=%2
		shift
	)
	if "%1" == "-s" (
		if "%2" == "" (
			echo No DRAMS settings Provided.
			exit /b 1
		)
		set DRAMS=%2
		shift
	)
	
	if "%1" == "--port" (
		if "%2" == "" (
			echo No Port Provided.
			exit /b 1
		)
		set /a PORT=%2
		shift
	)
	if "%1" == "--address" (
		if "%2" == "" (
			echo No Address Provided.
			exit /b 1
		)
		set ADDRESS=%2
		shift
	)
	if "%1" == "--settings" (
		if "%2" == "" (
			echo No DRAMS Settings Provided.
			exit /b 1
		)
		set DRAMS=%2
		shift
	)
	if "%1" == "-b" (
		set /a BACKGROUND=1
	)
	if "%1" == "--background" (
		set /a BACKGROUND=1
	)
	if "%1" == "-h" (
		echo Usage start_fair_registry_windows.bat [-p <port>][-a <address>][-s <drams settings>][--background]
		exit /b
	)
	shift
    goto readargs
)

set FULL_ADDRESS=%ADDRESS%:%PORT%

cd /d %FAIR_HOME%

:: Set Environment Variables needed for Django
set DJANGO_SETTINGS_MODULE=%DRAMS%

@echo Using Django Settings %DJANGO_SETTINGS_MODULE%

@echo Spawning Server at %FULL_ADDRESS%

if %BACKGROUND%==0 (
	start "" "%FAIR_HOME%\venv\Scripts\python" "%FAIR_HOME%manage.py" runserver %FULL_ADDRESS% 1> "%FAIR_HOME%\output.log" 2>&1
) else (
	start /b "" "%FAIR_HOME%\venv\Scripts\python" "%FAIR_HOME%manage.py" runserver %FULL_ADDRESS% 1> "%FAIR_HOME%\output.log" 2>&1
)

echo Writing Session and Port Info
echo %PORT% > "%FAIR_HOME%session_port.log"
echo %ADDRESS% > "%FAIR_HOME%session_address.log"

if %ADDRESS%==0.0.0.0 (
	echo Bound to All Addresses ^(0.0.0.0^) setting to loopback address 127.0.0.1
	set ADDRESS=127.0.0.1
	set FULL_ADDRESs=127.0.0.1:%PORT%
)

echo waiting for server to start

set /A count=0
:wait_for_server
	if %count%==3 (echo Server Timed Out Please try again) && (cd %prevwd%) && (GOTO :EOF)
	set /a count=%count%+1
	::echo count is %count%
	start /wait timeout 5
	curl http://%FULL_ADDRESS% >NUL 2>&1 && (goto END) || (goto wait_for_server)	
:END

echo Server Started Successfully

call "%FAIR_HOME%\venv\Scripts\python" "%FAIR_HOME%manage.py" get_token > "%FAIR_HOME%token" 2>&1
echo Token available at "%FAIR_HOME%token"

cd /d %prevwd%

if %BACKGROUND%==1 (	
	color a0
	echo Server Running in background close this window  
	echo or run stop_fair_registry_windows.bat to stop the server
)