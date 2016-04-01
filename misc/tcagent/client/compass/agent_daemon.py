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

#standard python libs
import time
import subprocess
import socket
import requests
import json

#third party libs
from daemon import runner
import netifaces



class App():
    
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/tmp/agent_stdout'
        self.stderr_path = '/tmp/agent_stderr'
        self.pidfile_path =  '/tmp/agent_daemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        from service_listener import get_server_info
        from common import Log

        Log.debug('enter run')
        address, port = get_server_info()
        # get net iface info
        ifaces = netifaces.interfaces()
        nics= {}
        filtered = ['lo', 'dummy']
        for iface in ifaces:
            nicType = iface.rstrip('1234567890 ')
            if nicType in filtered:
                continue
            MAC = netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr']
            nics[iface]=MAC
        Log.debug((address, port, nics))
        url = 'http://%s:%s/servers' % (address, port)
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url, data=json.dumps(nics), headers=headers)

        while True:
            r = requests.get(url)
            if r.text == 'reboot':
                subprocess.call(['reboot'])
                break
            else:
                time.sleep(5)
                continue


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
