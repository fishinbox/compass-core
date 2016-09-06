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

from lxml import etree
from subprocess import Popen,PIPE

from pprint import pprint


def describeSize(size):
    return '%s (%s)' % (calculateSize(size), calculateSize(size, True))


def calculateSize(size, isSi=False, level=0):
    unit = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    siUnit = ['B', 'KB', 'MB', 'GB', 'TB']
    if size >= 1000 and isSi:
        return calculateSize(size/1000, isSi, level+1)
    elif size >= 1024:
        return calculateSize(size/1024, isSi, level+1)
    else:
        # limit float presentation to 3 significant digits
        return "%.3g%s" % (size, siUnit[level] if isSi else unit[level])


def getDisk(inventory):
    def describeSize(size):
        return '%s (%s)' % (calculateSize(size), calculateSize(size, True))

    def calculateSize(size, isSi=False, level=0):
        unit = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
        siUnit = ['B', 'KB', 'MB', 'GB', 'TB']
        if size >= 1000 and isSi:
            return calculateSize(size/1000, isSi, level+1)
        elif size >= 1024:
            return calculateSize(size/1024, isSi, level+1)
        else:
            # limit float presentation to 3 significant digits
            return "%.3g%s" % (size, siUnit[level] if isSi else unit[level])

    disks = {}
    count = 0
    capacity = 0
    devices = []

    find_disks = etree.XPath(".//node[@class='disk']")
    for disk in find_disks(inventory):
        # has to be a hard-disk
        if disk.find('size') is not None:
            device = {}
            count += 1
            size = float(disk.find('size').text)
            capacity += size
            name = disk.find('logicalname').text
            device['size'] = describeSize(size)
            device['dev_name'] = name
            devices.append(device)

    disks['count'] = count
    disks['total_capacity'] = describeSize(capacity)
    disks['devices'] = devices
    return disks


def getMemory(inventory):
    memories = {}
    count = 0
    capacity = 0
    devices = []
    #find_memory = etree.XPath(".//node[@class='memory']/node[@class='memory']")
    find_memory = etree.XPath(".//node[@class='memory']")

    for memory in find_memory(inventory):
        if memory.find('size') is not None and memory.get('id').startswith('bank'):
            device = {}
            count += 1
            #pprint(etree.tostring(memory))
            pprint(memory.get('id'))
            size = float(memory.find('size').text)
            capacity += size
            device['size'] = describeSize(size)
            device['description'] = memory.find('description').text
            devices.append(device)
    memories['count'] = count
    memories['total_memory'] = describeSize(capacity)
    memories['devices'] = devices
    return memories


def getNetwork(inventory):
    networks = {}
    count = 0
    devices = []
    find_network = etree.XPath(".//node[@class='bridge']/node[@class='network']")

    for network in find_network(inventory):
        device = {}
        count += 1
        device['name'] = network.find('logicalname').text
        device['mac'] = network.find('serial').text
        device['is_link_up'] = network.find('configuration/setting[@id="link"]').get('value')
        device['duplex'] = network.find('configuration/setting[@id="duplex"]').get('value')
        device['speed'] = network.find('configuration/setting[@id="speed"]').get('value')
        device['switch'] = {}
        devices.append(device)
    networks['count'] = count
    networks['devices'] = devices
    return networks


def getProcessor(inventory):
    find_cpus = etree.XPath(".//node[@class='processor']")

    count = 0
    total_cores = 0
    total_enabledcores = 0
    total_threads = 0

    devices =[]

    for i in  find_cpus(inventory):
        if i.find('size') is not None and not bool(i.get('disabled', False)):
            #pprint(etree.tostring(i))
            pprint(etree.tostring(i.find('size')))
            count = count + 1
            product = i.find('product').text
            # print "width: " + i.find('width').text
            #pprint(etree.tostring(i.find('configuration')))
            cores = i.find('configuration/setting/[@id="cores"]').get('value')
            enabledcores = i.find('configuration/setting/[@id="enabledcores"]').get('value')
            try:
                threads = i.find('configuration/setting/[@id="threads"]').get('value')
            except:
                threads = 1

            total_cores = total_cores + int(cores)
            total_enabledcores = total_enabledcores + int(enabledcores)
            total_threads = total_threads + int(threads)
            devices.append({
                'product': product,
                'cores': cores,
                'enabledcores': enabledcores,
                'threads': threads
            })

    return {
        'count': count,
        'total_cores': total_cores,
        'total_enabledcores': total_enabledcores,
        'total_threads': total_threads,
        'devices': devices
    }


def getMachineInfo():
    lshw = Popen(['lshw', '-xml', '-numeric'], stdout=PIPE).communicate()[0]
    lshw = etree.XML(lshw)
    return {
        'processor': getProcessor(lshw),
        'memory': getMemory(lshw),
        'disk': getDisk(lshw),
        'network': getNetwork(lshw)
    }

