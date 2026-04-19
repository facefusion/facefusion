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

LOCALES =\
{
	'install_dependency': 'install the {dependency} package',
	'force_reinstall': 'force reinstall of packages',
	'skip_conda': 'skip the conda environment check',
	'conda_not_activated': 'conda is not activated'
}
ONNXRUNTIME_SET =\
{
	'default': ('onnxruntime', '1.24.4')
}
if is_windows() or is_linux():
	ONNXRUNTIME_SET['cuda'] = ('onnxruntime-gpu', '1.24.4')
	ONNXRUNTIME_SET['openvino'] = ('onnxruntime-openvino', '1.24.1')
if is_windows():
	ONNXRUNTIME_SET['directml'] = ('onnxruntime-directml', '1.24.4')
	ONNXRUNTIME_SET['qnn'] = ('onnxruntime-qnn', '1.24.4')
if is_linux():
	ONNXRUNTIME_SET['migraphx'] = ('onnxruntime-migraphx', '1.24.2')
	ONNXRUNTIME_SET['rocm'] = ('onnxruntime-rocm', '1.22.2.post1')


def cli() -> None:
	signal.signal(signal.SIGINT, signal_exit)
	program = ArgumentParser(formatter_class = partial(HelpFormatter, max_help_position = 50))
	program.add_argument('--onnxruntime', help = LOCALES.get('install_dependency').format(dependency = 'onnxruntime'), choices = ONNXRUNTIME_SET.keys(), required = True)
	program.add_argument('--force-reinstall', help = LOCALES.get('force_reinstall'), action = 'store_true')
	program.add_argument('--skip-conda', help = LOCALES.get('skip_conda'), action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def signal_exit(signum : int, frame : FrameType) -> None:
	sys.exit(0)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()
	has_conda = 'CONDA_PREFIX' in os.environ

	if not args.skip_conda and not has_conda:
		sys.stdout.write(LOCALES.get('conda_not_activated') + os.linesep)
		sys.exit(1)

	commands = [ shutil.which('pip'), 'install' ]

	if args.force_reinstall:
		commands.append('--force-reinstall')

	with open('requirements.txt') as file:

		for line in file.readlines():
			__line__ = line.strip()
			if not __line__.startswith('onnxruntime'):
				commands.append(__line__)

	onnxruntime_name, onnxruntime_version = ONNXRUNTIME_SET.get(args.onnxruntime)
	commands.append(onnxruntime_name + '==' + onnxruntime_version)

	subprocess.call([ shutil.which('pip'), 'uninstall', 'onnxruntime', onnxruntime_name, '-y', '-q' ])

	subprocess.call(commands)
