from typing import Dict, Tuple
import argparse
import os
import sys
import subprocess
import tempfile

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import metadata, wording

ONNXRUNTIMES : Dict[str, Tuple[str, str]] =\
{
	'cpu': ('onnxruntime', '1.15.1'),
	'cuda': ('onnxruntime-gpu', '1.15.1'),
	'coreml-legacy': ('onnxruntime-coreml', '1.13.1'),
	'coreml-silicon': ('onnxruntime-silicon', '1.14.2'),
	'directml': ('onnxruntime-directml', '1.15.1'),
	'openvino': ('onnxruntime-openvino', '1.15.0')
}


def run() -> None:
	program = argparse.ArgumentParser(formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 120))
	program.add_argument('--onnxruntime', help = wording.get('onnxruntime_help'), dest = 'onnxruntime', choices = ONNXRUNTIMES.keys())
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	args = program.parse_args()

	if args.onnxruntime:
		answers =\
		{
			'onnxruntime': args.onnxruntime
		}
	else:
		answers = inquirer.prompt(
		[
			inquirer.List(
				'onnxruntime',
				message = wording.get('onnxruntime_help'),
				choices = list(ONNXRUNTIMES.keys())
			)
		])

	if answers is not None:
		onnxruntime = answers['onnxruntime']
		onnxruntime_name, onnxruntime_version = ONNXRUNTIMES[onnxruntime]
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)
		subprocess.call([ 'pip', 'uninstall', 'torch', '-y' ])
		if onnxruntime == 'cuda':
			subprocess.call([ 'pip', 'install', '-r', 'requirements.txt', '--extra-index-url', 'https://download.pytorch.org/whl/cu118' ])
		else:
			subprocess.call([ 'pip', 'install', '-r', 'requirements.txt' ])
		if onnxruntime != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		if onnxruntime != 'coreml-silicon':
			subprocess.call([ 'pip', 'install', onnxruntime_name + '==' + onnxruntime_version ])
		elif python_id in [ 'cp39', 'cp310', 'cp311' ]:
			wheel_name = '-'.join([ 'onnxruntime_silicon', onnxruntime_version, python_id, python_id, 'macosx_12_0_arm64.whl' ])
			wheel_path = os.path.join(tempfile.gettempdir(), wheel_name)
			wheel_url = 'https://github.com/cansik/onnxruntime-silicon/releases/download/v' + onnxruntime_version + '/' + wheel_name
			subprocess.call([ 'curl', wheel_url, '-o', wheel_path, '-L' ])
			subprocess.call([ 'pip', 'install', wheel_path ])
			os.remove(wheel_path)
