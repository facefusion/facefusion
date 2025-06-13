import os
import shutil
import signal
import subprocess
import sys
from argparse import ArgumentParser, HelpFormatter
from functools import partial
from types import FrameType

from facefusion import metadata, wording
from facefusion.common_helper import is_linux, is_windows

ONNXRUNTIME_SET =\
{
	'default': ('onnxruntime', '1.22.0')
}
if is_windows() or is_linux():
	ONNXRUNTIME_SET['cuda'] = ('onnxruntime-gpu', '1.22.0')
	ONNXRUNTIME_SET['openvino'] = ('onnxruntime-openvino', '1.22.0')
if is_windows():
	ONNXRUNTIME_SET['directml'] = ('onnxruntime-directml', '1.17.3')
if is_linux():
	ONNXRUNTIME_SET['rocm'] = ('onnxruntime-rocm', '1.21.0')


def cli() -> None:
	signal.signal(signal.SIGINT, signal_exit)
	program = ArgumentParser(formatter_class = partial(HelpFormatter, max_help_position = 50))
	program.add_argument('--onnxruntime', help = wording.get('help.install_dependency').format(dependency = 'onnxruntime'), choices = ONNXRUNTIME_SET.keys(), required = True)
	program.add_argument('--skip-conda', help = wording.get('help.skip_conda'), action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def signal_exit(signum : int, frame : FrameType) -> None:
	sys.exit(0)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()
	has_conda = 'CONDA_PREFIX' in os.environ
	onnxruntime_name, onnxruntime_version = ONNXRUNTIME_SET.get(args.onnxruntime)

	if not args.skip_conda and not has_conda:
		sys.stdout.write(wording.get('conda_not_activated') + os.linesep)
		sys.exit(1)

	with open('requirements.txt') as file:

		for line in file.readlines():
			__line__ = line.strip()
			if not __line__.startswith('onnxruntime'):
				subprocess.call([ shutil.which('pip'), 'install', line, '--force-reinstall' ])

	if args.onnxruntime == 'rocm':
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)

		if python_id in [ 'cp310', 'cp312' ]:
			wheel_name = 'onnxruntime_rocm-' + onnxruntime_version + '-' + python_id + '-' + python_id + '-linux_x86_64.whl'
			wheel_url = 'https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4/' + wheel_name
			subprocess.call([ shutil.which('pip'), 'install', wheel_url, '--force-reinstall' ])
	else:
		subprocess.call([ shutil.which('pip'), 'install', onnxruntime_name + '==' + onnxruntime_version, '--force-reinstall' ])

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

	if args.onnxruntime == 'directml':
		subprocess.call([ shutil.which('pip'), 'install', 'numpy==1.26.4', '--force-reinstall' ])
