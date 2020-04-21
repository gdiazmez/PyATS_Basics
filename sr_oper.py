"""Implementation SR Operation triggers"""

import logging
import secrets
import re
from pyats import aetest
from genie.harness.base import Trigger
from utils import apply_template
import pprint


log = logging.getLogger(__name__)

class TriggerSrOper(Trigger):

    @aetest.test
    def sr_validation(self, steps, uut, message, Local_Prefix, Remote_Prefix):

        log.info("Test case steps:\n{msg}".format(msg=message))

        isis_parsed = uut.parse('show isis')
        process_id = ''
        for instances in isis_parsed['instance'].keys():
            process_id = isis_parsed['instance'][instances]['process_id']
            vrf = isis_parsed['instance'][instances]['vrf']
            if (vrf == 'default'):
                break

        hostname = uut.api.get_running_config_hostname()

        with steps.start("Verify SRLB on ISIS Process",continue_=True) as step:
            if 'srlb' not in isis_parsed['instance'][process_id]['vrf']['default'].keys():
                step.failed('Segment Routing Local Block not assigned in ISIS process: {msg}'.format(msg=process_id))
            else:
                log.info('Segment Routing Local Block assigned in ISIS process: {msg}'.format(msg=process_id))

        with steps.start("Verify SRGB on ISIS Process",continue_=True) as step:
            if 'srgb' not in isis_parsed['instance'][process_id]['vrf']['default'].keys():
                step.failed('Segment Routing Global Block not assigned in ISIS process: {msg}'.format(msg=process_id))
            else:
                log.info('Segment Routing Global Block assigned in ISIS process: {msg}'.format(msg=process_id))

        with steps.start("Verify SR info is advertised in ISIS",continue_=True) as step:
            db = uut.execute('show isis database {hostname} verbose'.format(hostname=hostname))
            db = db.splitlines()
            for line in db:
                if re.search('Prefix-SID', line.strip()):
                    log.info("There are Prefix-SID values in this local LSP")
                    break
            else:
                step.failed("There are not Prefix-SID values in this local LSP")

        with steps.start("Verify local node-sid in ISIS",continue_=True) as step:
            local_route = uut.execute('show isis route {prefix} detail'.format(prefix=Local_Prefix))
            local_route = local_route.splitlines()
            for line in local_route:
                if re.search(r'prefix-SID.*N:1', line.strip()):
                    log.info("This route represent a Node SID")
                    break
            else:
                step.failed("This route does not represent a Node SID")

        with steps.start("Verify remote node-sid in ISIS",continue_=True) as step:
            local_route = uut.execute('show isis route {prefix} detail'.format(prefix=Remote_Prefix))
            local_route = local_route.splitlines()
            for line in local_route:
                if re.search(r'prefix-SID.*N:1', line.strip()):
                    log.info("This route represent a Node SID")
                    break
            else:
                step.failed("This route does not represent a Node SID")
