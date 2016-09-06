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

import logging
import ConfigParser
import json

from daemon import runner


logging.basicConfig(filename='/tmp/agent_%s.log' % __name__, level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
Log = logging.getLogger(__name__)


def getApiUrlFromServiceInfo():
    try:
        with open(CONF.service_info_file) as data_file:
            d = json.load(data_file)
            return 'http://%s:%s/machines' % (d['host'], d['port'])
    except:
        return None


def getApiUrlFromConfig():
	config = ConfigParser.RawConfigParser()
	config.read('agent.conf')
	try:
		api_server = config.get('DEFAULT','api_server')
		api_port = config.get('DEFAULT','api_port')
		return 'http://%s:%s/machines' % (api_server, api_port)
	except:
		Log.debug('No api_server')
		return None


def getApiUrl(fromConfig=False):
    return getApiUrlFromConfig() if fromConfig else getApiUrlFromServiceInfo()


#owner_id is a boot param configured by cobbler "kopts"
def getOwnerId():
    fh = open("/proc/cmdline")
    str = fh.read()
    params = str.split(" ")
    for param in params:
        if "owner_id" in param:
            return int(param[9:])



class Configuration(object):
    conf = {}
    machine_info_file = '/tmp/machine_info.json'
    service_info_file = '/tmp/service_info.json'
    def lldp_info_file(self, interface):
        return '/tmp/lldp_info.%s.json' % interface
    def Save(self):
        try:
            with open('config.json','w') as file:
                json.dump(self.conf, file)
        except:
            print('Error on Save conf')

    def Load(self):
        try:
            with open('config.json') as file:
                json.load(self.conf, file)
        except:
            print('Error on Load conf')

    def __init__(self):
        super(type(self), self).__init__()

CONF = Configuration()
