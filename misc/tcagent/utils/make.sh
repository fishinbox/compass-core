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

. ./image.conf
source path.rc

TMPBASEDIR=/tmp/tcagent
SRCDIR=/tmp/tcagent/src
WORKDIR=/tmp/tcagent/working
TARGETDIR=/tmp/tcagent/target

# make directories
mkdir -p ${SRCDIR}
mkdir -p ${WORKDIR}
mkdir -p ${TARGETDIR}

# start download

get_dependencies ()
{
	app=${1}
	#echo ${app} dependencies are ${app}.dep
	if [ "$(find ${TMPBASEDIR} -path */${app} )" != "" ]; then
		return
	fi
	echo downloading ${app}
	curl -s ${tcz_repo}${app} -o ${SRCDIR}/tczs/${app}

	deplist=`curl -fs ${tcz_repo}${app}.dep 2>/dev/null`
	for depapp in $deplist; do
		get_dependencies $depapp 
	done
}


mkdir -p ${SRCDIR}/iso
if [ "$(find ${SRCDIR}/iso -path */core.iso)" == "" ]; then
	echo downloading iso
	curl ${release} -o ${SRCDIR}/iso/core.iso
fi


mkdir -p ${SRCDIR}/tczs
IFS=',' read -ra DEPS <<< ${dependencies}
for i in ${DEPS[@]}; do
	get_dependencies $i
done
# start working
# iso root
mkdir -p ${SRCDIR}/mnt
sudo mount -o loop ${SRCDIR}/iso/core.iso ${SRCDIR}/mnt
mkdir -p ${WORKDIR}/iso
sudo cp -rp ${SRCDIR}/mnt/* ${WORKDIR}/iso/

# extract initfs
mkdir -p ${WORKDIR}/initfs-root
cd ${WORKDIR}/initfs-root
sudo sh -c "zcat ${WORKDIR}/iso/${initfs} | cpio -i -H newc -d"

echo 'doing squash'
mkdir -p ${WORKDIR}
# unsquash tcz
ls ${SRCDIR}/tczs/
for i in $( ls ${SRCDIR}/tczs/ ); do
	if [ -f ${SRCDIR}/tczs/$i ]; then
		echo 
		echo ${SRCDIR}/tczs/$i
		unsquashfs -n -d ${WORKDIR}/squashfs-root/ -f ${SRCDIR}/tczs/$i
	fi
done

# 2nd time extract
for i in $(find ${TMPBASEDIR} -path ${WORKDIR}/squashfs-root/*.tar.gz); do
	echo $i
	tar xf $i -C ${WORKDIR}/squashfs-root/
done

# Copyback
sudo cp -rp ${WORKDIR}/squashfs-root/* ${WORKDIR}/initfs-root/

# Copy scripts
for i in $(find ${BASEDIR}/../client/compass -path *.pyc); do
	rm $i
done
sudo cp -r ${BASEDIR}/../client/* ${WORKDIR}/initfs-root/opt/

# rebuild initfs image
sudo sh -c "find | cpio -o -H newc | gzip -9 > ${WORKDIR}/iso/${initfs}"

# make ISO image
sudo mkisofs -l -J -r \
-no-emul-boot \
-boot-load-size 4 \
-boot-info-table \
-b boot/isolinux/isolinux.bin \
-c boot/isolinux/boot.cat \
-o ${TARGETDIR}/core.iso ${WORKDIR}/iso/

# backup
ISODIR=${BASEDIR}/../iso
if [[ -f ${ISOPATH} ]]; then
    echo 'found existing core image, backing-up'
    mv $ISODIR/core.iso ${ISODIR}/core.iso.backup.$(date +%Y%m%d_%H%M%S)
fi
# copy new ISO
cp ${TARGETDIR}/core.iso $ISODIR/core.iso

# clean
sudo umount ${SRCDIR}/mnt
#sudo rm -r ${WORKDIR}/


