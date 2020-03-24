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
    def cfg_lacp_setup(self, testbed, steps, message):
        log.info("Test case steps:\n{msg}".format(msg=message))

        try:
            xr1 = testbed.devices['uut']
        except KeyError:
            step.failed('Could not find XR device node "uut1" in the testbed')

        try:
            xr2 = testbed.devices['uut2']
        except KeyError:
            step.failed('Could not find XR device node "uut2" in the testbed')

        

        bundle1 = xr1.parse('show bundle')
        bundle2 = xr2.parse('show bundle')

        pprint.pprint(bundle1)
        pprint.pprint(bundle2)
