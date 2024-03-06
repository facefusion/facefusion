from typing import List
from functools import lru_cache
import subprocess
import xml.etree.ElementTree as ElementTree

from facefusion.typing import GpuDevice, ValueAndUnit


@lru_cache(maxsize = None)
def detect_static_cuda_devices() -> List[GpuDevice]:
	return detect_cuda_devices()


def detect_cuda_devices() -> List[GpuDevice]:
	cuda_devices : List[GpuDevice] = []
	try:
		output, _ = run_nvidia_smi().communicate()
		contents = ElementTree.fromstring(output)
	except FileNotFoundError:
		contents = ElementTree.Element('xml')

	for gpu in contents.findall('gpu'):
		cuda_devices.append(
		{
			'driver_version': contents.find('.//driver_version').text,
			'framework':
			{
				'name': 'cuda',
				'version': contents.find('.//cuda_version').text,
			},
			'product':
			{
				'vendor': 'nvidia',
				'name': gpu.find('product_name').text.lower().replace('nvidia ', ''),
				'architecture': gpu.find('product_architecture').text.lower(),
			},
			'video_memory':
			{
				'total': create_value_and_unit(gpu.find('fb_memory_usage/total').text),
				'free': create_value_and_unit(gpu.find('fb_memory_usage/free').text)
			},
			'utilization':
			{
				'gpu': create_value_and_unit(gpu.find('utilization/gpu_util').text),
				'memory': create_value_and_unit(gpu.find('utilization/memory_util').text)
			}
		})
	return cuda_devices


def run_nvidia_smi() -> subprocess.Popen[bytes]:
	commands = [ 'nvidia-smi', '--query', '--xml-format' ]
	return subprocess.Popen(commands, stdout = subprocess.PIPE)


def create_value_and_unit(text : str) -> ValueAndUnit:
	value, unit = text.split()
	value_and_unit : ValueAndUnit =\
	{
		'value': value,
		'unit': unit
	}

	return value_and_unit
