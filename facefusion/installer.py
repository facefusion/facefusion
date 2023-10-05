from typing import Dict, Tuple
import os
import sys
import subprocess
import tempfile
from argparse import ArgumentParser, HelpFormatter

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import metadata, wording

TORCH : Dict[str, str] =\
{
	'cpu': 'https://download.pytorch.org/whl/cpu',
	'cuda': 'https://download.pytorch.org/whl/cu118',
	'rocm': 'https://download.pytorch.org/whl/rocm5.6'
}
ONNXRUNTIMES : Dict[str, Tuple[str, str]] =\
{
	'cpu': ('onnxruntime', '1.16.0 '),
	'cuda': ('onnxruntime-gpu', '1.16.0'),
	'coreml-legacy': ('onnxruntime-coreml', '1.13.1'),
	'coreml-silicon': ('onnxruntime-silicon', '1.14.2'),
	'directml': ('onnxruntime-directml', '1.16.0'),
	'openvino': ('onnxruntime-openvino', '1.15.0')
}


def cli() -> None:
	program = ArgumentParser(formatter_class = lambda prog: HelpFormatter(prog, max_help_position = 120))
	program.add_argument('--torch', help = wording.get('install_dependency_help').format(dependency = 'torch'), dest = 'torch', choices = TORCH.keys())
	program.add_argument('--onnxruntime', help = wording.get('install_dependency_help').format(dependency = 'onnxruntime'), dest = 'onnxruntime', choices = ONNXRUNTIMES.keys())
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()

	if args.onnxruntime:
		answers =\
		{
			'torch': args.torch,
			'onnxruntime': args.onnxruntime
		}
	else:
		answers = inquirer.prompt(
		[
			inquirer.List(
				'torch',
				message = wording.get('install_dependency_help').format(dependency = 'torch'),
				choices = list(TORCH.keys())
			),
			inquirer.List(
				'onnxruntime',
				message = wording.get('install_dependency_help').format(dependency = 'onnxruntime'),
				choices = list(ONNXRUNTIMES.keys())
			)
		])
	if answers is not None:
		torch = answers['torch']
		torch_url = TORCH[torch]
		onnxruntime = answers['onnxruntime']
		onnxruntime_name, onnxruntime_version = ONNXRUNTIMES[onnxruntime]
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)
		subprocess.call([ 'pip', 'uninstall', 'torch', '-y' ])
		subprocess.call([ 'pip', 'install', '-r', 'requirements.txt', '--extra-index-url', torch_url ])
		if onnxruntime != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		if onnxruntime != 'coreml-silicon':
			subprocess.call([ 'pip', 'install', onnxruntime_name + '==' + onnxruntime_version ])
		elif python_id in [ 'cp39', 'cp310', 'cp311' ]:
			wheel_name = '-'.join([ 'onnxruntime_silicon', onnxruntime_version, python_id, python_id, 'macosx_12_0_arm64.whl' ])
			wheel_path = os.path.join(tempfile.gettempdir(), wheel_name)
			wheel_url = 'https://github.com/cansik/onnxruntime-silicon/releases/download/v' + onnxruntime_version + '/' + wheel_name
			subprocess.call([ 'curl', '--silent', '--location', '--continue-at', '-', '--output', wheel_path, wheel_url ])
			subprocess.call([ 'pip', 'install', wheel_path ])
			os.remove(wheel_path)
