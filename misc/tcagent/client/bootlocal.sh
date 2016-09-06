#!/usr/local/bin/bash
# put other system startup commands here
pylist=( setuptools netifaces pbr lockfile docutils six python-daemon requests enum34 zeroconf lxml)
for i in ${pylist[@]}; do
	f=$(find /opt/py/ -path *$i*.tar.gz)
	cd /tmp
	tar xf $f
	cd /tmp/$(basename $f .tar.gz)
	sudo python setup.py install
done

# compile and install lshw
cd /opt/lshw
make
make install

#wait for network config
SEC=60
while [ $SEC -gt 0 ] ; do
   ifconfig | grep -q "Bcast" && break || sleep 1
   echo -ne "Waiting for IP $((SEC--))  \r"      
done                                       
ifconfig

bash /opt/compass/start_agent.sh

clear

