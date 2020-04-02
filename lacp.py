"""Implementation LACP triggers"""

import logging
import secrets
import re
from pyats import aetest
from genie.harness.base import Trigger
from utils import apply_template
import pprint


log = logging.getLogger(__name__)

class TriggerLacp(Trigger):

    @aetest.setup
    def cfg_lacp_setup(self, testbed, steps, message, BE_ID_uut,
                        interfaces_uut, BE_ID_uut2, interfaces_uut2,
                        templates_dir, template_config, remove_sysid):
        log.info("Test case steps:\n{msg}".format(msg=message))

        try:
            xr1 = testbed.devices['uut']
        except KeyError:
            step.failed('Could not find XR device node "uut1" in the testbed')
            self.failed(goto=['next_tc'])

        try:
            xr2 = testbed.devices['uut2']
        except KeyError:
            step.failed('Could not find XR device node "uut2" in the testbed')
            self.failed(goto=['next_tc'])

        with steps.start("Remove LACP Sys-ID on XR1") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr1, templates_dir, remove_sysid,
                                                commit_label=self.commit_label)

            lacp_sysid_1 = xr1.parse('show lacp system-id')

        with steps.start("Remove LACP Sys-ID on XR2") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr2, templates_dir, remove_sysid,
                                                commit_label=self.commit_label)

            lacp_sysid_2 = xr2.parse('show lacp system-id')

        with steps.start("Determining LACP higher priority device") as step:

            if (lacp_sysid_1['system_priority'] == lacp_sysid_2['system_priority']):
                log.info('XR1 and XR2 has same system_priority, continue comparing MAC')
                if (lacp_sysid_1['system_id_mac'] < lacp_sysid_2['system_id_mac']):
                    log.info('XR1 has higher LACP priority')
                    best_xr = xr1
                    best_id = BE_ID_uut
                else:
                    log.info('XR2 has higher LACP priority')
                    best_xr = xr2
                    best_id = BE_ID_uut2

            elif (lacp_sysid_1['system_priority'] < lacp_sysid_2['system_priority']):
                log.info('XR1 has higher LACP priority')
                best_xr = xr1
                best_id = BE_ID_uut

            else :
                log.info('XR2 has higher LACP priority')
                best_xr = xr2
                best_id = BE_ID_uut2

        with steps.start("Apply test configuration on XR1") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr1, templates_dir, template_config,
                                              bundle_id=BE_ID_uut,
                                              interface_name_1=interfaces_uut[0],
                                              interface_name_2=interfaces_uut[1],
                                              commit_label=self.commit_label)

        with steps.start("Apply test configuration on XR2") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr2, templates_dir, template_config,
                                                      bundle_id=BE_ID_uut2,
                                                      interface_name_1=interfaces_uut2[0],
                                                      interface_name_2=interfaces_uut2[1],
                                                      commit_label=self.commit_label)

        with steps.start("Determining LACP Port priorities on winning device") as step:

            bundle_parsed = best_xr.parse('show bundle')
            bundle_if = 'Bundle-Ether{id}'.format(id=best_id)

            for port in bundle_parsed['interfaces'][bundle_if]['port'].keys() :
                port_id = bundle_parsed['interfaces'][bundle_if]['port'][port]['port_id']
                log.info('On {BE} member {intf} priority is {pri}'.format(BE = bundle_if, intf = port, pri=port_id))

    @aetest.test
    def cfg_lacp_mismatch(self, testbed, steps, BE_wrong_ID_uut2, mismatch_cfg, interfaces_uut2, templates_dir, BE_ID_uut, sys_pri_cfg,
                            new_sys_pri, new_intf_pri, interfaces_uut):
        with steps.start("Apply mismatch configuration on XR2") as step:
            try:
                xr1 = testbed.devices['uut']
            except KeyError:
                step.failed('Could not find XR device node "uut1" in the testbed')
                self.failed(goto=['next_tc'])

            try:
                xr2 = testbed.devices['uut2']
            except KeyError:
                step.failed('Could not find XR device node "uut2" in the testbed')
                self.failed(goto=['next_tc'])

            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr2, templates_dir, mismatch_cfg,
                                                      bundle_id=BE_wrong_ID_uut2,
                                                      interface_name_1=interfaces_uut2[1],
                                                      commit_label=self.commit_label)

        with steps.start("Verify Bundle Negotiation") as step:

            bundle_if = 'Bundle-Ether{id}'.format(id=BE_ID_uut)
            bundle_parsed = xr1.parse('show bundle')

            for port in bundle_parsed['interfaces'][bundle_if]['port'].keys() :
                link_state = bundle_parsed['interfaces'][bundle_if]['port'][port]['link_state']
                if (link_state != 'Link is Active'):
                    log.info('On {BE} member {intf} state is {state}'.format(BE = bundle_if, intf = port, state=link_state))

        with steps.start("Change System ID and port Priority") as step:

            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr1, templates_dir, sys_pri_cfg,
                                                      system_priority=new_sys_pri,
                                                      interface_name_1=interfaces_uut[1],
                                                      interface_priority=new_intf_pri,
                                                      commit_label=self.commit_label)

        with steps.start("Verify Bundle Negotiation after changes") as step:

            bundle_if = 'Bundle-Ether{id}'.format(id=BE_ID_uut)
            bundle_parsed = xr1.parse('show bundle')

            for port in bundle_parsed['interfaces'][bundle_if]['port'].keys() :
                link_state = bundle_parsed['interfaces'][bundle_if]['port'][port]['link_state']
                if (link_state != 'Link is Active'):
                    log.info('On {BE} member {intf} state is {state}'.format(BE = bundle_if, intf = port, state=link_state))

        with steps.start("Fixing configuration on XR2") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr2, templates_dir, mismatch_cfg,
                                                      bundle_id=BE_wrong_ID_uut2,
                                                      interface_name_1=interfaces_uut2[0],
                                                      commit_label=self.commit_label)

        with steps.start("Final Verification for Bundle Negotiation") as step:

            bundle_if = 'Bundle-Ether{id}'.format(id=BE_ID_uut)
            bundle_parsed = xr1.parse('show bundle')

            for port in bundle_parsed['interfaces'][bundle_if]['port'].keys() :
                link_state = bundle_parsed['interfaces'][bundle_if]['port'][port]['link_state']
                if (link_state == 'Link is Active'):
                    log.info('On {BE} member {intf} state is {state}'.format(BE = bundle_if, intf = port, state=link_state))
                else:
                    break
                    step.failed('On {BE} member {intf} state is {state}'.format(BE = bundle_if, intf = port, state=link_state))

    @aetest.cleanup
    def cfg_lacp_cleanup(self, testbed, steps, BE_ID_uut, BE_ID_uut2, BE_wrong_ID_uut2, interfaces_uut,
                        interfaces_uut2, templates_dir, lacp_cleanup):

        try:
            xr1 = testbed.devices['uut']
        except KeyError:
            step.failed('Could not find XR device node "uut1" in the testbed')
            self.failed(goto=['next_tc'])

        try:
            xr2 = testbed.devices['uut2']
        except KeyError:
            step.failed('Could not find XR device node "uut2" in the testbed')
            self.failed(goto=['next_tc'])

        with steps.start("Remove config on XR1") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr1, templates_dir, lacp_cleanup,
                                                bundle_id=BE_ID_uut,
                                                interface_name_1=interfaces_uut[0],
                                                interface_name_2=interfaces_uut[1],
                                                commit_label=self.commit_label)

        with steps.start("Remove config on XR2") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, message = apply_template(xr2, templates_dir, lacp_cleanup,
                                                bundle_id=BE_ID_uut2,
                                                interface_name_1=interfaces_uut2[0],
                                                interface_name_2=interfaces_uut2[1],
                                                commit_label=self.commit_label)

            success, message = apply_template(xr2, templates_dir, lacp_cleanup,
                                                bundle_id=BE_wrong_ID_uut2,
                                                interface_name_1=interfaces_uut2[0],
                                                interface_name_2=interfaces_uut2[1],
                                                commit_label=self.commit_label)
