from typing import Dict
import os
import platform
import shutil
import sys
import subprocess

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import wording

ONNXRUNTIMES : Dict[str, str] =\
{
	'cpu': 'onnxruntime==1.15.1',
	'cuda': 'onnxruntime-gpu==1.15.1',
	'coreml-legacy': 'onnxruntime-coreml==1.13.1',
	'coreml-silicon': 'onnxruntime-silicon==1.13.1',
	'directml': 'onnxruntime-directml==1.15.1',
	'openvino': 'onnxruntime-openvino==1.15.0'
}


def run() -> None:
	virtual_environment = None
	onnxruntime_name = None
	answers : Dict[str, str] = inquirer.prompt(
	[
		inquirer.List(
			'virtual_environment',
			message = wording.get('select_virtual_environment_install'),
			choices = [ 'conda', 'venv', 'none' ],
		),
		inquirer.List(
			'onnxruntime_key',
			message = wording.get('select_onnxruntime_install'),
			choices = list(ONNXRUNTIMES.keys()),
		)
	])

	if answers is not None:
		virtual_environment = answers['virtual_environment']
		onnxruntime_key = answers['onnxruntime_key']
		onnxruntime_name = ONNXRUNTIMES[onnxruntime_key]
		shutil.rmtree('venv', ignore_errors = True)
	if virtual_environment == 'conda':
		subprocess.call([ 'conda', 'create', '--prefix', 'venv', '-y' ])
	if virtual_environment == 'venv':
		subprocess.run([ sys.executable, '-m', 'venv', 'venv' ])
		if platform.system().lower() == 'windows':
			activate_path = os.path.join('venv', 'Scripts', 'activate.bat')
			subprocess.run([ activate_path ])
		else:
			activate_path = os.path.join('venv', 'bin', 'activate')
			subprocess.run([ 'source', activate_path ], shell = True)
	if answers is not None:
		subprocess.call([ 'pip', 'install', '-r', 'requirements.txt' ])
	if onnxruntime_name:
		if onnxruntime_name != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		subprocess.call([ 'pip', 'install', onnxruntime_name ])
