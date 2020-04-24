"""Implementation LACP Oper triggers"""
import logging
import secrets
from collections import deque
from operator import itemgetter
from pyats import aetest
from genie.harness.base import Trigger
from genie.utils.timeout import Timeout
from utils import apply_template
import re


log = logging.getLogger(__name__)


class TriggerLacpOper(Trigger):

    @aetest.setup
    def lacp_check(self, uut, steps, testbed, message, bundle_id_uut, bundle_id_peer):
        log.info("Test case steps:\n{msg}".format(msg=message))

        self.commit_stack_uut = deque()
        self.commit_stack_peer = deque()

        with steps.start("Determine master LACP device") as step:
            try:
                peer = testbed.devices['xr']
            except KeyError:
                step.failed('Could not find device "xr" in the testbed')

            lacp_uut = uut.parse('show lacp system-id')
            lacp_peer = peer.parse('show lacp system-id')

            uut_is_best = (lacp_uut['system_priority'] < lacp_peer['system_priority'] or
                           lacp_uut['system_priority'] == lacp_peer['system_priority'] and
                           lacp_uut['system_id_mac'] < lacp_peer['system_id_mac'])

            master = uut if uut_is_best else peer
            master_bundle_id = bundle_id_uut if uut_is_best else bundle_id_peer
            log.info('{device} is LACP master'.format(device='UUT' if uut_is_best else 'Peer'))

        with steps.start("Determine primary link on master device") as step:
            primary_if = 'null'
            best_priority = 65535
            best_num = 65535
            for member, port_id in bundle_iter(master, master_bundle_id, 'port_id'):
                log.info('On Bundle-Ether{bid} member {intf} priority is {pri}'.format(
                    bid=master_bundle_id, intf=member, pri=port_id))
                priority , port_num = port_id.split(',')
                priority = int(priority, 16)
                port_num = int(port_num, 16)
                if (priority < best_priority):
                    primary_if = member
                    best_priority = priority
                    best_num = port_num
                elif (priority == best_priority):
                    if (port_num < best_num):
                        best_num = port_num
                        primary_if = member
            log.info('Primary link on Bundle-Ether{bid} is {interface}'.format(
                        bid=master_bundle_id, interface=primary_if))

    @aetest.test
    def cfg_lacp_test(self, uut, steps, testbed, lacp_sys_pri, if_test_1,
                        templates_dir, config_sys, config_pri, if_priority,
                        bundle_id_uut, lacp_sys_mac, config_mac, config_pri_fast,
                        if_test_2, if_best_priority, config_no_fast):

        with steps.start("Configure LACP System Priority on UUT") as step:

            self.commit_label_initial = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))
            success, message = apply_template(uut, templates_dir, config_sys,
                                                system_priority=lacp_sys_pri,
                                                commit_label=self.commit_label_initial)

            try:
                peer = testbed.devices['xr']
            except KeyError:
                step.failed('Could not find device "xr" in the testbed')

            lacp_uut = uut.parse('show lacp system-id')
            lacp_peer = peer.parse('show lacp system-id')

            if success:
                uut_is_best = (lacp_uut['system_priority'] < lacp_peer['system_priority'] or
                                lacp_uut['system_priority'] == lacp_peer['system_priority'] and
                                lacp_uut['system_id_mac'] < lacp_peer['system_id_mac'])

                if uut_is_best:
                    step.passed('UUT configured and now is LACP master')
                else:
                    step.failed('UUT configured but peer device has lower priority than us')
            else:
                step.failed('Issue with configuration with this message: {msg}'.format(msg=message))

        with steps.start("Configure LACP Priority and period short on UUT") as step:

            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))
            success, message = apply_template(uut, templates_dir, config_pri_fast,
                                                interface_name_1=if_test_1,
                                                interface_priority=if_priority,
                                                commit_label=self.commit_label)

            if success:
                primary_if = ''
                best_priority = 65535
                best_num = 65535
                for member, port_id in bundle_iter(uut, bundle_id_uut, 'port_id'):
                    log.info('On Bundle-Ether{bid} member {intf} priority is {pri}'.format(
                        bid=bundle_id_uut, intf=member, pri=port_id))
                    priority , port_num = port_id.split(',')
                    priority = int(priority, 16)
                    port_num = int(port_num, 16)
                    if (priority < best_priority):
                        primary_if = member
                        best_priority = priority
                        best_num = port_num
                    elif (priority == best_priority):
                        if (port_num < best_num):
                            best_num = port_num
                            primary_if = member
                if (primary_if == if_test_1):
                    step.passed('UUT interface {if_test_1} has the highest priority on test Bundle'.format(
                                    if_test_1=if_test_1))
                else:
                    step.failed('UUT interface {if_test_1} has not the highest priority on test Bundle'.format(
                                    if_test_1=if_test_1))

            else:
                step.failed('Issue with configuration with this message: {msg}'.format(msg=message))

        with steps.start("Verify all links on Distributed state and Fast PDU") as step:

            lacp = uut.execute('show lacp bundle-eth{bid}'.format(bid=bundle_id_uut))

            #  Gi0/0/0/0        30s  ascdAF-- 0x07d0,0x0002 0x0001 0x0bb8,be-ef-be-ef-be-ef
            p1 = re.compile(r'^(?P<if_name>\S+[0-9]/[0-9]/[0-9]/[0-9]) +(?P<rate>\S+) +'
                            r'(?P<state>\S+) +\S+,\S+ +\S+ \S+,\S+$')

            # Partner          1s  ascdA--- 0x1000,0x0002 0x0001 0x8000,00-08-a4-4d-8f-37
            p1_1 = re.compile(r'^Partner +(?P<rate>\S+) +'
                            r'(?P<state>\S+) +\S+,\S+ +\S+ \S+,\S+$')

            #  Gi0/0/0/2             Current    Slow   Selected   Distrib   None    None
            p2 = re.compile(r'^(?P<if_name>\S+[0-9]/[0-9]/[0-9]/[0-9]) +\S+ +\S+ +\S+ +'
                            r'(?P<state>\S+) +\S+ +\S+$')

            for line in lacp.splitlines():
                line = line.strip()
                if not line:
                    continue

                #  Gi0/0/0/0        30s  ascdAF-- 0x07d0,0x0002 0x0001 0x0bb8,be-ef-be-ef-be-ef
                m = p1.match(line)
                if m:
                    if_name = str(m.group('if_name')).strip()
                    state = str(m.group('state')).strip()
                    if re.search(r'F',state):
                        log.info('Interface {intf} on Bundle-Eth{bid} is Requesting Fast PDU'.format(
                                    intf=if_name,bid=bundle_id_uut))
                        peer_validation = True
                    continue

                # Partner          1s  ascdA--- 0x1000,0x0002 0x0001 0x8000,00-08-a4-4d-8f-37
                m = p1_1.match(line)
                if m:
                    if peer_validation:
                        rate = str(m.group('rate')).strip()
                        if (rate == '1s'):
                            log.info('Peer Interface for {intf} on Bundle-Eth{bid} is transmiting at 1s'.format(
                                        intf=if_name,bid=bundle_id_uut))
                            peer_validation = False
                        else:
                            step.failed('Peer Interface for {intf} on Bundle-Eth{bid} is not transmiting at 1s'.format(
                                        intf=if_name,bid=bundle_id_uut))
                    continue

                #  Gi0/0/0/2             Current    Slow   Selected   Distrib   None    None
                m = p2.match(line)
                if m:
                    if_name = str(m.group('if_name')).strip()
                    state = str(m.group('state')).strip()
                    if (state == 'Distrib'):
                        log.info('Interface {intf} on Bundle-Eth{bid} is in Distributed state'.format(
                                    intf=if_name,bid=bundle_id_uut))
                    else:
                        step.failed('Interface {intf} on Bundle-Eth{bid} is not in Distributed state'.format(
                                    intf=if_name,bid=bundle_id_uut))

        with steps.start("Configure LACP System MAC on UUT") as step:

            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))
            success, message = apply_template(uut, templates_dir, config_mac,
                                                system_mac=lacp_sys_mac,
                                                commit_label=self.commit_label)

            if success:
                log.info('Verification of LACP Negotiation after MAC Change')
                lacp = uut.execute('show lacp bundle-eth{bid}'.format(bid=bundle_id_uut))

                #  Gi0/0/0/2             Current    Slow   Selected   Distrib   None    None
                p = re.compile(r'^(?P<if_name>\S+[0-9]/[0-9]/[0-9]/[0-9]) +\S+ +\S+ +\S+ +'
                                r'(?P<state>\S+) +\S+ +\S+$')

                for line in lacp.splitlines():
                    line = line.strip()
                    if not line:
                        continue

                    #  Gi0/0/0/2             Current    Slow   Selected   Distrib   None    None
                    m = p.match(line)
                    if m:
                        if_name = str(m.group('if_name')).strip()
                        state = str(m.group('state')).strip()
                        if (state == 'Distrib'):
                            log.info('Interface {intf} on Bundle-Eth{bid} is in Distributed state'.format(
                                        intf=if_name,bid=bundle_id_uut))
                        else:
                            step.failed('Interface {intf} on Bundle-Eth{bid} is not in Distributed state'.format(
                                        intf=if_name,bid=bundle_id_uut))
            else:
                step.failed('Issue with configuration with this message: {msg}'.format(msg=message))

        with steps.start("Configure LACP Priority on second interface") as step:

            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))
            success, message = apply_template(uut, templates_dir, config_pri,
                                                interface_name_1=if_test_2,
                                                interface_priority=if_best_priority,
                                                commit_label=self.commit_label)

            if success:
                primary_if = ''
                best_priority = 65535
                best_num = 65535
                for member, port_id in bundle_iter(uut, bundle_id_uut, 'port_id'):
                    log.info('On Bundle-Ether{bid} member {intf} priority is {pri}'.format(
                        bid=bundle_id_uut, intf=member, pri=port_id))
                    priority , port_num = port_id.split(',')
                    priority = int(priority, 16)
                    port_num = int(port_num, 16)
                    if (priority < best_priority):
                        primary_if = member
                        best_priority = priority
                        best_num = port_num
                    elif (priority == best_priority):
                        if (port_num < best_num):
                            best_num = port_num
                            primary_if = member
                if (primary_if == if_test_2):
                    step.passed('UUT interface {if_test_2} has the highest priority on test Bundle'.format(
                                    if_test_2=if_test_2))
                else:
                    step.failed('UUT interface {if_test_2} has not the highest priority on test Bundle'.format(
                                    if_test_2=if_test_2))

            else:
                step.failed('Issue with configuration with this message: {msg}'.format(msg=message))

        with steps.start("Remove LACP fast period on interface") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))
            success, message = apply_template(uut, templates_dir, config_no_fast,
                                                interface_name_1=if_test_1,
                                                commit_label=self.commit_label)

            if success:
                if_index = re.sub('GigabitEthernet','',if_test_1)

                lacp = uut.execute('show lacp bundle-eth{bid}'.format(bid=bundle_id_uut))

                #  Gi0/0/0/0        30s  ascdAF-- 0x07d0,0x0002 0x0001 0x0bb8,be-ef-be-ef-be-ef
                p1 = re.compile(r'^Gi(?P<index>[0-9]/[0-9]/[0-9]/[0-9]) +(?P<rate>\S+) +'
                                r'(?P<state>\S+) +\S+,\S+ +\S+ \S+,\S+$')

                # Partner          1s  ascdA--- 0x1000,0x0002 0x0001 0x8000,00-08-a4-4d-8f-37
                p1_1 = re.compile(r'^Partner +(?P<rate>\S+) +'
                                r'(?P<state>\S+) +\S+,\S+ +\S+ \S+,\S+$')

                for line in lacp.splitlines():
                    line = line.strip()
                    if not line:
                        continue

                    #  Gi0/0/0/0        30s  ascdAF-- 0x07d0,0x0002 0x0001 0x0bb8,be-ef-be-ef-be-ef
                    m = p1.match(line)
                    if m:
                        index = str(m.group('index')).strip()
                        if (index == if_index):
                            peer_validation = True
                        continue

                    # Partner          1s  ascdA--- 0x1000,0x0002 0x0001 0x8000,00-08-a4-4d-8f-37
                    m = p1_1.match(line)
                    if m:
                        if peer_validation:
                            rate = str(m.group('rate')).strip()
                            if (rate == '30s'):
                                log.info('Peer Interface for {intf} on Bundle-Eth{bid} is transmiting at 30s again'.format(
                                            intf=if_test_1,bid=bundle_id_uut))
                                peer_validation = False
                            else:
                                step.failed('Peer Interface for {intf} on Bundle-Eth{bid} is not back at 30s'.format(
                                            intf=if_test_1,bid=bundle_id_uut))
                        break

            else:
                step.failed('Issue with configuration with this message: {msg}'.format(msg=message))

    @aetest.cleanup
    def lacp_cleanup(self, uut, steps, testbed):
        with steps.start("Rollback") as step:
            uut.configure('load rollback changes to {label}'.format(label=self.commit_label_initial))


def bundle_iter(device, bundle_id, *fields):
    bundle_parsed = device.parse('show bundle')

    bundle = bundle_parsed['interfaces'].get('Bundle-Ether{id}'.format(id=bundle_id))
    if bundle is None:
        raise KeyError('Bundle-Ether{id} ia not present on {node}'.format(id=bundle_id, node=device.name))

    field_values = itemgetter('interface', *fields)
    return (field_values(port_info) for port_info in bundle.get('port', {}).values())
