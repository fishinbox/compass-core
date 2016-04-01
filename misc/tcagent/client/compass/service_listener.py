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
import netifaces

from common import *

class ServiceListener(object):
    service_names = []
 
    def remove_service(self, zeroconf, type, name):
        self.service_names.remove(name)
 
    def add_service(self, zeroconf, type, name):
        self.service_names.append(name)
 

def get_server_info():
    Log.debug('get_service_info')
    zeroconf = Zeroconf()
    listener = ServiceListener()
    service_type = "_compass_discovery._tcp.local."

    browser = ServiceBrowser(zeroconf, service_type, listener)
    Log.debug('enter browser')
   
    try:
        Log.debug('enter try')
        while len(listener.service_names)<=0:
            pass
        Log.debug('tried')
        name = listener.service_names[0]
        service = zeroconf.get_service_info(service_type, name)
        address = socket.inet_ntoa(service.address)
        port = service.port
        # get net iface info
        ifaces = netifaces.interfaces()
        nics= {}
        for iface in ifaces:
            if iface.startswith('lo'):
                continue
            MAC = netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr']
            nics[iface]=MAC
        return (address, port, nics)
    finally:
        zeroconf.close()
        # for nicely shutdown
        time.sleep(1)

