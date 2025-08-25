import os
import shutil
import signal
import subprocess
import sys
import time
from argparse import ArgumentParser, HelpFormatter
from functools import partial
from types import FrameType

# Try to import requests, if it fails, prompt the user to install it
try:
	import requests
except ImportError:
	print("Error: 'requests' library is not installed. Please install it first by running 'pip install requests'.")
	sys.exit(1)

from facefusion import metadata, wording
from facefusion.common_helper import is_linux, is_windows

# Define official and mirror pip sources
PIP_OFFICIAL_MIRROR = 'https://pypi.python.org/simple'
PIP_TUNA_MIRROR = 'https://pypi.tuna.tsinghua.edu.cn/simple'
PIP_ALIYUN_MIRROR = 'https://mirrors.aliyun.com/pypi/simple/'

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


def choose_pip_mirror() -> str:
	"""
	Tests pip sources by measuring their actual download speed (bandwidth)
	and returns the fastest one. This version includes a User-Agent header
	to avoid being blocked by anti-scraping mechanisms.
	"""
	mirrors = {
		"Official Source": PIP_OFFICIAL_MIRROR,
		"Tsinghua Mirror": PIP_TUNA_MIRROR,
		"Aliyun Mirror": PIP_ALIYUN_MIRROR
	}
	speeds = {}

	# Size of the data chunk to download for testing, e.g., 512 KB
	test_chunk_size_bytes = 512 * 1024

	# Masquerade as a common browser User-Agent to avoid being rejected by the server.
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
	}

	print("Testing pip source download speeds (bandwidth)...")

	for name, url in mirrors.items():
		try:
			print(f"- Testing {name} ({url})...")
			start_time = time.time()

			# Add the headers to the request.
			response = requests.get(url, stream=True, timeout=10, headers=headers)
			response.raise_for_status()

			downloaded_bytes = 0
			for chunk in response.iter_content(chunk_size=8192):
				downloaded_bytes += len(chunk)
				if downloaded_bytes >= test_chunk_size_bytes:
					break

			end_time = time.time()
			duration = end_time - start_time

			if duration == 0:
				speed_kbps = float('inf')
			else:
				speed_kbps = (downloaded_bytes / 1024) / duration

			speeds[name] = speed_kbps
			print(f"  => Speed: {speed_kbps:.2f} KB/s")

		except requests.RequestException as e:
			speeds[name] = 0
			print(f"  => Test failed: {e}")

	if not speeds or all(speed == 0 for speed in speeds.values()):
		print("\nAll pip sources are unreachable. Falling back to the default Official Source.")
		return PIP_OFFICIAL_MIRROR

	# Find the source with the highest speed.
	fastest_mirror_name = max(speeds, key=speeds.get)
	fastest_mirror_url = mirrors[fastest_mirror_name]

	print(f"\nTesting complete. Selected the fastest source: {fastest_mirror_name} ({fastest_mirror_url})\n")
	return fastest_mirror_url


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

	# Choose the fastest pip source

	PIP_MIRROR = choose_pip_mirror()

	if not args.skip_conda and not has_conda:
		sys.stdout.write(wording.get('conda_not_activated') + os.linesep)
		sys.exit(1)

	with open('requirements.txt') as file:

		for line in file.readlines():
			__line__ = line.strip()
			if not __line__.startswith('onnxruntime'):
				subprocess.call([ shutil.which('pip'), 'install', line, '--force-reinstall', '-i', PIP_MIRROR ])

	if args.onnxruntime == 'rocm':
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)

		if python_id in [ 'cp310', 'cp312' ]:
			wheel_name = 'onnxruntime_rocm-' + onnxruntime_version + '-' + python_id + '-' + python_id + '-linux_x86_64.whl'
			wheel_url = 'https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4/' + wheel_name
			subprocess.call([ shutil.which('pip'), 'install', wheel_url, '--force-reinstall', '-i', PIP_MIRROR ])
	else:
		subprocess.call([ shutil.which('pip'), 'install', onnxruntime_name + '==' + onnxruntime_version, '--force-reinstall', '-i',PIP_MIRROR ])

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
		subprocess.call([ shutil.which('pip'), 'install', 'numpy==1.26.4', '--force-reinstall', '-i', PIP_MIRROR ])
