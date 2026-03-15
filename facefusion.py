#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import core, conda

if __name__ == '__main__':
	conda.setup()
	core.cli()
