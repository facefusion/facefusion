#!/usr/bin/env python3

import os

os.environ['SYSTEM_VERSION_COMPAT'] = '0'

from weyfusion import installer

if __name__ == '__main__':
	installer.cli()
