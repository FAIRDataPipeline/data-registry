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

set /a PORT=8000
if "%1"=="-p" (set /a PORT=%2)
echo setting port to %PORT%

set FAIR_HOME="%homedrive%%homepath%\.fair\registry"

cd %FAIR_HOME%

:: Set Environment Variables needed for Django
setx DJANGO_SETTINGS_MODULE "drams.local-settings"

:: Because Windows use refreshenv from chocolatey to refresh environmental variables without restart
echo refreshing enviromental variables
call refreshenv

@echo Spawning Server
start %FAIR_HOME:"=%\venv\scripts\python.exe %FAIR_HOME:"=%/manage.py runserver %PORT%  1> %FAIR_HOME:"=%\output.log 2>&1

echo %PORT% > %FAIR_HOME:"=%\session_port.log

echo waiting for server to start

set /A count=0
:wait_for_server
	if %count%==6 (echo Server Timed Out Please try again) && (cd %prevwd%) && (GOTO :EOF)
	set /a count=%count%+1
	::echo count is %count%
	timeout /t 5
	curl localhost:%PORT% >NUL 2>&1 && (goto END) || (goto wait_for_server)	
:END

echo Server Started Successfully

call %FAIR_HOME:"=%\venv\Scripts\python %FAIR_HOME:"=%\manage.py get_token > %FAIR_HOME:"=%\token 2>&1
echo Token available at %FAIR_HOME:"=%\token

cd %prevwd%
@pause