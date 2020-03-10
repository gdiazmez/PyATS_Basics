#!/usr/bin/env python
###################################################################
# connection_example.py : A test script example which includes:
#     common_seup section - device connection, configuration
#     Tescase section with testcase setup and teardown (cleanup)
#     common_cleanup section - device cleanup
###################################################################

# To get a logger for the script
import logging

# Needed for aetest script
from pyats import aetest
from pyats.log.utils import banner

# Genie Imports
from genie.testbed import load

# Get your logger for your script
log = logging.getLogger()

###################################################################
###                  COMMON SETUP SECTION                       ###
###################################################################

class common_setup(aetest.CommonSetup):
    """ Common Setup section """

    # CommonSetup have subsection.
    # You can have 1 to as many subsection as wanted

    # First subsection
    @aetest.subsection
    def connect_to_devices(self, testbed, p_connect = True):

        # convert from pyATS testbed to genie testbed
        # this step will be deprecated soon (and not required)
        testbed = self.parent.parameters['testbed'] = load(testbed)

        # connect to all devices in testbed in parallel
        if p_connect:
            testbed.connect()
        else:
            for device in testbed:
                try:
                    device.connect()
                except Exception:
                    logger.exception('failed to connect to device %s'
                                     % device.name)

        log.debug(self.parameters)

###################################################################
###                     TESTCASES SECTION                       ###
###################################################################

# Testcase name : tc_one
class test_platform(aetest.Testcase):
    """ This is user Testcases section """

    @aetest.setup
    def setup(self, testbed):
        # Get device output
        testbed = self.parent.parameters['testbed'] = load(testbed)
        for device in testbed:
            if device.connected:
                output = device.parse('show platform')
                print ('hola')
                self.platform_info = device.parse('show version')

            else:
                self.failed('Cannot learn %s platform information: '
                            'did not establish connectivity to device'
                            % device.name)

#####################################################################
####                       COMMON CLEANUP SECTION                 ###
#####################################################################

# This is how to create a CommonCleanup
# You can have 0 , or 1 CommonCleanup.
# CommonCleanup can be named whatever you want :)
class common_cleanup(aetest.CommonCleanup):
    """ Common Cleanup for Sample Test """

    # CommonCleanup follow exactly the same rule as CommonSetup regarding
    # subsection
    # You can have 1 to as many subsection as wanted

    @aetest.subsection
    def disconnect(self, testbed):
        """ Common Cleanup Subsection """
        for device in testbed:
            # Connecting to the devices using the default connection
            device.disconnect()
