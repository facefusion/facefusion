#!/usr/bin/env python3

import os
import subprocess

os.environ['PIP_BREAK_SYSTEM_PACKAGES'] = '1'
subprocess.call([ 'pip', 'install', 'inquirer', '-q' ])

from facefusion import installer

if __name__ == '__main__':
	installer.cli()
