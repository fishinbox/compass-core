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

import os, sys
import socket
import struct
import subprocess
import re
import fcntl
import time
import signal
import json
from multiprocessing import Process

# agent libs
from common import *

try:
    import ctypes
    class ifreq(ctypes.Structure):
        _fields_ = [("ifr_ifrn", ctypes.c_char * 16),
                    ("ifr_flags", ctypes.c_short)]
except (ImportError, NameError) as e:
    print "Meh"
#Taken from the C Header Files
ETH_P_ALL = 0x0003
IFF_PROMISC = 0x100
SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914


def get_networklist(osnameonly=None):
    filtered = ['lo', 'dummy', 'tunl', 'tun', 'tap', 'ip_vti', 'vir', 'br', 'br-', 'ovs', 'qvo', 'qvb', 'qbr']
    interface_list = os.listdir("/sys/class/net")
    for interface in interface_list[:]:
        iftype = interface.rstrip('1234567890')
        if iftype in filtered or iftype[:3] in filtered:
            interface_list.remove(interface)
    return interface_list
    # python case switch http://stackoverflow.com/questions/60208/replacements-for-switch-statement-in-python

# Enable promiscuous mode from http://stackoverflow.com/a/6072625
def promiscuous_mode(interface, sock, enable=False):
    ifr = ifreq()
    ifr.ifr_ifrn = interface
    fcntl.ioctl(sock.fileno(), SIOCGIFFLAGS, ifr)
    if enable:
        ifr.ifr_flags |= IFF_PROMISC
    else:
        ifr.ifr_flags &= ~IFF_PROMISC
    fcntl.ioctl(sock.fileno(), SIOCSIFFLAGS, ifr)
def saveLldpInfo(interface, interfaces, switch_name="", vlan_id="", port="", management_address=""):
    switch = {
        "switch_name": switch_name,
        "vlan_id": vlan_id,
        "port": port,
        "management_address": management_address,
    }
    if port not in interfaces:
        filename = CONF.lldp_info_file(interface)
        print filename
        with open(filename, 'w') as file:
            json.dump(switch, file)



def evaluate(interface, interfaces):
    rawSocket = socket.socket(17, socket.SOCK_RAW, socket.htons(0x0003))
    rawSocket.bind((interface, ETH_P_ALL))
    promiscuous_mode(interface, rawSocket, True)
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGALRM, exit_handler)
    saveLldpInfo(interface, interfaces)
    while True:
        try:
            packet = rawSocket.recvfrom(65565)
            packet = packet[0]
            lldpPayload = packet[14:]
            ethernetHeaderTotal = packet[0:14]
            ethernetHeaderUnpacked = struct.unpack("!6s6s2s", ethernetHeaderTotal)
            ethernetHeaderProtocol = ethernetHeaderUnpacked[2]
            if ethernetHeaderProtocol != '\x88\xCC':
                continue

            VLAN_ID, Switch_Name, Port_Description, Ethernet_Port_Id, Management_Address, System_Description = parse_lldp_packet_frames(lldpPayload)
            saveLldpInfo(
                interface,
                interfaces,
                Switch_Name,
                VLAN_ID,
                Port_Description,
                Management_Address,
            )
            # Note(ZZR): check port to avoid local lldp communications
        except socket.error as msg:
            print "Error occured with interface %s:\n%s" % (interface, msg)

    promiscuous_mode(interface, rawSocket, False)

