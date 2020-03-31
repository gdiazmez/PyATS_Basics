import jinja2
from genie.testbed import load
tb = load('../Testbed/XR_test.yaml')

dev = tb.devices['ASR9906']
dev.connect()

env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath='../config_files'))
template = env.get_template('config_ospf.j2')

configuration = template.render(process_id='1',
									rid='1.1.1.1',
									area_id='0',
									loopback_if='loopback0',
									interface_name='TenGigE0/0/0/0',
									interface_name_2='Te0/1/0/0',
									interface_name_3='Bundle-Eth13',
									bfd_min='250',
									bfd_multi='4')

dev.configure(configuration)

dev.disconnect()
