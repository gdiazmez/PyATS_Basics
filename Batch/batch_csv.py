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

for device in tb.devices.keys():
    if (tb.devices[device].os == 'linux'):
        continue
    else:
        uut = tb.devices[device]
        try:
            uut.connect(init_exec_commands=[], init_config_commands=[],connection_timeout=5)
        except Exception:
            print('fallo al conectar a {}'.format(uut.name))
            continue
        with open('commands.csv', 'r') as g:
            reader2 = csv.reader(g)
            for row2 in reader2:
                uut.execute((row2)[0])
