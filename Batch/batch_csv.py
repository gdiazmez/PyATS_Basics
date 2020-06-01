from pyats.topology import Testbed, Device
from genie.testbed import load
import getpass
import sys
import csv

testbed = Testbed('exampleTestbed')
ip_jump_server = input ("Enter your jumpserver IP Address: ")
Port = input ("Enter your jumpserver TCP Port: ")
user = input("Enter your username and password for network devices: ")
password = getpass.getpass()
testbed.credentials['default'] = dict(username=user, password=password)

jump_server = Device('jump_host',
                  connections = {
                      'mgmt': {
                          'protocol': 'ssh',
                          'ip': ip_jump_server,
                          'port': Port
                      },
                  })
jump_server.os = 'linux'
jump_server.testbed = testbed

with open('devices.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        dev = Device((row)[0],
                    connections = {
                                'cli': {
                                    'protocol': 'ssh',
                                    'ip': (row)[1],
                                    'proxy': 'jump_host'
                                    },
                                })
        dev.os = 'iosxr'
        dev.testbed = testbed
        del dev


tb = load(testbed)
uut = tb.devices['xr9kv2']

uut.connect()
