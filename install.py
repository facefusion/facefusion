#!/usr/bin/env python3

import os
import shutil
import subprocess

os.environ['SYSTEM_VERSION_COMPAT'] = '0'
os.environ['PIP_BREAK_SYSTEM_PACKAGES'] = '1'
subprocess.call([ shutil.which('pip'), 'install', 'inquirer', '-q' ])

from facefusion import installer

if __name__ == '__main__':
	installer.cli()
