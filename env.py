"""Implementation Environment triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re

log = logging.getLogger(__name__)


class TriggerEnv(Trigger):

    @aetest.test
    def collect_environment_variables(self, uut, steps, message):
        log.info("Test case steps:\n{msg}".format(msg=message))

        try:
            output = uut.execute('show inventory all')
        except SubCommandFailure as e:
            self.failed(goto=['next_tc'])

        output_parsed_inventory = inventory_parser(output)

        with steps.start('Collect show environment',continue_=True) as step:
            try:
                output1 = uut.execute('show environment')
            except SubCommandFailure as e:
                step.failed(str(e))

        with steps.start('Collect show environment all',continue_=True) as step:
            try:
                output2 = uut.execute('show environment all')
            except SubCommandFailure as e:
                step.failed(str(e))

        with steps.start('Collect show environment power',continue_=True) as step:
            try:
                output3 = uut.execute('show environment power')
            except SubCommandFailure as e:
                step.failed(str(e))
            output3 = output3.splitlines()
            for module in output_parsed_inventory['module_name'].keys():
                if re.search(r'PM', module):
                    log.info('Location in inventory for power-module is {module}'.format(module=module))
                    check_module = None
                    for line in output3:
                        if re.search(module, line.strip()):
                            log.info("There are power environment values for power-module at {mod}".format(mod=module))
                            check_module = True
                    if (not check_module):
                        step.failed('Environment values not found for fan-tray at: {module}'.format(module=module))

        with steps.start('Collect show environment fan',continue_=True) as step:
            try:
                output4 = uut.execute('show environment fan')
            except SubCommandFailure as e:
                step.failed(str(e))
            output4 = output4.splitlines()
            for module in output_parsed_inventory['module_name'].keys():
                if re.search(r'FT',module):
                    log.info('Location in inventory for fan-tray is {module}'.format(module=module))
                    check_module = None
                    for line in output4:
                        if re.search(module, line.strip()):
                            log.info("There are fan environment values for fan-tray at {mod}".format(mod=module))
                            check_module = True
                    if (not check_module):
                        step.failed('Environment values not found for fan-tray at: {module}'.format(module=module))

        with steps.start('Collect show environment temperature',continue_=True) as step:
            try:
                output5 = uut.execute('show environment temperature')
            except SubCommandFailure as e:
                step.failed(str(e))
            output5 = output5.splitlines()
            for module in output_parsed_inventory['module_name'].keys():
                if re.search(r'^0/',module):
                    log.info('Check Location in inventory at {module}'.format(module=module))
                    check_module = None
                    for line in output5:
                        if re.search(module, line.strip()):
                            log.info("There are temperature values for module at {mod}".format(mod=module))
                            check_module = True
                    if (not check_module):
                        step.failed('Temperature values not found for module at: {module}'.format(module=module))

        if not steps.result:
            self.failed(goto=['next_tc'])


def inventory_parser(output):
    # Init vars
    inventory_dict = {}

    # NAME: "module 0/RSP0/CPU0", DESCR: "ASR9K Route Switch Processor with 440G/slot Fabric and 6GB"
    # NAME: "Rack 0", DESCR: "Cisco XRv9K Centralized Virtual Router"
    # NAME: "Rack 0", DESCR: "Sherman 1RU Chassis with 24x400GE QSFP56-DD & 12x100G QSFP28"
    # NAME: "0/FT4", DESCR: "Sherman Fan Module Reverse Airflow / exhaust, BLUE"
    # NAME: "TenGigE0/0/0/0", DESCR: "Cisco SFP+ 10G SR Pluggable Optics Module"
    p1 = re.compile(r'^NAME: +\"(?P<module_name>[\S\s]*)\",'
                    r' +DESCR: +\"(?P<descr>[\S\s]*)\"$')

    # PID: A9K-MPA-20X1GE, VID: V02, SN: FOC1811N49J
    # PID: SFP-1G-NIC-X      , VID: N/A, SN: N/A
    # PID: N/A, VID: N/A, SN:
    p2 = re.compile(r'^PID: *(?P<pid>[\S\s]*),'
                    r' +VID: *(?P<vid>[\S\s]*),'
                    r' SN: *(?P<sn>[\S\s]*)$')

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # NAME: "0/FT4", DESCR: "Sherman Fan Module Reverse Airflow / exhaust, BLUE"
        # NAME: "TenGigE0/0/0/0", DESCR: "Cisco SFP+ 10G SR Pluggable Optics Module"
        m = p1.match(line)
        if m:
            if 'module_name' not in inventory_dict:
                inventory_dict['module_name'] = {}
            module_name = str(m.groupdict()['module_name'])
            if module_name not in inventory_dict['module_name']:
                inventory_dict['module_name'][module_name] = {}
                inventory_dict['module_name'][module_name]['descr'] = \
                    str(m.group('descr')).strip()
                continue

        # PID: A9K-MPA-20X1GE, VID: V02, SN: FOC1811N49J
        # PID: SFP-1G-NIC-X      , VID: N/A, SN: N/A
        m = p2.match(line)
        if m:
            inventory_dict['module_name'][module_name]['pid'] = \
                str(m.group('pid')).strip()
            inventory_dict['module_name'][module_name]['vid'] = \
                str(m.group('vid')).strip()
            inventory_dict['module_name'][module_name]['sn'] = \
                str(m.group('sn')).strip()
            continue
    return inventory_dict
