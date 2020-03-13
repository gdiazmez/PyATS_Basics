import os

from genie.harness.main import gRun

def main():
    test_path = os.path.dirname(os.path.abspath(__file__))

    gRun(trigger_datafile='trigger_datafile_test.yaml',
         subsection_datafile='subsection_datafile.yaml')
