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
            echo "Script to install a local registry with options to specify the DRAMS settings file, directory and git branch or tag"
            echo "/bin/bash -c localregistry.sh [-d <install-directory>]"
            echo "                               [-t <git-tag> | -b <git-branch> | -p | -m ]"
            echo ""
            echo "Arguments:"
            echo "    -d                  Install directory"
            echo "    -b <git-branch>     Install from specific git branch"
            echo "    -t <git-tag>        Install from specific git tag"
            echo "    -p                  Install from latest pre-release"
            echo "    -m                  Install from latest state of branch 'main'"
            exit 0
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
        -p|--prerelease)
            GIT_PRE_RELEASE=$1
        ;;
        -m|--main)
            GIT_BRANCH="main"
        ;;
    esac
    shift
done

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
elif [ ! -z $(echo ${GIT_PRE_RELEASE} | xargs) ]; then
    TAG=`curl --silent "https://api.github.com/repos/FAIRDataPipeline/data-registry/releases" | sed -n 's/^.*"tag_name": "\(v.*\)",.*$/\1/p' | sort -r -V | head -n 1`
    echo "Cloning tag $TAG"
    git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
    cd "$FAIR_HOME"
    git checkout tags/$TAG > /dev/null 2>&1
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
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd "$FAIR_HOME"/scripts || exit
./rebuild-local.sh
