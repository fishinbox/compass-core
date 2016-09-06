#!/usr/bin/bash

python /opt/compass/agent_daemon.py start
python /opt/compass/service_listener.py start
python /opt/compass/machine_info.py start
python /opt/compass/lldp_info.py start
