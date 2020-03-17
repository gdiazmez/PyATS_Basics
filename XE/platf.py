"""Implementation platform triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re
import pprint

log = logging.getLogger(__name__)


class TriggerPlatf(Trigger):

    @aetest.test
    def collect_environment_variables(self, uut, steps, message, testbed):
        log.info("Test case steps:\n{msg}".format(msg=message))


        with steps.start("Collect show environment", continue_=True) as step:
            output = uut.parse('show platform')

        if not steps.result:
            self.failed(goto=['next_tc'])
