"""Implementation SCP triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re
import pprint
from unicon.eal.dialogs import Dialog, Statement

log = logging.getLogger(__name__)


class TriggerScp(Trigger):

    @aetest.test
    def scp_testing(self,
                    uut,
                    steps,
                    message,
                    testbed,
                    remote_test_file_download,
                    remote_test_file_upload,
                    vrf,
                    local_test_file,
                    scp_server):

        log.info("Test case steps:\n{msg}".format(msg=message))

        with steps.start("Copy from SCP server to Disk0:", continue_=True) as step:

            try:
                uut.api.copy_to_device(remote_path=remote_test_file_download,
                                            local_path=local_test_file,
                                            server=scp_server,
                                            protocol='scp',
                                            quiet=False,
                                            vrf=vrf)

            except Exception as e:
                step.failed

            pass_dialog = Dialog(
            [
            Statement(
            pattern=r"Connecting*"
                    r"Pasword:*",
            action="sendline()",
            loop_continue=True,
            continue_timer=False,
            )
            ]
            )

            #uut.execute('scp gdiazmez@172.16.11.32:test/test.txt disk0:/test.txt vrf management', reply=pass_dialog)

        with steps.start("Copy test file to SCP Server", continue_=True) as step:

            try:
                uut.api.copy_from_device(remote_path=remote_test_file_upload,
                                            local_path=local_test_file,
                                            server=scp_server,
                                            protocol='scp',
                                            quiet=False,
                                            vrf=vrf)
            except Exception as e:
                step.failed

        if not steps.result:
            self.failed(goto=['next_tc'])
