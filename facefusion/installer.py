from typing import Dict
import subprocess

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

from facefusion import wording

ONNXRUNTIMES =\
{
	'cpu': 'onnxruntime==1.15.1',
	'coreml': 'onnxruntime-silicon==1.13.1',
	'coreml-silicon': 'onnxruntime-coreml==1.13.1',
	'cuda': 'onnxruntime-gpu==1.15.1',
	'directml': 'onnxruntime-directml==1.15.1',
	'openvino': 'onnxruntime-openvino==1.15.0'
}


def run() -> None:
	onnxruntime_name = None
	answers : Dict[str, str] = inquirer.prompt(
	[
		inquirer.List(
			'onnxruntime_key',
			message = wording.get('select_onnxruntime_installed'),
			choices = list(ONNXRUNTIMES.keys()),
		)
	])

	if answers is not None:
		onnxruntime_key = answers['onnxruntime_key']
		onnxruntime_name = ONNXRUNTIMES[onnxruntime_key]

	if onnxruntime_name:
		subprocess.call([ 'pip', 'install', '-r', 'requirements.txt' ])
		if onnxruntime_name != 'cpu':
			subprocess.call([ 'pip', 'uninstall', 'onnxruntime', onnxruntime_name, '-y' ])
		subprocess.call([ 'pip', 'install', onnxruntime_name ])
