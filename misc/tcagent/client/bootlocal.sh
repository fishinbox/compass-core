#!/usr/local/bin/bash
# put other system startup commands here
pylist=( setuptools netifaces pbr lockfile docutils six python-daemon requests)
for i in ${pylist[@]}; do
	f=$(find /opt/py/ -path *$i*.tar.gz)
	cd /tmp
	tar xf $f
	cd /tmp/$(basename $f .tar.gz)
	sudo python setup.py install
done

#wait for network config
SEC=60
while [ $SEC -gt 0 ] ; do
   ifconfig | grep -q "Bcast" && break || sleep 1
   echo -ne "Waiting for IP $((SEC--))  \r"      
done                                       
ifconfig

python /opt/compass/agent_daemon.py start

clear

