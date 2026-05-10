#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import environment, core

if __name__ == '__main__':
	environment.setup_for_conda()
	environment.setup_for_system()
	core.cli()
