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
            output1 = uut.execute('show platform')
            parsed = platform_parse(output1)
            pprint.pprint(parsed)

        if not steps.result:
            self.failed(goto=['next_tc'])

def platform_parse(out):
    platform_dict = {}

    # Chassis type: ASR1006
    p1 = re.compile(r'^[Cc]hassis +type: +(?P<chassis>\w+)$')

    # Slot      Type                State                 Insert time (ago)
    # --------- ------------------- --------------------- -----------------
    # 0         ASR1000-SIP40       ok                    00:33:53
    #  0/0      SPA-1XCHSTM1/OC3    ok                    2d00h
    p2 = re.compile(r'^(?P<slot>\w+)(\/(?P<subslot>\d+))? +(?P<name>\S+) +'
                    '(?P<state>\w+(\, \w+)?) +(?P<insert_time>[\w\.\:]+)$')


    for line in out.splitlines():
        line = line.strip()

        m = p1.match(line)
        if m:
            if 'main' not in platform_dict:
                platform_dict['main'] = {}
                platform_dict['main']['chassis'] = m.groupdict()['chassis']
                continue

        m = p2.match(line)
        if m:
            slot = m.groupdict()['slot']
            subslot = m.groupdict()['subslot']
            name = m.groupdict()['name']
            state = m.groupdict()['state']
            insert_time = m.groupdict()['insert_time']
            if not name:
                continue

            #fan
            if re.search(r'F',slot):
                state = name + ' ' + state
                name = None
            # subslot
            if subslot:
                slot = slot + '/' + subslot

            if 'slot' not in platform_dict:
                platform_dict['slot'] = {}
            if slot not in platform_dict['slot']:
                platform_dict['slot'][slot] = {}
                platform_dict['slot'][slot]['name'] = name
                platform_dict['slot'][slot]['state'] = state
                platform_dict['slot'][slot]['insert_time'] = insert_time
                continue

    return platform_dict
