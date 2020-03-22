"""Implementation fan triggers"""

import logging
from pyats import aetest
from genie.harness.base import Trigger
import re
import pprint

log = logging.getLogger(__name__)


class TriggerFan(Trigger):

    @aetest.test
    def collect_hardware_information(self, uut, steps, message, testbed):
        log.info("Test case steps:\n{msg}".format(msg=message))

        with steps.start("Collect and parse show environment for fan", continue_=True) as step:
            output = uut.execute('show environment all | inc FC')
            fan_parsed = fan_parser(output)
            pprint.pprint(fan_parsed)

        if not steps.result:
            self.failed(goto=['next_tc'])

def fan_parser(output):
    # Init vars
    fan_dict = {}

    #  Temp: FC PWM1    P2                Fan Speed 60%     21 Celsius
    p1 = re.compile(r'^ Temp: +(?P<Sensor>\w+\s\w+) +'
                    r'(?P<Location>\w+) +'
                    r'Fan Speed *(?P<Fan_Speed>\w+)% +'
                    r'(?P<Temperature>\w+) Celsius')

    for line in output.splitlines():
        if not line:
            continue

        #  Temp: FC PWM1    P2                Fan Speed 60%     21 Celsius
        m = p1.match(line)
        if m:
            if 'Sensor' not in fan_dict:
                fan_dict['Sensor'] = {}
            Sensor = str(m.groupdict()['Sensor'])
            if Sensor not in fan_dict['Sensor']:
                fan_dict['Sensor'][Sensor] = {}
                fan_dict['Sensor'][Sensor]['Location'] = \
                    str(m.group('Location')).strip()
                fan_dict['Sensor'][Sensor]['Fan_Speed'] = \
                    str(m.group('Fan_Speed')).strip()
                fan_dict['Sensor'][Sensor]['Temperature'] = \
                    str(m.group('Temperature')).strip()
                continue

    return fan_dict
