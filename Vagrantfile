# -*- mode: ruby -*-
# vi: set ft=ruby :

#
# A VM can be created using the command "vagrant up"
#
# This will make a local version of the registry running in a VM.
# You can connect to the registry via http://192.168.20.10:8000
#

Vagrant.configure("2") do |config|

    config.vm.box = "bento/ubuntu-20.04"

    # sync folder containing data registry code
    config.vm.synced_folder ".", "/code/data-registry"

    config.vm.network "private_network", ip: "192.168.20.10"
    config.vm.network "forwarded_port", guest: 8000, host: 8000
    config.vm.provision :shell, inline: <<SHELL
set -x

mkdir -p /root/.ssh
cp ~vagrant/.ssh/authorized_keys /root/.ssh

apt-get update -y
apt-get install -y python3-venv graphviz

export FAIR_HOME=/code/data-registry
rm -rf "$FAIR_HOME"/venv
python3 -m venv "$FAIR_HOME"/venv --copies
source "$FAIR_HOME"/venv/bin/activate

# An issue with virtualbox can lead to issues when reinstalling the VM
# see https://www.virtualbox.org/ticket/8761 
# a work around for this is to use the --ignore-installed option for pip
python -m pip install --upgrade pip wheel --ignore-installed
python -m pip install -r "$FAIR_HOME"/local-requirements.txt  --ignore-installed

export DJANGO_SETTINGS_MODULE="drams.vagrant-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin

cd "$FAIR_HOME"/scripts || exit

./rebuild-local.sh
./start_fair_registry_vagrant

SHELL

end
