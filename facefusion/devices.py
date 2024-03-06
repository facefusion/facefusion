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
		output = subprocess.check_output([ 'nvidia-smi', '--query', '--xml-format' ])
		output = ElementTree.fromstring(output)

		for gpu in output.findall('gpu'):
			cuda_devices.append(
			{
				'driver_version': output.find('.//driver_version').text,
				'framework':
				{
					'name': 'cuda',
					'version': output.find('.//cuda_version').text,
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
	except Exception:
		pass
	return cuda_devices


def create_value_and_unit(text : str) -> ValueAndUnit:
	value, unit = text.split()
	value_and_unit : ValueAndUnit =\
	{
		'value': value,
		'unit': unit
	}

	return value_and_unit
