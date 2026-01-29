from typing import List, Optional, Tuple

from facefusion.cli_helper import render_table
from facefusion.logger import get_package_logger
from facefusion.types import DiskMetrics, ExecutionDevice, ExecutionDeviceFrequency, ExecutionDeviceProduct, ExecutionDeviceTemperature, ExecutionDeviceUtilization, ExecutionDeviceVideoMemory, MemoryMetrics, ProcessorMetrics, TableContent, TableHeader, ValueAndUnit


def compose_execution_devices(execution_devices : List[ExecutionDevice]) -> Tuple[List[TableHeader], List[List[TableContent]]]:
	headers : List[TableHeader] =\
	[
		'id',
		'vendor',
		'name',
		'frequency',
		'video memory',
		'temperature',
		'utilization'
	]
	contents : List[List[TableContent]] = []

	for device in execution_devices:
		contents.append(
		[
			device.get('id'),
			format_product_vendor(device.get('product')),
			format_product_name(device.get('product')),
			format_frequency(device.get('frequency')),
			format_video_memory(device.get('video_memory')),
			format_temperature(device.get('temperature')),
			format_utilization(device.get('utilization'))
		])

	return headers, contents


def compose_processors(processors : List[ProcessorMetrics]) -> Tuple[List[TableHeader], List[List[TableContent]]]:
	headers : List[TableHeader] =\
	[
		'id',
		'vendor',
		'name',
		'frequency',
		'utilization'
	]
	contents : List[List[TableContent]] = []

	for processor in processors:
		contents.append(
		[
			processor.get('id'),
			processor.get('vendor'),
			processor.get('name'),
			format_processor_value(processor.get('frequency')),
			format_processor_value(processor.get('utilization'))
		])

	return headers, contents


def compose_memory(memory : MemoryMetrics) -> Tuple[List[TableHeader], List[List[TableContent]]]:
	headers : List[TableHeader] = [ 'total', 'free', 'utilization' ]
	contents : List[List[TableContent]] = []

	contents.append(
	[
		format_value_and_unit(memory.get('total')),
		format_value_and_unit(memory.get('free')),
		format_value_and_unit(memory.get('utilization'))
	])

	return headers, contents


def compose_disk(disk : DiskMetrics) -> Tuple[List[TableHeader], List[List[TableContent]]]:
	headers : List[TableHeader] = [ 'total', 'free', 'utilization' ]
	contents : List[List[TableContent]] = []

	contents.append(
	[
		format_value_and_unit(disk.get('total')),
		format_value_and_unit(disk.get('free')),
		format_value_and_unit(disk.get('utilization'))
	])

	return headers, contents


def format_value_and_unit(value_and_unit : ValueAndUnit) -> str:
	return str(value_and_unit.get('value')) + ' ' + str(value_and_unit.get('unit'))


def format_processor_value(value_and_unit : ValueAndUnit) -> str:
	if value_and_unit:
		return format_value_and_unit(value_and_unit)
	return None


def format_product_vendor(product : ExecutionDeviceProduct) -> str:
	if product:
		return product.get('vendor')
	return None


def format_product_name(product : ExecutionDeviceProduct) -> str:
	if product:
		return product.get('name')
	return None


def format_frequency(frequency : ExecutionDeviceFrequency) -> str:
	if frequency:
		return format_value_and_unit(frequency.get('gpu'))
	return None


def format_video_memory(video_memory : ExecutionDeviceVideoMemory) -> str:
	if video_memory:
		return str(video_memory.get('free').get('value')) + ' / ' + str(video_memory.get('total').get('value')) + ' ' + str(video_memory.get('total').get('unit'))
	return None


def format_temperature(temperature : ExecutionDeviceTemperature) -> str:
	if temperature:
		return format_value_and_unit(temperature.get('gpu'))
	return None


def format_utilization(utilization : Optional[ExecutionDeviceUtilization]) -> str:
	if utilization:
		return format_value_and_unit(utilization.get('gpu'))
	return None


def render_execution_devices(execution_devices : List[ExecutionDevice]) -> None:
	package_logger = get_package_logger()
	package_logger.critical('')
	package_logger.critical('EXECUTION DEVICES')
	headers, contents = compose_execution_devices(execution_devices)
	render_table(headers, contents)


def render_processors(processors : List[ProcessorMetrics]) -> None:
	package_logger = get_package_logger()
	package_logger.critical('')
	package_logger.critical('PROCESSORS')
	headers, contents = compose_processors(processors)
	render_table(headers, contents)


def render_memory(memory : MemoryMetrics) -> None:
	package_logger = get_package_logger()
	package_logger.critical('')
	package_logger.critical('MEMORY')
	headers, contents = compose_memory(memory)
	render_table(headers, contents)


def render_disk(disk : DiskMetrics) -> None:
	package_logger = get_package_logger()
	package_logger.critical('')
	package_logger.critical('DISK')
	headers, contents = compose_disk(disk)
	render_table(headers, contents)
