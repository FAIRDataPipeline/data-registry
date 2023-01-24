#!/bin/bash
set -e
INSTALL_DIR=$HOME/.fair
while [ -n "$1" ]; do
    case $1 in
        -d|--directory)
        if [ -z $(echo $2 | xargs) ]; then
            echo "No install directory provided."
            exit 1
        fi
        INSTALL_DIR=$2
        ;;
        -h|--help)
            echo "/bin/bash -c localregistry.sh -s|--settings <drams-settings-file>"
            echo "[-d|--directory <directory>][-b|--branch <git-branch>][-t|--tag <git-tag>][-u|--username <superuser-username> -p|--password <superuser-password>]"                              
            echo ""
            echo "Arguments:"
            echo "    -s|--settings <drams-settings>                Drams Settings"
            echo "    -d|--directory <directory>                    Install directory"
            echo "    -b|--branch <git-branch>                      Install from specific git branch"
            echo "    -t|--tag <git-tag>                            Install from specific git tag"
            echo "    -u|--username <superuser-username>            SUPERUSER username"
            echo "    -p|--password <superuser-password>            SUPERUSER password"
            echo "    -m                                            Install from latest state of branch 'main'"
            exit 0
        ;;
        -s|--settings)
        if [ -z $(echo $2 | xargs) ]; then
            echo "No DRAMS settings provided."
            exit 1
        fi
        DRAMS=$2
        ;;
        -u|--username)
        if [ -z $(echo $2 | xargs) ]; then
            echo "No SUPERUSER username provided."
            exit 1
        fi
        SUPERUSER_USERNAME=$2
        ;;
        -p|--password)
        if [ -z $(echo $2 | xargs) ]; then
            echo "No SUPERUSER password provided."
            exit 1
        fi
        SUPERUSER_PASSWORD=$2
        ;;
        -t|--tag)
            if [ -z $(echo $2 | xargs) ]; then
                echo "No tag provided."
                exit 1
            fi
            GIT_TAG=$2
        ;;
        -b|--branch)
            if [ -z $(echo $2 | xargs) ]; then
                echo "No branch provided."
                exit 1
            fi
            GIT_BRANCH=$2
        ;;
        -m|--main)
            GIT_BRANCH="main"
        ;;
    esac
    shift
done

# Check SUPERUSER username and password
if [ ! -z $(echo ${SUPERUSER_USERNAME} | xargs) ]; then
    if [ -z $(echo ${SUPERUSER_PASSWORD} | xargs) ]; then
        echo "SUPERUSER username set without password"
        exit 1
    else
        echo "Setting SUPERUSER username and password"
        USE_SUPERUSER="True"
    fi
fi
if [ ! -z $(echo ${SUPERUSER_PASSWORD} | xargs) ]; then
    if [ -z $(echo ${SUPERUSER_USERNAME} | xargs) ]; then
        echo "SUPERUSER password set without username"
        exit 1
    fi
fi

# Check for DRAMS
if [ -z $(echo ${DRAMS} | xargs) ]; then
    echo "No DRAMS provided"
    exit 1
fi

export FAIR_HOME="$([[ $INSTALL_DIR = /* ]] && echo $INSTALL_DIR || echo $PWD/${INSTALL_DIR#./})/registry"
echo "Installing to '$FAIR_HOME'"

mkdir -p "$FAIR_HOME"

if [ ! -z $(echo ${GIT_TAG} | xargs) ]; then
    git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
    cd "$FAIR_HOME"
    git checkout tags/${GIT_TAG} > /dev/null 2>&1
elif [ ! -z $(echo ${GIT_BRANCH} | xargs) ]; then
    echo "Cloning branch ${GIT_BRANCH}"
    git clone https://github.com/FAIRDataPipeline/data-registry.git -b ${GIT_BRANCH} "$FAIR_HOME" > /dev/null 2>&1
else
    TAG=`curl --silent "https://api.github.com/repos/FAIRDataPipeline/data-registry/releases/latest" | sed -n 's/^.*"tag_name": "\(v.*\)",.*$/\1/p'`
    echo "Cloning tag $TAG"
    git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
    cd "$FAIR_HOME"
    git checkout tags/$TAG > /dev/null 2>&1
fi

python3 -m venv "$FAIR_HOME"/venv
source "$FAIR_HOME"/venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r "$FAIR_HOME"/local-requirements.txt
export DJANGO_SETTINGS_MODULE=$DRAMS
if [ ! -z $(echo ${USE_SUPERUSER} | xargs) ]; then
    export DJANGO_SUPERUSER_USERNAME=$SUPERUSER_USERNAME
    export DJANGO_SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD
    export FAIR_USE_SUPERUSER="True"
fi
cd "$FAIR_HOME"/scripts || exit
./rebuild.sh
