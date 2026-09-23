import os
import signal
import subprocess
import sys
from typing import List, NoReturn

from facefusion.common_helper import is_linux, is_windows


def setup() -> None:
	environment_ready = os.getenv('ENVIRONMENT_READY')

	if not environment_ready:
		if is_linux():
			setup_linux()

		if is_windows():
			setup_windows()


def setup_linux() -> NoReturn:
	conda_prefix = os.getenv('CONDA_PREFIX')

	os.environ['OMP_NUM_THREADS'] = '1'
	os.environ['MALLOC_ARENA_MAX'] = '4'
	os.environ['ENVIRONMENT_READY'] = '1'

	if conda_prefix:
		python_id = 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
		library_paths : List[str] =\
		[
			os.path.join(conda_prefix, 'lib'),
			os.path.join(conda_prefix, 'lib', python_id, 'site-packages', 'tensorrt_libs')
		]
		library_paths = list(filter(os.path.exists, library_paths))

		if library_paths:
			if os.getenv('LD_LIBRARY_PATH'):
				library_paths.append(os.getenv('LD_LIBRARY_PATH'))
			os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(library_paths)

	os.execv(sys.executable, [ sys.executable ] + sys.argv)


def setup_windows() -> NoReturn:
	conda_prefix = os.getenv('CONDA_PREFIX')

	os.environ['OMP_NUM_THREADS'] = '1'
	os.environ['ENVIRONMENT_READY'] = '1'

	if conda_prefix:
		library_paths =\
		[
			os.path.join(conda_prefix, 'Lib'),
			os.path.join(conda_prefix, 'Lib', 'site-packages', 'tensorrt_libs')
		]
		library_paths = list(filter(os.path.exists, library_paths))

		if library_paths:
			if os.getenv('PATH'):
				library_paths.append(os.getenv('PATH'))
			os.environ['PATH'] = os.pathsep.join(library_paths)

	signal.signal(signal.SIGINT, signal.SIG_IGN)
	process = subprocess.run([ sys.executable ] + sys.argv)
	sys.exit(process.returncode)
