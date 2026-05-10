import os
import sys
from typing import List

from facefusion.common_helper import is_linux, is_macos, is_windows


def setup_for_conda() -> None:
	conda_prefix = os.getenv('CONDA_PREFIX')
	conda_ready = os.getenv('CONDA_READY')

	if conda_prefix and not conda_ready:
		if is_linux():
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
				os.environ['CONDA_READY'] = '1'
				os.execv(sys.executable, [ sys.executable ] + sys.argv)

		if is_windows():
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
				os.environ['CONDA_READY'] = '1'


def setup_for_system() -> None:
	if is_macos():
		homebrew_path = os.environ.get('HOMEBREW_PREFIX')
		system_ready = os.getenv('SYSTEM_READY')

		if homebrew_path and not system_ready:
			library_paths =\
			[
				os.path.join(homebrew_path, 'lib'),
				os.path.join(homebrew_path, 'opt', 'openssl@3', 'lib')
			]
			library_paths = list(filter(os.path.isdir, library_paths))

			if library_paths:
				if os.getenv('DYLD_LIBRARY_PATH'):
					library_paths.append(os.getenv('DYLD_LIBRARY_PATH'))
				os.environ['DYLD_LIBRARY_PATH'] = os.pathsep.join(library_paths)
				os.environ['SYSTEM_READY'] = '1'
				os.execv(sys.executable, [ sys.executable ] + sys.argv)

	if is_windows():
		vcpkg_path = os.environ.get('VCPKG_INSTALLATION_ROOT')
		library_paths =\
		[
			os.path.join(vcpkg_path, 'installed', 'x64-windows', 'bin')
		]
		library_paths = list(filter(os.path.isdir, library_paths))

		if library_paths:
			if os.getenv('PATH'):
				library_paths.append(os.getenv('PATH'))
			os.environ['PATH'] = os.pathsep.join(library_paths)

