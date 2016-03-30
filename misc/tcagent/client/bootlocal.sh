#!/usr/local/bin/bash
# put other system startup commands here
pylist=( setuptools netifaces pbr lockfile docutils six python-daemon)
for i in ${pylist[@]}; do
	f=$(find /opt/py/ -path *$i*.tar.gz)
	cd /tmp
	tar xf $f
	cd /tmp/$(basename $f .tar.gz)
	sudo python setup.py install
done

python /opt/compass/agent_daemon.py start
