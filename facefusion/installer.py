from typing import Dict, Tuple
import os
import platform
import shutil
import sys
import subprocess

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import wording

ONNXRUNTIMES : Dict[str, Tuple[str, str]] =\
{
	'cpu': ('onnxruntime', '1.15.1'),
	'cuda': ('onnxruntime-gpu', '1.15.1'),
	'coreml-legacy': ('onnxruntime-coreml', '1.13.1'),
	'coreml-silicon': ('onnxruntime-silicon', '1.13.1'),
	'directml': ('onnxruntime-directml', '1.15.1'),
	'openvino': ('onnxruntime-openvino', '1.15.0')
}


def run() -> None:
	virtual_environment = None
	onnxruntime_key = None
	onnxruntime_name = None
	onnxruntime_version = None
	answers : Dict[str, str] = inquirer.prompt(
	[
		inquirer.List(
			'virtual_environment',
			message = wording.get('select_virtual_environment_install'),
			choices = [ 'venv', 'none' ]
		),
		inquirer.List(
			'onnxruntime_key',
			message = wording.get('select_onnxruntime_install'),
			choices = list(ONNXRUNTIMES.keys())
		)
	])

	if answers is not None:
		virtual_environment = answers['virtual_environment']
		onnxruntime_key = answers['onnxruntime_key']
		onnxruntime_name, onnxruntime_version = ONNXRUNTIMES[onnxruntime_key]
		shutil.rmtree('venv', ignore_errors = True)
	if virtual_environment == 'venv':
		subprocess.call([ sys.executable, '-m', 'venv', 'venv' ])
		if platform.system().lower() == 'windows':
			activate_path = os.path.join('venv', 'Scripts', 'activate.bat')
			subprocess.call([ activate_path ])
		else:
			activate_path = os.path.join('venv', 'bin', 'activate')
			subprocess.call([ 'bash', '-c', 'source ' + activate_path ])
	if answers is not None:
		subprocess.call([ 'pip', 'install', '-r', 'requirements.txt' ])
	if onnxruntime_key:
		if onnxruntime_key != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		subprocess.call([ 'pip', 'install', onnxruntime_name + '==' + onnxruntime_version ])
