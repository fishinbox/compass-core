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
import requests
import json

# third party libs
import netifaces

# agent libs
from common import *




class DiscoveryAgentApp():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/tmp/agent_stdout'
        self.stderr_path = '/tmp/agent_stderr'
        self.pidfile_path =  '/tmp/agent_daemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        from common import Log
        while True:
            try:
                # using service info as primary and configuration file as fallback
                url = getApiUrl()
                if not url:
                    url = getApiUrl(fromConfig=True)
                print('url get')
                headers = {'Content-Type': 'application/json'}
                # get machine info
                machine_info = {}
                with open(CONF.machine_info_file) as file:
                    machine_info = json.load(file)
                print('machine info get')

                # submit machine information to the Compass Service
                # TODO
                r = requests.post(url, data=json.dumps(machine_info), headers=headers)
                print('posted')

                # Again and again
                # wait for n Seconds
                # TODO

                #r = requests.get(url)
                #if r.text == 'reboot':
                #    subprocess.call(['reboot'])
                #    break
            except:
                print('bug at run')
                import traceback
                traceback.print_exc()
            finally:
                time.sleep(5)



agent = DiscoveryAgentApp()
agent_runner = runner.DaemonRunner(agent)
agent_runner.do_action()


