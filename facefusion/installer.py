import os
import subprocess
import sys
from typing import Dict
import inquirer

def install_package(package_name: str) -> None:
    subprocess.call(['pip', 'install', package_name, '-q'])

def uninstall_package(package_name: str) -> None:
    subprocess.call(['pip', 'uninstall', package_name, '-y'])

def install_requirements(venv_python_bin: str):
    subprocess.run([venv_python_bin, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    
def select_onnxruntime() -> str:
    ONNXRUNTIMES = {
        'cpu': 'onnxruntime==1.15.1',
        'coreml-legacy': 'onnxruntime-coreml==1.13.1',
        'coreml-silicon': 'onnxruntime-silicon==1.13.1',
        'cuda': 'onnxruntime-gpu==1.15.1',
        'directml': 'onnxruntime-directml==1.15.1',
        'openvino': 'onnxruntime-openvino==1.15.0'
    }
    choices = list(ONNXRUNTIMES.keys())
    onnxruntime_key = None
    try:
        answers = inquirer.prompt([
            inquirer.List(
                'onnxruntime_key',
                message='Select the ONNX Runtime to install',
                choices=choices,
            )
        ])
        if answers is not None:
            onnxruntime_key = answers['onnxruntime_key']
    except ImportError:
        for i, choice in enumerate(choices):
            print(f"{i + 1}. {choice}")
        choice_index = int(input("Enter the number of your choice: ")) - 1
        if 0 <= choice_index < len(choices):
            onnxruntime_key = choices[choice_index]
    if onnxruntime_key:
        return ONNXRUNTIMES[onnxruntime_key]
    else:
        return ''

def create_virtual_environment() -> None:
    questions = [
        inquirer.List(
            'venv_type',
            message="Select the virtual environment type",
            choices=['venv', 'conda', 'none'],
            default='venv',
        )
    ]
    answers = inquirer.prompt(questions)
    venv_type = answers['venv_type']
    if venv_type == "conda":
        subprocess.call(['conda', 'create', '--name', 'venv', 'python=3.10'])        
    elif venv_type == "venv":
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor not in (9, 10):
            print("Python 3.9 or 3.10 is required.")
            sys.exit(1)
        subprocess.call([sys.executable, '-m', 'venv', 'venv'])  
    else:
        pass
    
def run() -> None:
    create_virtual_environment()    
    venv_python_bin = 'venv/bin/python' if sys.platform != 'win32' else 'venv\\Scripts\\python.exe'    
    onnxruntime_name = select_onnxruntime()    
    if onnxruntime_name:
        install_package('inquirer')
        install_requirements(venv_python_bin)
        if onnxruntime_name != 'onnxruntime':
            uninstall_package('onnxruntime')
            uninstall_package(onnxruntime_name)
        install_package(onnxruntime_name)
