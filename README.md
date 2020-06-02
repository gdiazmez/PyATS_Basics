PyATS Automation Testing on XE and XR platforms

Usage:

pyats run job job_test.py -t 'Testbed Location'

Currently 6 local Tests
 1. Environment Test driven by env.py
 2. LACP Test driven by lacp.py
 3. SCP Copy Test driven by scp.py
 4. ISIS BCDL Test briven by isis_bcdl.py
 5. Segment Routing validation driven by sr_oper.py
 6. LACP Operational tests driven by lacp_oper.py


PyATS Automated Collection on "Batch" Folder

This PyATS job file triggers a definition on-the-fly of a new testbed from CSV devices using two jump-servers and environment variables.

Usage:

pyats run job job.by
