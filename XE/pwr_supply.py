"""Implementation platform triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re
import pprint

log = logging.getLogger(__name__)


class TriggerPwrSupply(Trigger):

    @aetest.test
    def collect_power_supply_information(self, uut, steps, message, testbed):
        log.info("Test case steps:\n{msg}".format(msg=message))


        with steps.start("Collect and parse show environment", continue_=True) as step:
            output = uut.parse('show environment')
            #pprint.pprint(output)
            for modules in output['slot'].keys():
                if re.search(r'P.',modules):
                    #print('Found Power-Module at {mod}'.format(mod=modules))
                    for sensor in output['slot'][modules]['sensor'].keys():
                        state = output['slot'][modules]['sensor'][sensor]['state']
                        #print('State at {sensor} is {state}'.format(sensor=sensor,state=state))
                        if (state == 'Normal'):
                            log.info('State at {sensor} in module {mod} is {state}'.format(sensor=sensor,mod=modules,state=state))
                        else:
                            step.failed('State at {sensor} in module {mod} is {state}'.format(sensor=sensor,mod=modules,state=state))

        if not steps.result:
            self.failed(goto=['next_tc'])
