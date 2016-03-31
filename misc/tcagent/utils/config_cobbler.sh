#!/bin/bash
# Copyright 2016 Network Intelligence Research Center, 
# Beijing University of Posts and Telecommunications
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

source path.rc
DistroName=test_core
DistroArch=x86_64
ISO=$(readlink -f $1)

# TODO configure cobbler signature

# Check SELinux status
if [ $(getenforce) == 'Enforcing' ]; then
	# workaround
	sudo setenforce 0
fi

# Check cobblerd service
if [ "$(ps -ef | grep cobblerd | grep -v grep)" == '' ]; then
	sudo systemctl start cobblerd
fi

# Check distro status
if [ "$(sudo cobbler distro find --name=${DistroName}-${DistroArch})" != "" ]; then
	if [ "$(sudo cobbler distro find --name=${DistroName}-${DistroArch}.orig)" != "" ]; then
		sudo cobbler distro remove --name=${DistroName}-${DistroArch}.orig
	fi
	if [ "$(sudo cobbler profile find --name=${DistroName}-${DistroArch}.orig)" != "" ]; then
		sudo cobbler profile remove --name=${DistroName}-${DistroArch}.orig
	fi
	sudo cobbler distro rename \
		--name=${DistroName}-${DistroArch} \
		--newname=${DistroName}-${DistroArch}.orig
	sudo cobbler profile rename \
		--name=${DistroName}-${DistroArch} \
		--newname=${DistroName}-${DistroArch}.orig
fi

# import new distro
mkdir -p ${BASEDIR}/tmp/working/mnt
sudo mount -o loop $ISO ${BASEDIR}/tmp/working/mnt
sudo cobbler import --name=${DistroName} --arch=${DistroArch} --path=${BASEDIR}/tmp/working/mnt
sudo umount ${BASEDIR}/tmp/working/mnt
#rm -r ${BASEDIR}/tmp/working

# Check system status
if [ "$(sudo cobbler system find --name=default)" == "" ]; then
	sudo cobbler system create --name=default
fi

# Update system
sudo cobbler system edit --name=default --profile=${DistroName}-${DistroArch}

# Sync
sudo cobbler sync
