#!/usr/bin/env python3

import sys
import subprocess

if __name__ == '__main__':
	if 'venv' in sys.executable or '--skip-venv' in sys.argv:
		from facefusion import core

		core.cli()
	else:
		try:
			subprocess.run([ 'venv/bin/python', 'run.py' ])
		except:
			sys.exit()
