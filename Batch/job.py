import os
from pyats.easypy import run
import getpass

def main():

    ip_js1 = os.environ.get('JS1')
    user1 = os.environ.get('USER1')
    pass1 = os.environ.get('PASS1')

    ip_js2 = os.environ.get('JS2')
    port2 = os.environ.get('PORT')
    user2 = user1
    pass2 = os.environ.get('PASS2')

    user3 = os.environ.get('USER2')
    pass3 = os.environ.get('PASS3')

    test_path = os.path.dirname(os.path.abspath(__file__))
    testscript = os.path.join(test_path, 'get_commands.py')

    run(testscript=testscript, ip_js1=ip_js1, user1 = user1,
        pass1 = pass1, ip_js2=ip_js2, port2=port2,
        user2=user2, pass2=pass2, user3=user3, pass3=pass3)
