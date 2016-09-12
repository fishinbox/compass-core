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

TMPBASEDIR=/tmp/compass_discovery_agent
SRCDIR=/tmp/compass_discovery_agent/src
WORKDIR=/tmp/compass_discovery_agent/working
TARGETDIR=/tmp/compass_discovery_agent/target

# clear WORK and TARGET directory
sudo rm -rf ${WORKDIR}
sudo rm -rf ${TARGETDIR}

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
	curl -s ${tcz_repo}${app} -o ${SRCDIR}/tczs/${app} --compressed

	deplist=`curl -fs ${tcz_repo}${app}.dep --compressed 2>/dev/null`
	for depapp in $deplist; do
		get_dependencies $depapp 
	done
}


mkdir -p ${SRCDIR}/iso
if [ "$(find ${SRCDIR}/iso -path */core.iso)" == "" ]; then
	echo downloading iso
	curl ${release} -o ${SRCDIR}/iso/core.iso --compressed
fi


mkdir -p ${SRCDIR}/tczs
IFS=',' read -ra DEPS <<< ${dependencies}
for i in ${DEPS[@]}; do
	get_dependencies $i
done

# Get Python Dependencies
download_py()
{
	mkdir -p ${SRCDIR}/py/
	pygz=$1
	py_repo='https://pypi.python.org/'
	echo 'download and compact '$pygz
	py=$(echo $pygz | sed -e 's/\-[0-9\.]*\.tar\.gz$//')
	url=${py_repo}$(curl -s ${py_repo}simple/${py}/ --compressed | grep ${pygz}| sed -e 's/.*href\=\"\.\.\/\.\.\/\([^\"]*\)\#.*/\1/')
	curl -s ${url} -o ${SRCDIR}/py/${pygz} --compressed
	#advdef -z4 ${SRCDIR}/py/${pygz} -q
}

pylist=(
	setuptools-19.6.tar.gz
	netifaces-0.10.4.tar.gz
	pbr-1.8.1.tar.gz
	lockfile-0.12.2.tar.gz
	docutils-0.12.tar.gz
	six-1.10.0.tar.gz
	python-daemon-2.1.1.tar.gz
	requests-2.9.1.tar.gz
	enum34-1.1.6.tar.gz
	zeroconf-0.17.5.tar.gz
    lxml-3.6.0.tar.gz
)

for i in ${pylist[@]}; do
	download_py $i
done

# Get lshw
git clone -b ${lshw_version} ${lshw_repo} ${SRCDIR}/lshw
# Checkout B.02.18 version lshw
git --git-dir=${SRCDIR}/lshw/.git/ checkout B.02.18

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

# Clean pyc
for i in $(find ${BASEDIR}/../client/compass -path *.pyc); do
	rm $i
done
# Copy scripts
sudo cp -r ${BASEDIR}/../client/* ${WORKDIR}/initfs-root/opt/
# Copy Python Dependencies
sudo cp -r ${SRCDIR}/py ${WORKDIR}/initfs-root/opt/

# Copy lshw
sudo cp -r ${SRCDIR}/lshw ${WORKDIR}/initfs-root/opt/

# rebuild initfs image
sudo sh -c "find | cpio -o -H newc | gzip -2 > ${WORKDIR}/iso/${initfs}"

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
#sudo rm -r ${WORKDIR}


