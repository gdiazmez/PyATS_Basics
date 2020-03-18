"""Implementation platform triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re
import pprint

log = logging.getLogger(__name__)


class TriggerPlatf(Trigger):

    @aetest.test
    def collect_hardware_information(self, uut, steps, message, testbed):
        log.info("Test case steps:\n{msg}".format(msg=message))


        with steps.start("Collect and parse show platform", continue_=True) as step:
            output = uut.parse('show platform')
            pprint.pprint(output)

        if not steps.result:
            self.failed(goto=['next_tc'])
