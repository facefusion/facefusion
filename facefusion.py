#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import core, environment

if __name__ == '__main__':
	environment.setup_conda()
	environment.setup_platform()
	core.cli()
