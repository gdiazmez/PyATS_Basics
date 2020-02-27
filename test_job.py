''' Description of file '''

# Python
import logging
import os

# pyATS
from pyats import aetest

# Genie
from genie.harness.base import Trigger
# from genie.utils.timeout import Timeout

# Unicon
from unicon.core.errors import SubCommandFailure

log = logging.getLogger(__name__)

def main():
    # Find the location of the script in relation to the job file
    test_path = os.path.dirname(os.path.abspath(__file__))



class TriggerSimple(Trigger):
    ''' Trigger Simple for Training '''

    @aetest.setup
    def check_interface(self, uut, steps):
        output = uut.parse('show interfaces')
        if output:
            self.passed('interface found')
