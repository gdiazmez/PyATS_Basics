from pyats.topology import Testbed, Device
from genie.testbed import load
import getpass
import sys
import csv

testbed = Testbed('exampleTestbed')
#ip_jump_server = input ("Enter your jumpserver IP Address: ")
#Port = input ("Enter your jumpserver TCP Port: ")
user = input("Enter your username and password for network devices: ")
password = getpass.getpass()
testbed.credentials['default'] = dict(username=user, password=password)

jump_host_1 = Device('jump_host_1',
                    connections = {
                        'mgmt': {
                            'protocol': 'ssh',
                            'ip': '64.100.29.32',
                            'port': '22'
                        },
                    },
                )
jump_host_1.os = 'linux'
jump_host_1.credentials['default'] = dict(username='gdiazmez', password='F_may2020')
jump_host_1.testbed = testbed

jump_host_2 = Device('jump_host_2',
                    connections = {
                        'mgmt': {
                            'protocol': 'ssh',
                            'ip': '200.83.2.14',
                            'port': '4500',
                            'proxy': 'jump_host_1'
                        },
                    },
                )
jump_host_2.os = 'linux'
jump_host_2.credentials['default'] = dict(username='gdiazmez', password='F_dic2019')
jump_host_2.testbed = testbed

with open('vtr_devices.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        dev = Device((row)[0],
                    connections = {
                                'cli': {
                                    'protocol': 'ssh',
                                    'ip': (row)[1],
                                    'proxy': [{'device': 'jump_host_1',
                                                'command': 'ssh gdiazmez@200.83.2.14 -p 4500'},
                                                {'device': 'jump_host_2'}]
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
            uut.connect(init_exec_commands=[], init_config_commands=[],connection_timeout=30)
        except Exception:
            print('fallo al conectar a {}'.format(uut.name))
            continue
        with open('commands.csv', 'r') as g:
            reader2 = csv.reader(g)
            for row2 in reader2:
                uut.execute((row2)[0])
