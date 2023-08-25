import os
import platform
import shutil
import sys
from typing import Dict
import subprocess

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import wording

ONNXRUNTIMES =\
{
	'cpu': 'onnxruntime==1.15.1',
	'cuda': 'onnxruntime-gpu==1.15.1',
	'coreml-legacy': 'onnxruntime-coreml==1.13.1',
	'coreml-silicon': 'onnxruntime-silicon==1.13.1',
	'directml': 'onnxruntime-directml==1.15.1',
	'openvino': 'onnxruntime-openvino==1.15.0'
}


def run() -> None:
	install_venv = None
	onnxruntime_name = None
	answers : Dict[str, str] = inquirer.prompt(
	[
		inquirer.Confirm(
			'install_venv',
			message = wording.get('create_venv_install'),
			default = True
		),
		inquirer.List(
			'onnxruntime_key',
			message = wording.get('select_onnxruntime_install'),
			choices = list(ONNXRUNTIMES.keys()),
		)
	])

	if answers is not None:
		install_venv = answers['install_venv']
		onnxruntime_key = answers['onnxruntime_key']
		onnxruntime_name = ONNXRUNTIMES[onnxruntime_key]
	if install_venv:
		shutil.rmtree('venv', ignore_errors = True)
		subprocess.run([ sys.executable, '-m', 'venv', 'venv' ])
		if platform.system().lower() == 'windows':
			activate_path = os.path.join('venv', 'Scripts', 'activate.bat')
			subprocess.run([ activate_path ])
		else:
			activate_path = os.path.join('venv', 'bin', 'activate')
			subprocess.run([ 'source', activate_path ], shell = True)
	subprocess.call([ 'pip', 'install', '-r', 'requirements.txt' ])
	if onnxruntime_name:
		if onnxruntime_name != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		subprocess.call([ 'pip', 'install', onnxruntime_name ])
