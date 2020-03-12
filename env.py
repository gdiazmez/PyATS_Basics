"""Implementation NTP triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger

log = logging.getLogger(__name__)


class TriggerEnv(Trigger):

    @aetest.test
    def collect_environment_variables(self, uut, steps, message, testbed):
        log.info("Test case steps:\n{msg}".format(msg=message))

        #output = uut.execute('show inventory all')
        #self.output_parsed_all = inventory_parser(output)

        with steps.start("Collect show environment", continue_=True) as step:
            output1 = uut.execute('admin show environment')

        with steps.start("Collect show environment all", continue_=True) as step:
            output2 = uut.execute('admin show environment all')

        with steps.start("Collect show environment power", continue_=True) as step:
            output3 = uut.execute('admin show environment power')

        with steps.start("Collect show environment fan", continue_=True) as step:
            output4 = uut.execute('admin show environment fan')

        with steps.start("Collect show environment temperature", continue_=True) as step:
            output5 = uut.execute('admin show environment temperature')

        if not steps.result:
            self.failed(goto=['next_tc'])

def inventory_parser(output):
    out = output

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

    for line in out.splitlines():
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


def diag_parser(output):
    out = output

    # Init vars
    diag_dict = {}
    module_name = ""

    p0 = re.compile(r'\s*$')

    # Rack 0-Chassis IDPROM - Cisco 8812 12-slot Chassis
    # 0/0/CPU0-MB IDPROM - Cisco 8800 48x100GE QSFP28 Line Card
    # 0/RP0/CPU0-MB IDPROM - Cisco 8800 Route Processor
    # 0/FC0-MB IDPROM - Cisco 8812 Fabric Card
    # 0/PT0-DC 60 Power Tray IDPROM - Cisco 8800 Power Tray for 48V 60A DC Power Supply
    # 0/PT1-PM0-PSU4.4KW_DC_V3_DELTA IDPROM - 4.4kW DC Power Module
    # 0/FT0-FT IDPROM - Cisco 8812 Fan Tray
    p1 = re.compile(r'^(?P<module_name>\S+[\S\s]*)-(Chassis|MB|DC|PSU|FT)')

    # UDI Description            : Cisco 8800 Route Processor
    p2 = re.compile(r'^\s+UDI Description +: *(?P<descr>[\S\s]*)')

    # PID                        : 8800-LC-48H
    p3 = re.compile(r'^\s+PID +: *(?P<pid>[\S\s]*)')

    # Version Identifier         : V01
    p4 = re.compile(r'^\s+Version Identifier +: *(?P<vid>[\S\s]*)')

    # PCB Serial Number          : FOC2330PAZY
    p5 = re.compile(r'^\s+PCB Serial Number +: *(?P<sn>[\S\s]*)$')

    # Chassis Serial Number      : FOX2337P3YZ
    p6 = re.compile(r'^\s+Chassis Serial Number +: *(?P<sn>[\S\s]*)$')

    for line in out.splitlines():
        m = p0.match(line)
        if m:
            module_name = ""

        m = p1.match(line)
        if m:
            if 'module_name' not in diag_dict:
                diag_dict['module_name'] = {}
            module_name = str(m.groupdict()['module_name'])
            if module_name not in diag_dict['module_name']:
                diag_dict['module_name'][module_name] = {}
                continue

        m = p2.match(line)
        if m and module_name != "":
            diag_dict['module_name'][module_name]['descr'] = \
                str(m.group('descr')).strip()
            continue

        m = p3.match(line)
        if m and module_name != "":
            diag_dict['module_name'][module_name]['pid'] = \
                str(m.group('pid')).strip()
            continue

        m = p4.match(line)
        if m and module_name != "":
            diag_dict['module_name'][module_name]['vid'] = \
                str(m.group('vid')).strip()
            continue

        m = p5.match(line)
        if m and module_name != "" and 'Rack' not in module_name:
            diag_dict['module_name'][module_name]['sn'] = \
                str(m.group('sn')).strip()
            continue

        m = p6.match(line)
        if m and module_name != "" and 'Rack' in module_name:
            diag_dict['module_name'][module_name]['sn'] = \
                str(m.group('sn')).strip()
            continue

    return diag_dict