def parse_lldp_packet_frames(lldpPayload):
    Switch_Name = None
    VLAN_ID = None
    Ethernet_Port_Id = None
    Port_Description = None
    Management_Address = None
    System_Description = None
    while lldpPayload:
        #print lldpPayload
        #print 'lldpPayload'
        #print ":".join("{:02x}".format(ord(c)) for c in lldpPayload)

    #[0] at the end of the unpack is because of the tuple returnvalue
    #!H unpacks as an unsigned short, which has a size of two bytes, which is what we need because the TLV "header" is 9 and 7 bits long (2bytes)
    #The right bitshift by 9 bits shifts away the length part of the TLV, leaving us with the TLV Type
    #The bitmask gives us the length of the real payload by masking the first 7 bits with a 0000000111111111 mask (0x01ff in hex)
    #lldpDU is the 3rd-Nth byte of the TLV Frame
    #lldpDU: we need to add +2 bytes because the address space changes when we cut off the header ( see http://standards.ieee.org/getieee802/download/802.1AB-2009.pdf page 24)
    #if tlvtype is 4 then datafield must start at 0 because of the payload structure for Port Descriptions (see IEEE PDF)
        tlv_header = struct.unpack("!H", lldpPayload[:2])[0]
        tlv_type = tlv_header >> 9
        tlv_len = (tlv_header & 0x01ff)
        lldpDU = lldpPayload[2:tlv_len + 2]
        if tlv_type == 127:
            tlv_oui = lldpDU[:3]
            tlv_subtype = lldpDU[3:4]
            tlv_datafield = lldpDU[4:tlv_len]
            if tlv_oui == "\x00\x80\xC2" and tlv_subtype == "\x01":
                VLAN_ID = struct.unpack("!H", tlv_datafield)[0]
            print 'Vendor specific TLV detected'
        elif tlv_type == 0:
            #print "TLV Type is ZERO, Breaking the while loop"
            # Note(ZZR): End of LLDP Packet
            break
        else:
            tlv_subtype = struct.unpack("!B", lldpDU[0:1]) if tlv_type is 2 else ""
            startbyte = 1 if tlv_type is 2 else 0
            tlv_datafield = lldpDU[startbyte:tlv_len]

        #Chassis ID TLV (Type = 1)
        #Port ID TLV (Type = 2)
        #Time To Live TLV (Type = 3)
        #End of LLDPDU TLV (Type = 0)

        # Optional TLVs
        #Port Description TLV (Type = 4)
        #System Name TLV (Type = 5)
        #System Description TLV (Type = 6)
        #System Capabilities TLV (Type = 7)
        #Management Address TLV (Type = 8)

        if tlv_type == 4:
            Port_Description = tlv_datafield
        elif tlv_type == 2:
            Ethernet_Port_Id = tlv_datafield
        elif tlv_type == 5:
            Switch_Name = tlv_datafield
        elif tlv_type == 1:
            #print 'Chassis ID'
            chassis_id_subtype = struct.unpack('!B', lldpDU[0])[0]
            #print ":".join("{:02x}".format(ord(c)) for c in lldpDU[1:])
        elif tlv_type == 3:
            ttl = struct.unpack('!H', lldpDU)[0]
        elif tlv_type == 6:
            #print ":".join("{:02x}".format(ord(c)) for c in lldpDU)
            System_Description = tlv_datafield
        elif tlv_type == 7:
            #print 'System Capability'
            #print ":".join("{:02x}".format(ord(c)) for c in lldpDU)
            pass
        elif tlv_type == 8:
            address_string_length = struct.unpack('!B',lldpDU[0])[0]
            address_subtype = struct.unpack('!B',lldpDU[1])[0]
            lldpDU = lldpDU[1:]
            #print 'MGMTIP'
            #print ":".join("{:02x}".format(ord(c)) for c in lldpDU[1:address_string_length])
            AF_TYPEs = {
                1: socket.AF_INET,
                2: socket.AF_INET6
            }
            Management_Address = socket.inet_ntop(AF_TYPEs[address_subtype], lldpDU[1:address_string_length])
            lldpDU = lldpDU[address_string_length:]
            interface_subtype = struct.unpack('!B',lldpDU[0])[0]
            interface_number = struct.unpack('!L',lldpDU[1:5])[0]
            OID_string_length = struct.unpack('!B',lldpDU[5])[0]

        else:
            #print 'TLV_TYPE is %d' % tlv_type
            #print ":".join("{:02x}".format(ord(c)) for c in lldpDU)
            #print 'Data is %s' % tlv_datafield
            # TODO: optional 3rd-party LLDP fileds
            pass

        lldpPayload = lldpPayload[2 + tlv_len:]


    return VLAN_ID, Switch_Name, Port_Description, Ethernet_Port_Id, Management_Address, System_Description



def exit_handler(signum, frame):
    """ Exit signal handler """

    rawSocket = frame.f_locals['rawSocket']
    interface = frame.f_locals['interface']

    promiscuous_mode(interface, rawSocket, False)
    print("Abort, %s exit promiscuous mode." % interface)

    sys.exit(1)

def exit_handler_aix(signum, frame):
    print "Aborting AIX"
    sys.exit(0)


class LldpInfoApp():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/tmp/lldpinfo_stdout'
        self.stderr_path = '/tmp/lldpinfo_stderr'
        self.pidfile_path =  '/tmp/lldpinfo_daemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        networkname_list = get_networklist()
        processes = [Process(target=evaluate, args=(interface, networkname_list)) for interface in networkname_list]
        for x in processes:
            x.start()

lldpinfo = LldpInfoApp()
lldpinfo_runner = runner.DaemonRunner(lldpinfo)
lldpinfo_runner.do_action()


