"""Implementation Cli Based Reload on IOS-XR triggers"""
import logging
import re
import secrets
from pyats import aetest
from genie.harness.base import Trigger
from genie.utils.timeout import Timeout
from unicon.core.errors import SubCommandFailure
from utils import apply_template
from parsers import cpu_parser
from parsers import memory_parser
from parsers import exception_parser
from parsers import files_parser
import math
import pprint

log = logging.getLogger(__name__)


class TriggerCliReload(Trigger):

    @aetest.test
    def cli_reload(self, uut, testbed, steps, message, templates_dir, template_config,
                    helper_interface, reload_max_time, check_interval):
        log.info("Test case steps:\n{msg}".format(msg=message))

        with steps.start("Verify Redundancy Operation", continue_=True) as step:

            cmd = 'show redundancy summary'
            try:
                redundancy_parsed = uut.parse(cmd)
            except Exception as e:
                step.failed("Failed to parse '{}':\n{}".format(cmd, e))

            for node in redundancy_parsed['node'].keys():
                try:
                    check = redundancy_parsed['node'][node]['node_detail']
                except Exception as e:
                    step.failed("Failed to verify redundancy detail with:\n{}".format(e))

                if (check == 'Node Ready, NSR:Ready'):
                    step.passed('RSPs are operating with full redundancy')
                    break
                else:
                    step.failed('RSPs are not operating with full redundancy')

        with steps.start("Collect Initial State for Router") as step:

            with step.start('Collect Line Card state', continue_=True) as child:

                cmd = 'show platform'
                try:
                    lc_state_initial = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

            with step.start('Collect Interface State', continue_=True) as child:

                cmd = 'show interfaces description'
                try:
                    if_state_initial = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

            with step.start('Collect ISIS adjacency table', continue_=True) as child:

                cmd = 'show isis neighbors'
                try:
                    isis_state_initial = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

            with step.start('Collect CPU State', continue_=True) as child:
                cmd = 'sh processes cpu | e 0%'
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                cpu_initial = cpu_parser(out)

            with step.start('Collect Memory State', continue_=True) as child:
                cmd = 'sh watchdog memory-state'
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                mem_initial = memory_parser(out)

            with step.start('Find exception files directory path') as child:
                cmd = 'sh exception'
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                exception_parsed = exception_parser(out)
                path = exception_parsed['path']
                log.info('Path for searching exceptions and tracebacks is {}'.format(path))

            with step.start('Find crash/traces files') as child:
                cmd = 'dir {}'.format(path)
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                files_initial = files_parser(out)

