import os
import sys
from typing import List

from facefusion.common_helper import is_linux, is_windows


def collect_nvidia_library_paths(site_packages_path : str, library_directory_name : str) -> List[str]:
	nvidia_directory_path = os.path.join(site_packages_path, 'nvidia')
	library_paths : List[str] = []

	if not os.path.exists(nvidia_directory_path):
		return library_paths

	for library_name in sorted(os.listdir(nvidia_directory_path)):
		library_path = os.path.join(nvidia_directory_path, library_name, library_directory_name)
		if os.path.exists(library_path):
			library_paths.append(library_path)
	return library_paths


def setup() -> None:
	conda_prefix = os.getenv('CONDA_PREFIX')
	conda_ready = os.getenv('CONDA_READY')

	if conda_prefix and not conda_ready:
		if is_linux():
			python_id = 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
			site_packages_path = os.path.join(conda_prefix, 'lib', python_id, 'site-packages')
			library_paths : List[str] =\
			[
				os.path.join(conda_prefix, 'lib'),
				os.path.join(site_packages_path, 'tensorrt_libs')
			]
			library_paths.extend(collect_nvidia_library_paths(site_packages_path, 'lib'))
			library_paths = list(filter(os.path.exists, library_paths))

			if library_paths:
				if os.getenv('LD_LIBRARY_PATH'):
					library_paths.append(os.getenv('LD_LIBRARY_PATH'))
				os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(library_paths)
				os.environ['CONDA_READY'] = '1'
				os.execv(sys.executable, [ sys.executable ] + sys.argv)

		if is_windows():
			site_packages_path = os.path.join(conda_prefix, 'Lib', 'site-packages')
			library_paths =\
			[
				os.path.join(conda_prefix, 'Lib'),
				os.path.join(site_packages_path, 'tensorrt_libs')
			]
			library_paths.extend(collect_nvidia_library_paths(site_packages_path, 'bin'))
			library_paths = list(filter(os.path.exists, library_paths))

			if library_paths:
				if os.getenv('PATH'):
					library_paths.append(os.getenv('PATH'))
				os.environ['PATH'] = os.pathsep.join(library_paths)
				os.environ['CONDA_READY'] = '1'
