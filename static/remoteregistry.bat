@echo off & title %~nx0 & color 5F
set prevwd=%cd%

:: This script requires Python 3, GIT and Chocolatey to be installed, test for this first

:: Test for Python
goto :DOES_PYTHON_EXIST

:DOES_PYTHON_EXIST
python -V | find /v "Python 3" >NUL 2>NUL && (goto :PYTHON_DOES_NOT_EXIST)
python -V | find "Python 3"    >NUL 2>NUL && (goto :PYTHON_DOES_EXIST)
goto :EOF

:PYTHON_DOES_NOT_EXIST
echo Python is not installed or not located in your system path, please ensure it is installed an in the system path
@pause
goto :EOF

:PYTHON_DOES_EXIST
:: Show Python Version
for /f "delims=" %%V in ('python -V') do @set ver=%%V
echo Python, %ver% is installed, continuing...

:: Test For GIT
:DOES_GIT_EXIST
git --version >NUL 2>&1 && (goto :GIT_DOES_EXIST) || (goto :GIT_DOES_NOT_EXIST)

:GIT_DOES_NOT_EXIST
echo Git is not installed or not located in your system path, please ensure it is installed an in the system path
goto :EOF

:GIT_DOES_EXIST
:: Show GIT Version.
for /f "delims=" %%V in ('git --version') do @set ver=%%V
echo Git, %ver% is installed, continuing...

::	Set Default Directory
set FAIR_HOME="%homedrive%%homepath%\.fair\registry"
:: Unset any previous variables
set "GIT_TAG="
set "GIT_BRANCH="
set "SUPERUSER_USERNAME="
set "SUPERUSER_PASSWORD="
set "USE_SUPERUSER="


:readargs
if not "%1" == "" (
    echo Reading Parameter %1...

	if "%1" == "-d" (
		if "%2" == "" (
			echo No Directory Provided.
			exit /b 1
		)
		set FAIR_HOME=%2\registry
		shift
	)
	
	if "%1" == "-b" (
		if "%2" == "" (
			echo No Branch Provided.
			exit /b 1
		)
		set GIT_BRANCH=%2
		shift
	)
	if "%1" == "-t" (
		if "%2" == "" (
			echo No Tag Provided.
			exit /b 1
		)
		set GIT_TAG=%2
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
	if "%1" == "-p" (
		if "%2" == "" (
			echo No password Provided.
			exit /b 1
		)
		set SUPERUSER_PASSWORD=%2
		shift
	)
	if "%1" == "-u" (
		if "%2" == "" (
			echo No username Provided.
			exit /b 1
		)
		set SUPERUSER_USERNAME=%2
		shift
	)
	if "%1" == "--directory" (
		if "%2" == "" (
			echo No Directory Provided.
			exit /b 1
		)
		set FAIR_HOME=%2\registry
		shift
	)
	if "%1" == "--branch" (
		if "%2" == "" (
			echo No Branch Provided.
			exit /b 1
		)
		set GIT_BRANCH=%2
		shift
	)
	if "%1" == "--tag" (
		if "%2" == "" (
			echo No Tag Provided.
			exit /b 1
		)
		set GIT_TAG=%2
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
	if "%1" == "--username" (
		if "%2" == "" (
			echo No username Provided.
			exit /b 1
		)
		set SUPERUSER_USERNAME=%2
		shift
	)
	if "%1" == "--password" (
		if "%2" == "" (
			echo No password Provided.
			exit /b 1
		)
		set SUPERUSER_PASSWORD=%2
		shift
	)
	if "%1" == "-m" (
		set GIT_BRANCH=main
	)
	if "%1" == "--main" (
		set GIT_BRANCH=main
	)
	if "%1" == "-h" (
		echo Usage local_registry.bat
        echo -s|--settings <drams-settings-file> [-d|--directory <directory>][-b|--branch <git-branch>][-t|--tag <git-tag>][-u|--username <superuser-username> -p|--password <superuser-password>]
		exit /b
	)
	
	shift
    goto readargs
)

:: Check if both username and password are set for superuser
if defined SUPERUSER_USERNAME (
	if defined SUPERUSER_PASSWORD (
		echo setting SUPERUSER USERNAME and PASSWORD
		set USE_SUPERUSER=y
	)
	if not defined SUPERUSER_PASSWORD (
		echo SUPERUSER username set without password
		exit /b 1
	)
)
if not defined SUPERUSER_USERNAME (
	if defined SUPERUSER_PASSWORD (
		echo SUPERUSER password set without username
		exit /b 1
	)
)

if not defined DRAMS (
	echo no DRAMS Settings Specified
)


:: Make the Directory
if exist %FAIR_HOME%\ (
	echo Directory %FAIR_HOME% already exists please supply an empty directory
	exit /b 1
)
echo Creating directory %FAIR_HOME%
mkdir %FAIR_HOME%

:: Resolve Absolute Filepath
pushd %FAIR_HOME%
	set FAIR_HOME=%CD%
popd

:: Clone the registry into the directory
if defined GIT_BRANCH (
	echo cloning %GIT_BRANCH% into %FAIR_HOME%
	git clone https://github.com/FAIRDataPipeline/data-registry.git -b %GIT_BRANCH% %FAIR_HOME%
) else (
	git clone https://github.com/FAIRDataPipeline/data-registry.git %FAIR_HOME%
	if not defined GIT_TAG (
		echo Determaning latest tag
		FOR /F %%i IN ('git -C %FAIR_HOME:"=% describe --abbrev^=0 --tags') DO set GIT_TAG=%%i
	)
)
if defined GIT_TAG (
	echo cloning %GIT_TAG% into %FAIR_HOME%
	git -C %FAIR_HOME% checkout tags/%GIT_TAG% >NUL 2>NUL
)

:: install Virtual Environment Module
python -m venv %FAIR_HOME%/venv

:: Activate the Virtual Environment
echo calling "%FAIR_HOME:"=%\venv\scripts\activate.bat" to activate virtual enviroment
call %FAIR_HOME:"=%\venv\Scripts\activate.bat

:: Install Python Dependencies
python -m pip install --upgrade pip wheel
python -m pip install -r "%FAIR_HOME:"=%\local-requirements.txt"

:: Change into FAIR HOME directory
cd /d %FAIR_HOME%

:: Set Environment Variables needed for Django

:: Set Environment Variables needed for Django
set DJANGO_SETTINGS_MODULE=%DRAMS%

@echo Using Django Settings %DJANGO_SETTINGS_MODULE%

if defined USE_SUPERUSER (
	set DJANGO_SUPERUSER_USERNAME=SUPERUSER_USERNAME
	set DJANGO_SUPERUSER_PASSWORD=SUPERUSER_PASSWORD
)


:: Run Migrations
echo running migrations
start /b /wait python manage.py makemigrations custom_user
start /b /wait python manage.py makemigrations data_management
start /b /wait python manage.py migrate
start /b /wait python manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o %FAIR_HOME:"=%\schema.dot
start /b /wait python manage.py collectstatic --noinput > nul 2>&1
if defined USE_SUPERUSER (
	start /b /wait python manage.py createsuperuser --noinput
)
start /b /wait python manage.py set_site_info

:: Finish
echo Complete Exiting Now
cd /d %prevwd%
