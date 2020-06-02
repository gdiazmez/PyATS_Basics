from pyats.topology import Testbed, Device
from genie.testbed import load
import getpass
import csv
import logging
from pyats import aetest
import os

log = logging.getLogger(__name__)

class Testcase(aetest.Testcase):
    @aetest.setup
    def create_testbed(self, steps):
        testbed = Testbed('PyATS Testbed')
        ip_js1 = self.parameters['ip_js1']
        user1 = self.parameters['user1']
        pass1 = self.parameters['pass1']
        ip_js2 = self.parameters['ip_js2']
        user2 = self.parameters['user2']
        pass2 = self.parameters['pass2']
        port2 = self.parameters['port2']
        user3 = self.parameters['user3']
        pass3 = self.parameters['pass3']

        testbed.credentials['default'] = dict(username=user3, password=pass3)

        with steps.start('Creating jump_host1') as step:
            try:
                jump_host_1 = Device('jump_host_1',
                                    connections = {
                                        'mgmt': {
                                            'protocol': 'ssh',
                                            'ip': ip_js1,
                                            'port': '22'
                                        },
                                    },
                                )
            except:
                step.failed()

            jump_host_1.os = 'linux'
            jump_host_1.credentials['default'] = dict(username=user1, password=pass1)
            jump_host_1.testbed = testbed
            log.info('Entering Jump host with IP {} and user "{}"'.format(ip_js1,user1))

        with steps.start('Creating jump_host2') as step:
            try:
                jump_host_2 = Device('jump_host_2',
                                    connections = {
                                        'mgmt': {
                                            'protocol': 'ssh',
                                            'ip': ip_js2,
                                            'port': port2,
                                            'proxy': 'jump_host_1'
                                        },
                                    },
                                )
            except:
                step.failed()

            jump_host_2.os = 'linux'
            jump_host_2.credentials['default'] = dict(username=user2, password=pass2)
            jump_host_2.testbed = testbed
            log.info('Entering Jump host with IP {} and user "{}"'.format(ip_js2,user2))

        with steps.start('Populating testbed from CSV File') as step:
            File = os.environ.get('PRIVATE_PATH') + 'vtr_devices.csv'
            try:
                with open(File, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        dev = Device((row)[0],
                                    connections = {
                                                'cli': {
                                                    'protocol': 'ssh',
                                                    'ip': (row)[1],
                                                    'proxy': [{'device': 'jump_host_1',
                                                                'command': 'ssh {}@{} -p {}'.format(user2, ip_js2, port2)},
                                                                {'device': 'jump_host_2'}]
                                                    },
                                                })
                        dev.os = 'iosxr'
                        dev.testbed = testbed
                        log.info('Adding device {} to testbed'.format((row)[0]))
                        del dev
            except IOError:
                log.info('Input Devices CSV not accesible')
                step.failed()

        self.tb = load(testbed)
    @aetest.test
    def collect_task(self, steps):

        with steps.start('Connecting devices except jumpservers') as step:
            Success = True
            Failed = []
            for device in self.tb.devices.keys():
                if (self.tb.devices[device].os == 'linux'):
                    continue
                else:
                    uut = self.tb.devices[device]
                    try:
                        log.info('Connecting to device {}'.format(uut.name))
                        uut.connect(init_exec_commands=[], init_config_commands=[],connection_timeout=10)
                    except Exception:
                        log.info('Failed connection to: {}'.format(uut.name))
                        Success = False
                        Failed.append(uut.name)
                        continue
                    with open('commands.csv', 'r') as g:
                        reader2 = csv.reader(g)
                        for row2 in reader2:
                            uut.execute((row2)[0])
            if Success:
                step.passed('All devices were collected')
            else:
                step.failed('These devices could not be collected: {}'.format(Failed))

if __name__ == '__main__': # pragma: no cover
    #ip_jump_server = input ("Enter your jumpserver IP Address: ")
    aetest.main()
