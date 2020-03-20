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
                    remote_file,
                    local_file,
                    vrf,
                    scp_server,
                    scp_username,
                    scp_password):

        log.info("Test case steps:\n{msg}".format(msg=message))

        scp_dialog = Dialog(
            [
                Statement(
                    pattern=r"Connecting.*"
                    r"Password:.*",
                    action=lambda spawn, password: spawn.sendline(password),
                    args={'password': scp_password},
                    loop_continue=True,
                    continue_timer=False,
                )
            ]
        )

        with steps.start("Copy from SCP server to Disk0:", continue_=True) as step:

            output = uut.execute('scp {user}@{ip}:{remote_file} {local_file} vrf {vrf}'.format(user=scp_username,
                                                                                                ip=scp_server,
                                                                                                remote_file=remote_file,
                                                                                                local_file=local_file,
                                                                                                vrf=vrf),
                                    reply=scp_dialog)

            if re.search(r'Transferred', output):
                log.info("Test file transferred from {user}@{ip}:{remote_file} to {local_file}".format(local_file=local_file,
                                                                                                        user=scp_username,
                                                                                                        ip=scp_server,
                                                                                                        remote_file=remote_file))
            else:
                step.failed('Test file was not transferred into device')

        with steps.start("Copy test file to SCP Server", continue_=True) as step:

            output = uut.execute('scp {local_file} {user}@{ip}:{remote_file} vrf {vrf}'.format(user=scp_username,
                                                                                                ip=scp_server,
                                                                                                remote_file=remote_file,
                                                                                                local_file=local_file,
                                                                                                vrf=vrf),
                                    reply=scp_dialog)

            if re.search(r'Transferred', output):
                log.info("Test file transferred from {local_file} to {user}@{ip}:{remote_file}".format(local_file=local_file,
                                                                                                        user=scp_username,
                                                                                                        ip=scp_server,
                                                                                                        remote_file=remote_file))
            else:
                step.failed('Test file was not transferred from device')


        if not steps.result:
            self.failed(goto=['next_tc'])
