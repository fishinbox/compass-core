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

from zeroconf import ServiceBrowser, Zeroconf
import time
import socket
import json

from common import *

class ServiceListener(object):
    service_names = []

    def remove_service(self, zeroconf, type, name):
        self.service_names.remove(name)

    def add_service(self, zeroconf, type, name):
        service = zeroconf.get_service_info(type, name)
        service_host = socket.inet_ntoa(service.address)
        service_port = service.port
        d = {
                'host': service_host,
                'port': service_port
                }
        with open(CONF.service_info_file, 'w') as outfile:
                json.dump(d, outfile)
        self.service_names.append(name)

class ServiceListenerApp():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/tmp/servicelistener_stdout'
        self.stderr_path = '/tmp/servicelistener_stderr'
        self.pidfile_path =  '/tmp/servicelistener_daemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        #Log.debug('get_service_info')
        zeroconf = Zeroconf()
        listener = ServiceListener()
        service_type = "_compass_discovery._tcp.local."

        browser = ServiceBrowser(zeroconf, service_type, listener)
        #Log.debug('enter browser')
        try:
            while True:
                pass
        finally:
            zeroconf.close()

servicelistener = ServiceListenerApp()
servicelistener_runner = runner.DaemonRunner(servicelistener)
servicelistener_runner.do_action()


