import os
import sys
    

# workaround for -n posted to https://github.com/pytest-dev/pytest/issues/289
# allowing for running test in parallel using pytest-xdist
def pytest_configure(config):
    os.environ['PYTHONPATH'] = ':'.join(sys.path)