#        with steps.start("Connect to UUT console") as step:
#            # Determine which RP is accessible via console
#            platform = uut.parse('show platform')
#
#            # Loop through RPs to find the active RP by taking the last character from the slot value, e.g. "0/RP0"
#            for k, v in platform['slot']['rp'].items():
#                if v['redundancy_state'] == "Active":
#                    active_rp_id = k[-1]
#                    log.info("RP{id} is active.".format(id=active_rp_id))
#
#            try:
#                uut.connect(via='console-rp{}'.format(active_rp_id), alias='con')
#            except SubCommandFailure as e:
#                step.failed(str(e))
#
#        with steps.start("Reload UUT") as step:
#            uut.con.transmit("reload location all noprompt\r")
#            uut.con.receive(r'\[Done\]', timeout=30)
#            uut.con.disconnect()
#            self.uut_reloaded = True
#            uut.disconnect()

        with steps.start("Shutdown BE1") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(uut, templates_dir, template_config,
                                                interface_id = helper_interface,
                                                commit_label=self.commit_label)

            if success:
                self.uut_reloaded = True
            else:
                step.failed('Apply template failed with:\n{}'.format(message))

        with steps.start("Verify UUT as ISIS neighbor up in peer") as step:
            try:
                peer = testbed.devices['xr2']
            except KeyError:
                step.failed('Could not find device "xr2" in the testbed')

            timeout_up = Timeout(reload_max_time, check_interval)
            reload_time = check_interval
            while timeout_up.iterate():
                neighbor_up = peer.api.verify_isis_neighbor_in_state(
                    interfaces=[helper_interface],
                    max_time=check_interval,
                    check_interval=check_interval)
                if neighbor_up:
                    break
                else:
                    reload_time = reload_time + check_interval
            log.info('Time taken for ISIS to came up was {} seconds'.format(reload_time))

        with steps.start("Collect Final State for Router") as step:

            # Reconnect to UUT device after reloading
            # uut.connect()

            with step.start('Verify ISIS adjacency table', continue_=True) as child:

                isis_parsed = uut.parse('show isis')
                process_id = ''
                for instances in isis_parsed['instance'].keys():
                    process_id = isis_parsed['instance'][instances]['process_id']
                    vrf = isis_parsed['instance'][instances]['vrf']
                    if (vrf == 'default'):
                        break

                cmd = 'show isis neighbors'
                try:
                    isis_state_final = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

                initial_isis_neigh = isis_state_final['isis'][process_id]['vrf']['default']['interfaces']
                final_isis_neigh = isis_state_final['isis'][process_id]['vrf']['default']['interfaces']

                for intf in initial_isis_neigh.keys():
                    neigh1 = initial_isis_neigh[intf]['neighbors'].keys()
                    neigh2 = final_isis_neigh[intf]['neighbors'].keys()

                    if (neigh1 != neigh2):
                        child.failed('ISIS neighbors on interface {} not found on actual state'.format(
                                    intf))
                        break
                    else:
                        log.info('ISIS neighbors on interface {} found on actual state'.format(
                                    intf))
                    continue

            with step.start('Verify interface state', continue_=True) as child:

                cmd = 'show interfaces description'
                try:
                    if_state_final = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

                for intf in if_state_final['interfaces'].keys():
                    state_initial = if_state_initial['interfaces'][intf]['status']
                    state_final = if_state_final['interfaces'][intf]['status']
                    if (state_initial != state_final):
                        child.failed('Interface {} is on different state than initial: {}'.format(
                                    intf, state_final))
                        break
                    else:
                        log.info('Interface {} is on same state than initial: {}'.format(
                                    intf, state_final))
                    continue

            with step.start('Verify Line Card state', continue_=True) as child:

                cmd = 'show platform'
                try:
                    lc_state_final = uut.parse(cmd)
                except Exception as e:
                    child.failed("Failed to parse '{}':\n{}".format(cmd, e))

                for slots in lc_state_initial['slot'].keys():
                    for locations in lc_state_initial['slot'][slots].keys():
                        state_initial = lc_state_initial['slot'][slots][locations]['state']
                        state_final = lc_state_initial['slot'][slots][locations]['state']
                    if (state_initial != state_final):
                        child.failed('Module at {} is on different state than initial: {}'.format(
                                    locations, state_final))
                        break
                    else:
                        log.info('Module at {} is on same state than initial: {}'.format(
                                    locations, state_final))
                    continue

            with step.start('Verify CPU State', continue_=True) as child:
                cmd = 'sh processes cpu | e 0%'
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                cpu_final = cpu_parser(out)

                cpu_one_final = int(cpu_final['cpu_one'])
                cpu_one_inital = int(cpu_initial['cpu_one'])

                if (math.fabs(cpu_one_final - cpu_one_inital) > 10):
                    child.failed('The difference on CPU from initial state is higher than 10%')
                else:
                    child.passed('Difference on CPU from initial state is normal')

            with step.start('Verify Memory State', continue_=True) as child:
                cmd = 'sh watchdog memory-state'
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                mem_final = memory_parser(out)

                free_mem_initial = float(mem_initial['free_mem'])
                free_mem_final = float(mem_final['free_mem'])
                dif = math.fabs(free_mem_initial - free_mem_final)

                if (dif * 100 / free_mem_initial > 10):
                    child.failed('The difference on Free Memory from initial state is higher than 10%')
                else:
                    child.passed('Difference on Free Memory from initial state is normal')

            with step.start('Verify crash/traces files') as child:
                cmd = 'dir {}'.format(path)
                try:
                    out = uut.execute(cmd)
                except Exception as e:
                    child.failed("Failed to execute '{}':\n{}".format(cmd, e))

                files_final = files_parser(out)

                if files_final:
                    for file_final in files_final:
                        for file_initial in files_initial:
                            if (file_final == file_initial):
                                log.info('File {} was present before reload'.format(file_final))
                                break
                            else:
                                continue
                        else:
                            child.failed('File {} was not present before reload'.format(file_final))
                else:
                    child.passed('No crash/traceback files present in directory: {}'.format(path))
