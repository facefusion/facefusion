#!/usr/bin/env python3

import subprocess
import sys

if __name__ == '__main__':
	if 'venv' in sys.executable or 'conda' in sys.executable:
		from facefusion import core

		core.cli()
	else:
		try:
			subprocess.run([ 'venv/bin/python', 'run.py' ])
		except KeyboardInterrupt:
			sys.exit()
