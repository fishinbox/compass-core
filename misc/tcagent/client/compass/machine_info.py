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

# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

# standard python libs
import time
import subprocess
import socket
import json

# third party libs
import netifaces

# agent libs
from common import *
from lshw import getMachineInfo

class MachineInfoApp():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/tmp/machineinfo_stdout'
        self.stderr_path = '/tmp/machineinfo_stderr'
        self.pidfile_path =  '/tmp/machineinfo_daemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        # One time lshw information parse and gathering
        machine_info = getMachineInfo()
        
        mac = machine_info['network']['devices'][0]['mac']
        machine_info_all = {
            "owner_id": getOwnerId(),
            "mac": mac,
            "machine_attribute": machine_info
        }
        with open(CONF.machine_info_file, 'w') as file:
            json.dump(machine_info_all, file)

        while True:
            # Do lldp discovery in the loop
            for network in machine_info['network']['devices']:
                interface = network['name']
                try:
                    with open(CONF.lldp_info_file(interface)) as file:
                        switch = json.load(file)
                        network['switch'] = switch
                except:
                    # Note(ZZR): there may not be all lldp_info for
                    # each interface, ignoreing the exception
                    pass
            # and update the machine info JSON file
            with open(CONF.machine_info_file, 'w') as file:
                json.dump(machine_info_all, file)




            '''
            # get net iface info
            ifaces = netifaces.interfaces()
            nics= {}
            filtered = ['lo', 'dummy', 'tunl', 'tun', 'tap', 'ip_vti']
            for iface in ifaces:
                nicType = iface.rstrip('1234567890 ')
                if nicType in filtered:
                    continue
                MAC = netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr']
                nics[iface]=MAC
                addrs = netifaces.ifaddresses(iface)
            #with open(CONF.machine_info_file, 'w') as outfile:
            #    json.dump(nics, outfile)
            '''
            time.sleep(1)

machineinfo = MachineInfoApp()
machineinfo_runner = runner.DaemonRunner(machineinfo)
machineinfo_runner.do_action()

