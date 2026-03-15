#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import conda, core

if __name__ == '__main__':
	conda.setup()
	core.cli()
