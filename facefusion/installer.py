import os
import shutil
import signal
import subprocess
import sys
from argparse import ArgumentParser, HelpFormatter
from functools import partial
from types import FrameType

from facefusion import metadata
from facefusion.common_helper import is_linux, is_windows

LOCALS =\
{
	'install_dependency': 'install the {dependency} package',
	'force_reinstall': 'force reinstall of packages',
	'skip_conda': 'skip the conda environment check',
	'conda_not_activated': 'conda is not activated'
}
ONNXRUNTIME_SET =\
{
	'default': ('onnxruntime', '1.23.2')
}
if is_windows() or is_linux():
	ONNXRUNTIME_SET['cuda'] = ('onnxruntime-gpu', '1.23.2')
	ONNXRUNTIME_SET['openvino'] = ('onnxruntime-openvino', '1.23.0')
if is_windows():
	ONNXRUNTIME_SET['directml'] = ('onnxruntime-directml', '1.23.0')
if is_linux():
	ONNXRUNTIME_SET['migraphx'] = ('onnxruntime-migraphx', '1.23.0')
	ONNXRUNTIME_SET['rocm'] = ('onnxruntime_rocm', '1.22.1', '7.0.2') #type:ignore[assignment]


def cli() -> None:
	signal.signal(signal.SIGINT, signal_exit)
	program = ArgumentParser(formatter_class = partial(HelpFormatter, max_help_position = 50))
	program.add_argument('--onnxruntime', help = LOCALS.get('install_dependency').format(dependency = 'onnxruntime'), choices = ONNXRUNTIME_SET.keys(), required = True)
	program.add_argument('--force-reinstall', help = LOCALS.get('force_reinstall'), action = 'store_true')
	program.add_argument('--skip-conda', help = LOCALS.get('skip_conda'), action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def signal_exit(signum : int, frame : FrameType) -> None:
	sys.exit(0)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()
	has_conda = 'CONDA_PREFIX' in os.environ
	commands = [ shutil.which('pip'), 'install' ]

	if args.force_reinstall:
		commands.append('--force-reinstall')

	if not args.skip_conda and not has_conda:
		sys.stdout.write(LOCALS.get('conda_not_activated') + os.linesep)
		sys.exit(1)

	with open('requirements.txt') as file:

		for line in file.readlines():
			__line__ = line.strip()
			if not __line__.startswith('onnxruntime'):
				commands.append(__line__)

	if args.onnxruntime == 'rocm':
		onnxruntime_name, onnxruntime_version, rocm_version = ONNXRUNTIME_SET.get(args.onnxruntime) #type:ignore[misc]
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)

		if python_id in [ 'cp310', 'cp312' ]:
			wheel_name = onnxruntime_name + '-' + onnxruntime_version + '-' + python_id + '-' + python_id + '-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl'
			wheel_url = 'https://repo.radeon.com/rocm/manylinux/rocm-rel-' + rocm_version + '/' + wheel_name
			commands.append(wheel_url)
	else:
		onnxruntime_name, onnxruntime_version = ONNXRUNTIME_SET.get(args.onnxruntime)
		commands.append(onnxruntime_name + '==' + onnxruntime_version)

	subprocess.call(commands)

	if args.onnxruntime == 'cuda' and has_conda:
		library_paths = []

		if is_linux():
			if os.getenv('LD_LIBRARY_PATH'):
				library_paths = os.getenv('LD_LIBRARY_PATH').split(os.pathsep)

			python_id = 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
			library_paths.extend(
			[
				os.path.join(os.getenv('CONDA_PREFIX'), 'lib'),
				os.path.join(os.getenv('CONDA_PREFIX'), 'lib', python_id, 'site-packages', 'tensorrt_libs')
			])
			library_paths = list(dict.fromkeys([ library_path for library_path in library_paths if os.path.exists(library_path) ]))

			subprocess.call([ shutil.which('conda'), 'env', 'config', 'vars', 'set', 'LD_LIBRARY_PATH=' + os.pathsep.join(library_paths) ])

		if is_windows():
			if os.getenv('PATH'):
				library_paths = os.getenv('PATH').split(os.pathsep)

			library_paths.extend(
			[
				os.path.join(os.getenv('CONDA_PREFIX'), 'Lib'),
				os.path.join(os.getenv('CONDA_PREFIX'), 'Lib', 'site-packages', 'tensorrt_libs')
			])
			library_paths = list(dict.fromkeys([ library_path for library_path in library_paths if os.path.exists(library_path) ]))

			subprocess.call([ shutil.which('conda'), 'env', 'config', 'vars', 'set', 'PATH=' + os.pathsep.join(library_paths) ])
