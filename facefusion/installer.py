from typing import Dict, Tuple
import sys
import os
import platform
import tempfile
import subprocess
import inquirer
from argparse import ArgumentParser, HelpFormatter

from facefusion import metadata, wording

if platform.system().lower() == 'darwin':
	os.environ['SYSTEM_VERSION_COMPAT'] = '0'

ONNXRUNTIMES : Dict[str, Tuple[str, str]] = {}

if platform.system().lower() == 'darwin':
	ONNXRUNTIMES['default'] = ('onnxruntime', '1.17.1')
else:
	ONNXRUNTIMES['default'] = ('onnxruntime', '1.17.1')
	ONNXRUNTIMES['cuda-12.2'] = ('onnxruntime-gpu', '1.17.1')
	ONNXRUNTIMES['cuda-11.8'] = ('onnxruntime-gpu', '1.17.1')
	ONNXRUNTIMES['openvino'] = ('onnxruntime-openvino', '1.17.1')
if platform.system().lower() == 'linux':
	ONNXRUNTIMES['rocm-5.4.2'] = ('onnxruntime-rocm', '1.16.3')
	ONNXRUNTIMES['rocm-5.6'] = ('onnxruntime-rocm', '1.16.3')
if platform.system().lower() == 'windows':
	ONNXRUNTIMES['directml'] = ('onnxruntime-directml', '1.17.1')


def cli() -> None:
	program = ArgumentParser(formatter_class = lambda prog: HelpFormatter(prog, max_help_position = 130))
	program.add_argument('--onnxruntime', help = wording.get('help.install_dependency').format(dependency = 'onnxruntime'), choices = ONNXRUNTIMES.keys())
	program.add_argument('--skip-conda', help = wording.get('help.skip_conda'), action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()
	python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)

	if not args.skip_conda and 'CONDA_PREFIX' not in os.environ:
		sys.stdout.write(wording.get('conda_not_activated') + os.linesep)
		sys.exit(1)
	if args.onnxruntime:
		answers =\
		{
			'onnxruntime': args.onnxruntime
		}
	else:
		answers = inquirer.prompt(
		[
			inquirer.List('onnxruntime', message = wording.get('help.install_dependency').format(dependency = 'onnxruntime'), choices = list(ONNXRUNTIMES.keys()))
		])
	if answers:
		onnxruntime = answers['onnxruntime']
		onnxruntime_name, onnxruntime_version = ONNXRUNTIMES[onnxruntime]

		subprocess.call([ 'pip', 'install', '-r', 'requirements.txt', '--force-reinstall' ])
		if onnxruntime == 'rocm-5.4.2' or onnxruntime == 'rocm-5.6':
			if python_id in [ 'cp39', 'cp310', 'cp311' ]:
				rocm_version = onnxruntime.replace('-', '')
				rocm_version = rocm_version.replace('.', '')
				wheel_name = 'onnxruntime_training-' + onnxruntime_version + '+' + rocm_version + '-' + python_id + '-' + python_id + '-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'
				wheel_path = os.path.join(tempfile.gettempdir(), wheel_name)
				wheel_url = 'https://download.onnxruntime.ai/' + wheel_name
				subprocess.call([ 'curl', '--silent', '--location', '--continue-at', '-', '--output', wheel_path, wheel_url ])
				subprocess.call([ 'pip', 'uninstall', wheel_path, '-y', '-q' ])
				subprocess.call([ 'pip', 'install', wheel_path, '--force-reinstall' ])
				os.remove(wheel_path)
		else:
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y', '-q' ])
			if onnxruntime == 'cuda-12.2':
				subprocess.call([ 'pip', 'install', onnxruntime_name + '==' + onnxruntime_version, '--extra-index-url', 'https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple', '--force-reinstall' ])
			else:
				subprocess.call([ 'pip', 'install', onnxruntime_name + '==' + onnxruntime_version, '--force-reinstall' ])
