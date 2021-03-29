"""Implementation ISIS triggers"""

import logging
import secrets
import re
from pyats import aetest
from genie.harness.base import Trigger
from utils import apply_template
from parsers import route_detail_parser
import pprint


log = logging.getLogger(__name__)

class TriggerIsisBcdl(Trigger):

    @aetest.setup
    def cfg_isis_setup(self, testbed, steps, message, Test_Prefix1, Test_Prefix2,
                        ACL_Name_High, ACL_Name_Medium, templates_dir, isis_cfg):
        log.info("Test case steps:\n{msg}".format(msg=message))

        try:
            xr1 = testbed.devices['R1']
        except KeyError:
            step.failed('Could not find XR device node "R1" in the testbed')
            self.failed(goto=['next_tc'])

        with steps.start("Discovering ISIS process ID") as step:

            isis_parsed = xr1.parse('show isis')
            process_id = ''
            for instances in isis_parsed['instance'].keys():
                process_id = isis_parsed['instance'][instances]['process_id']
                vrf = isis_parsed['instance'][instances]['vrf']
                if (vrf == 'default'):
                    break

            log.info("ISIS process name for VRF default is {process}".format(process=process_id))

        with steps.start("Configure ISIS SPF Priority") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, conf_message = apply_template(xr1, templates_dir, isis_cfg,
                                                process_id = process_id,
                                                ACL_Name_High = ACL_Name_High,
                                                ACL_Name_Medium = ACL_Name_Medium,
                                                Prefix_High = Test_Prefix1,
                                                Prefix_Medium = Test_Prefix2,
                                                commit_label=self.commit_label)

            if not success:
                log.info("Configuration failed with: {msg}".format(msg=conf_message))
                self.failed(goto=['next_tc'])

    @aetest.test
    def test_routes(self, steps, uut, Test_Prefix1, Test_Prefix2, Test_Prefix3):

        with steps.start("Testing High Priority Route",continue_=True) as step:
            out1 = uut.execute('show route {route} detail'.format(route=Test_Prefix1))
            out1_parsed = route_detail_parser(out1)

            route_priority = out1_parsed['prefix'][Test_Prefix1]['route_priority']
            if re.search(r'HIGH', route_priority):
                log.info("Prefix {prefix} has route priority {priority}".format(prefix=Test_Prefix1,
                                                                                priority=route_priority))
            else:
                step.failed("Prefix {prefix} has incorrect route priority {priority}".format(prefix=Test_Prefix1,
                                                                                priority=route_priority))

        with steps.start("Testing Medium Priority Route",continue_=True) as step:
            out2 = uut.execute('show route {route} detail'.format(route=Test_Prefix2))
            out2_parsed = route_detail_parser(out2)

            route_priority = out2_parsed['prefix'][Test_Prefix2]['route_priority']
            if re.search(r'MEDIUM', route_priority):
                log.info("Prefix {prefix} has route priority {priority}".format(prefix=Test_Prefix2,
                                                                                priority=route_priority))
            else:
                step.failed("Prefix {prefix} has incorrect route priority {priority}".format(prefix=Test_Prefix2,
                                                                                priority=route_priority))

        with steps.start("Testing Low Priority Route",continue_=True) as step:
            out3 = uut.execute('show route {route} detail'.format(route=Test_Prefix3))
            out3_parsed = route_detail_parser(out3)

            route_priority = out3_parsed['prefix'][Test_Prefix3]['route_priority']
            if re.search(r'LOW', route_priority):
                log.info("Prefix {prefix} has route priority {priority}".format(prefix=Test_Prefix3,
                                                                                priority=route_priority))
            else:
                step.failed("Prefix {prefix} has incorrect route priority {priority}".format(prefix=Test_Prefix3,
                                                                                priority=route_priority))

    @aetest.cleanup
    def uncfg_isis_setup(self, testbed, steps, message,
                        ACL_Name_High, ACL_Name_Medium, templates_dir, isis_uncfg):
        log.info("Test case steps:\n{msg}".format(msg=message))

        try:
            xr1 = testbed.devices['R1']
        except KeyError:
            step.failed('Could not find XR device node "R1" in the testbed')
            self.failed(goto=['next_tc'])

        with steps.start("Discovering ISIS process ID") as step:

            isis_parsed = xr1.parse('show isis')
            process_id = ''
            for instances in isis_parsed['instance'].keys():
                process_id = isis_parsed['instance'][instances]['process_id']
                vrf = isis_parsed['instance'][instances]['vrf']
                if (vrf == 'default'):
                    break

            log.info("ISIS process name for VRF default is {process}".format(process=process_id))

        with steps.start("Cleanup for ISIS SPF Priority") as step:
            self.commit_label = 'pyats_{secret}'.format(secret=secrets.token_urlsafe(10))

            success, conf_message = apply_template(xr1, templates_dir, isis_uncfg,
                                                process_id = process_id,
                                                ACL_Name_High = ACL_Name_High,
                                                ACL_Name_Medium = ACL_Name_Medium,
                                                commit_label=self.commit_label)

            if not success:
                log.info("Configuration failed with: {msg}".format(msg=conf_message))
                self.failed(goto=['next_tc'])
