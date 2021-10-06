@echo off & title %~nx0 & color 5F

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

:: Test for Chocolatey
:DOES_CHOCOLATEY_EXIST
chocolatey -v >NUL 2>&1 && (goto :CHOCOLATEY_DOES_EXIST) || (goto :CHOCOLATEY_DOES_NOT_EXIST)

:CHOCOLATEY_DOES_NOT_EXIST
echo Chocolatey is not installed or not located in your system path, please ensure it is installed an in the system path
goto :EOF

:CHOCOLATEY_DOES_EXIST
:: Show Chocolatey Version.
for /f "delims=" %%V in ('chocolatey -v') do @set ver=%%V
echo Chocolatey, %ver% is installed, continuing...

:: Make the Directory
set FAIR_HOME="%homedrive%%homepath%\.fair\registry"
mkdir %FAIR_HOME%

:: Clone the registry into the directory
git clone https://github.com/FAIRDataPipeline/data-registry.git %FAIR_HOME%

:: install Virtual Environment Module
python -m venv %FAIR_HOME%/venv

:: Activate the Virtual Environment
echo calling "%FAIR_HOME:"=%\venv\scripts\activate.bat" to activate virtual enviroment
call %FAIR_HOME:"=%\venv\Scripts\activate.bat

:: Install Python Dependencies
python -m pip install --upgrade pip wheel
python -m pip install -r "%FAIR_HOME:"=%\local-requirements.txt"

:: Change into FAIR HOME directory
cd %FAIR_HOME%

:: Set Environment Variables needed for Django
setx DJANGO_SETTINGS_MODULE "drams.local-settings"
setx DJANGO_SUPERUSER_USERNAME admin
setx DJANGO_SUPERUSER_PASSWORD admin

:: Because Windows use refreshenv from chocolatey to refresh environmental variables without restart
echo refreshing enviromental variables
call refreshenv

:: Reactivate Virtual Environment after refreshing environmental variables
echo calling "%FAIR_HOME:"=%\venv\scripts\activate.bat" to activate virtual enviroment
call %FAIR_HOME:"=%\venv\Scripts\activate.bat

:: Run Migrations
echo running migrations
python manage.py makemigrations custom_user
python manage.py makemigrations data_management
python manage.py migrate
python manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o %FAIR_HOME:"=%\schema.dot
python manage.py collectstatic --noinput > nul 2>&1
python manage.py createsuperuser --noinput

:: Finish
echo Complete Exiting Now
