#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from testingss import core

if __name__ == '__main__':
	core.cli()
