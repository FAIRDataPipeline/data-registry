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

echo calling "%FAIR_HOME:"=%venv\Scripts\activate.bat" to activate virtual enviroment
call %FAIR_HOME:"=%venv\Scripts\activate.bat

set /a PORT=8000
set ADDRESS=127.0.0.1
set /a LOG=1

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
	if "%1" == "--no-log" (
		set /a LOG=0
	)
	if "%1" == "-h" (
		echo Usage start_fair_registry.bat [-p <port>][-a <address>][<--no-log>]
		exit /b
	)
	shift
    goto readargs
)

set FULL_ADDRESS=%ADDRESS%:%PORT%

cd %FAIR_HOME%

:: Set Environment Variables needed for Django
setx DJANGO_SETTINGS_MODULE "drams.local-settings"

:: Because Windows use refreshenv from chocolatey to refresh environmental variables without restart
echo refreshing enviromental variables
call refreshenv

echo calling "%FAIR_HOME:"=%venv\Scripts\activate.bat" to activate virtual enviroment
call %FAIR_HOME:"=%venv\Scripts\activate.bat

set COMMAND=['python', '%FAIR_HOME:"=%manage.py', 'runserver', '%FULL_ADDRESS%']

@echo Spawning Server at %FULL_ADDRESS%
if %LOG%==0 (
	echo Disabling Logging
	python -c "import subprocess;start_ = subprocess.Popen(%COMMAND%, stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=False); start_.wait()"
) else (
	python %FAIR_HOME:"=%manage.py runserver %FULL_ADDRESS% 1> %FAIR_HOME:"=%\output.log 2>&1
)

echo Writing Session and Port Info
echo %PORT% > %FAIR_HOME:"=%session_port.log
echo %ADDRESS% > %FAIR_HOME:"=%session_address.log

echo waiting for server to start

set /A count=0
:wait_for_server
	if %count%==3 (echo Server Timed Out Please try again) && (cd %prevwd%) && (GOTO :EOF)
	set /a count=%count%+1
	::echo count is %count%
	start /wait timeout 5
	curl %FULL_ADDRESS% >NUL 2>&1 && (goto END) || (goto wait_for_server)	
:END

echo Server Started Successfully

call %FAIR_HOME:"=%venv\Scripts\python %FAIR_HOME:"=%manage.py get_token > %FAIR_HOME:"=%\token 2>&1
echo Token available at %FAIR_HOME:"=%\token

cd %prevwd%
