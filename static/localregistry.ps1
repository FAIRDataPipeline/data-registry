# Setup paramaters
param (
	[string]$d,
	[string]$directory,
	[string]$branch,
	[string]$tag,
	[string]$t,
	[string]$b,
	[switch]$m,
	[switch]$main,
	[switch]$h)

# Check for Python
$p = &{python -V} 2>&1
# check if an ErrorRecord was returned
$version = if($p -is [System.Management.Automation.ErrorRecord])
{
    # grab the version string from the error message
    $p.Exception.Message
	Write-Host "Python is not installed or not located in your system path, please ensure it is installed an in the system path"
	exit 1
}
else 
{
    # otherwise return as is
	Write-Host "Python Found: $p"
    $p
}
# Check for git
$g = &{git --version} 2>&1
# check if an ErrorRecord was returned
$version = if($g -is [System.Management.Automation.ErrorRecord])
{
    # grab the version string from the error message
    $g.Exception.Message
	Write-Host "Git is not installed or not located in your system path, please ensure it is installed an in the system path"
	exit 1
}
else 
{
    # otherwise return as is
	Write-Host "Git Found: $g"
    $g
}

$FAIR_HOME = "$Env:homedrive$Env:homepath\.fair\registry"

# Check Parameters
if ($d -ne "") {
	if ($directory -ne "") {
		$FAIR_HOME = "$directory\registry"
	} else {
		$FAIR_HOME = "$d\registry"
	}
} 
if ($b -ne "") {
	if ($branch -ne "") {
		$GIT_BRANCH = $branch
	} else {
		$GIT_BRANCH = $b
	}
}
if ($t -ne "") {
	if ($tag -ne "") {
		$GIT_TAG = $tag
	} else {
		$GIT_TAG = $t
	}
}
if ($m -Or $main) {
	$GIT_BRANCH = "main"
}
if ($h) {
	Write-Host "Usage local_registry.ps1"
	Write-Host "[-d <directory>][-b <git-branch>][-t <git-tag>]"
	exit 0
}

# Make the Directory
if (Test-Path -Path $FAIR_HOME) {
	Write-Host "Directory ${FAIR_HOME} already exists please supply an empty directory"
	exit 1
}
New-Item $FAIR_HOME -itemType Directory | Out-Null

Push-Location $FAIR_HOME
$FAIR_HOME = $pwd.path
Pop-Location

if ($GIT_BRANCH -ne $null) {
	Write-Host "Cloning ${GIT_BRANCH} into ${FAIR_HOME}"
	git clone https://github.com/FAIRDataPipeline/data-registry.git -b ${GIT_BRANCH} ${FAIR_HOME} *> $null
} else {
	git clone https://github.com/FAIRDataPipeline/data-registry.git ${FAIR_HOME} *> $null
	$GIT_TAG = git -C ${FAIR_HOME} for-each-ref refs/tags --sort=-taggerdate --format='%(refname:short)' --count=1
	Write-Host "GIT_TAG set to $GIT_TAG"
}
if ($GIT_TAG -ne $null) {
	Write-Host "Cloning ${GIT_TAG} into ${FAIR_HOME}"
	git -C ${FAIR_HOME} checkout tags/${GIT_TAG} *> $null
}

python -m venv ${FAIR_HOME}/venv

Write-Host "calling ${FAIR_HOME}\venv\scripts\activate.ps1 to activate virtual enviroment"
& ${FAIR_HOME}\venv\Scripts\activate.ps1

# Install Python Dependencies
python -m pip install --upgrade pip wheel
python -m pip install -r "${FAIR_HOME}\local-requirements.txt"

$Env:DJANGO_SETTINGS_MODULE= "drams.local-settings"
$Env:DJANGO_SUPERUSER_USERNAME= "admin"
$Env:DJANGO_SUPERUSER_PASSWORD= "admin"

Push-Location $FAIR_HOME

Write-Host "Running Migrations"
python manage.py makemigrations custom_user
python manage.py makemigrations data_management
python manage.py migrate
python manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o ${FAIR_HOME}\schema.dot
python manage.py collectstatic --noinput *> $null
python manage.py createsuperuser --noinput

Pop-Location