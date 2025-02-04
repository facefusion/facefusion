#!/usr/bin/env python3

import os
<<<<<<< HEAD
import subprocess

os.environ['PIP_BREAK_SYSTEM_PACKAGES'] = '1'
subprocess.call([ 'pip', 'install', 'inquirer', '-q' ])
=======

os.environ['SYSTEM_VERSION_COMPAT'] = '0'
>>>>>>> origin/master

from facefusion import installer

if __name__ == '__main__':
	installer.cli()
