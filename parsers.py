import re

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

def controller_parser(output):

    # Init vars
    controller_dict = {}

    #   T1 0/10/0 is up.
    p1 = re.compile(r'^(?P<if_name>[\S\s]* [\S\s]*) is (?P<state>[\S\s]*)\.$')

    #   Applique type is NCS4200-48T1E1-CE
    p2 = re.compile(r'^Applique type is +(?P<module_name>[\S\s]*)')

    #   DSX1 BERT pattern     : 2^23
    p3 = re.compile(r'^DSX1 BERT pattern +: +(?P<bert_pattern>[\S\s]*)')

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        #   T1 0/10/0 is up.
        m = p1.match(line)
        if m:
            if 'if_name' not in controller_dict:
                controller_dict['if_name'] = {}
            if_name = str(m.groupdict()['if_name'])
            if if_name not in controller_dict['if_name']:
                controller_dict['if_name'][if_name] = {}
                controller_dict['if_name'][if_name]['status'] = \
                    str(m.group('state')).strip()
                continue

        #   Applique type is NCS4200-48T1E1-CE
        m = p2.match(line)
        if m:
            controller_dict['if_name'][if_name]['module_name'] = \
                str(m.group('module_name')).strip()
            continue

        #   DSX1 BERT pattern     : 2^23
        m = p3.match(line)
        if m:
            controller_dict['if_name'][if_name]['bert_pattern'] = \
                str(m.group('bert_pattern')).strip()
            continue

    return controller_dict

def route_detail_parser(output):

    # Init vars
    out_dict = {}

    # Routing entry for 172.16.12.2/32
    p1 = re.compile(r'^Routing entry for (?P<prefix>[\S\s]*)$')

    # Route Priority: RIB_PRIORITY_NON_RECURSIVE_LOW (8) SVD Type RIB_SVD_TYPE_LOCAL
    p2 = re.compile(r'^Route Priority: (?P<route_priority>[\S\s]*) \(.*$')

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # Routing entry for 172.16.12.2/32
        m = p1.match(line)
        if m:
            if 'prefix' not in out_dict:
                out_dict['prefix'] = {}
            prefix = str(m.groupdict()['prefix'])
            if prefix not in out_dict['prefix']:
                out_dict['prefix'][prefix] = {}
                continue

        # Route Priority: RIB_PRIORITY_NON_RECURSIVE_LOW (8) SVD Type RIB_SVD_TYPE_LOCAL
        m = p2.match(line)
        if m:
            out_dict['prefix'][prefix]['route_priority'] = \
                str(m.group('route_priority')).strip()
            continue

    return out_dict

def parse_hostname(output):

    # Init vars
    hostname = ''
    p = re.compile(r'hostname (?P<hostname>[\S\s]*)')

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        m = p.match(line)
        if m:
            hostname = str(m.groupdict()['hostname'])
            break

    return hostname
