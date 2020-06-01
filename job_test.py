import sys
from pathlib import Path
# Needed for logic
from pyats.datastructures.logic import And, Not, Or
from genie.harness.main import gRun


def main():
    sys.path.append(str(Path(__file__).parent.parent.resolve()))

    gRun(mapping_datafile='mapping_datafile.yaml',
         trigger_datafile='trigger_datafile.yaml',
         trigger_groups=And('trigger','cli_reload'),
         subsection_datafile='subsection_datafile.yaml')
