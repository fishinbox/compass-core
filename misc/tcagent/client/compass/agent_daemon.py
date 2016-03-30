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

#third party libs
from daemon import runner
from service_listener import get_server_info

class App():
    
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path =  '/tmp/agent_daemon.pid'
        self.pidfile_timeout = 5   

    def run(self):
        address, port, nics = get_server_info()
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((address, port))
        clientsocket.send(str(nics))

        while True:
            data = clientsocket.recv(64)
            if data == 'reboot':
                subprocess.call(['reboot'])
                break
            if data == '':
                time.sleep(5)
                continue


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
