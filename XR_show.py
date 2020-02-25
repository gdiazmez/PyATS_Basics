import pprint
from genie.testbed import load
tb = load('XR_test.yaml')

dev = tb.devices['ASR9906']
dev.connect()

output = dev.parse('show ospf vrf all-inclusive neighbor detail')

print ('\n *** OSPF ipv4 neighbor structure *** \n')

for x in output['vrf'].keys():
	print ('\n *** For VRF', x , '*** \n')
	pprint.pprint(output['vrf'][x]['address_family']['ipv4']['instance'])

dev.disconnect()