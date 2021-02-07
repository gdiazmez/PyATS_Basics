import pprint
from genie.testbed import load
tb = load('/Users/gdiazmez/pyats/Testbed/2K.yaml')


dev = tb.devices['xr9kv1']
dev.connect()

output = dev.parse('show isis neighbors')

print ('\n *** ISIS ipv4 neighbor structure *** \n')

for x in output['isis']['Core']['vrf'].keys():
	print ('\n *** For VRF', x , '*** \n')
	for intf in output['isis']['Core']['vrf'][x]['interfaces'].keys():
		print ('neighbors for interface: {}'.format(intf))
		pprint.pprint(output['isis']['Core']['vrf'][x]['interfaces'][intf])

dev.disconnect()
