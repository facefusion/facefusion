from typing import List, Optional

from facefusion import logger, translator
from facefusion.types import DiskMetrics, ExecutionDevice, MemoryMetrics, ProcessorMetrics


def render_execution_devices(execution_devices : Optional[List[ExecutionDevice]]) -> None:
	package_logger = logger.get_package_logger()
	package_logger.critical(translator.get('metrics.execution_devices'))

	if execution_devices:
		for device in execution_devices:
			product = device.get('product')
			frequency = device.get('frequency')
			video_memory = device.get('video_memory')
			temperature = device.get('temperature')
			utilization = device.get('utilization')

			if device.get('id'):
				package_logger.critical(translator.get('metrics.id').format(value = device.get('id')))

			if product.get('vendor'):
				package_logger.critical(translator.get('metrics.vendor').format(value = product.get('vendor')))

			if product.get('name'):
				package_logger.critical(translator.get('metrics.name').format(value = product.get('name')))

			if frequency.get('gpu'):
				package_logger.critical(translator.get('metrics.frequency').format(value = frequency.get('gpu').get('value'), unit = frequency.get('gpu').get('unit')))

			if video_memory.get('total') and video_memory.get('free'):
				package_logger.critical(translator.get('metrics.video_memory').format(free = video_memory.get('free').get('value'), total = video_memory.get('total').get('value'), unit = video_memory.get('total').get('unit')))

			if temperature.get('gpu'):
				package_logger.critical(translator.get('metrics.temperature').format(value = temperature.get('gpu').get('value'), unit = temperature.get('gpu').get('unit')))

			if utilization.get('gpu'):
				package_logger.critical(translator.get('metrics.utilization').format(value = utilization.get('gpu').get('value'), unit = utilization.get('gpu').get('unit')))

		return None

	package_logger.critical(translator.get('metrics.not_available'))

	return None


def render_processors(processors : Optional[List[ProcessorMetrics]]) -> None:
	package_logger = logger.get_package_logger()
	package_logger.critical('')
	package_logger.critical(translator.get('metrics.processors'))

	if processors:
		for processor in processors:

			if processor.get('id'):
				package_logger.critical(translator.get('metrics.id').format(value = processor.get('id')))

			if processor.get('name'):
				package_logger.critical(translator.get('metrics.name').format(value = processor.get('name')))

			if processor.get('frequency'):
				package_logger.critical(translator.get('metrics.frequency').format(value = processor.get('frequency').get('value'), unit = processor.get('frequency').get('unit')))

			if processor.get('temperature'):
				package_logger.critical(translator.get('metrics.temperature').format(value = processor.get('temperature').get('value'), unit = processor.get('temperature').get('unit')))

			if processor.get('utilization'):
				package_logger.critical(translator.get('metrics.utilization').format(value = processor.get('utilization').get('value'), unit = processor.get('utilization').get('unit')))

		return None

	package_logger.critical(translator.get('metrics.not_available'))

	return None


def render_memory(memory : Optional[MemoryMetrics]) -> None:
	package_logger = logger.get_package_logger()
	package_logger.critical('')
	package_logger.critical(translator.get('metrics.memory'))

	if memory:
		package_logger.critical(translator.get('metrics.total').format(value = memory.get('total').get('value'), unit = memory.get('total').get('unit')))
		package_logger.critical(translator.get('metrics.free').format(value = memory.get('free').get('value'), unit = memory.get('free').get('unit')))
		package_logger.critical(translator.get('metrics.utilization').format(value = memory.get('utilization').get('value'), unit = memory.get('utilization').get('unit')))

		return None

	package_logger.critical(translator.get('metrics.not_available'))

	return None


def render_disk(disk : Optional[DiskMetrics]) -> None:
	package_logger = logger.get_package_logger()
	package_logger.critical('')
	package_logger.critical(translator.get('metrics.disk'))

	if disk:
		package_logger.critical(translator.get('metrics.total').format(value = disk.get('total').get('value'), unit = disk.get('total').get('unit')))
		package_logger.critical(translator.get('metrics.free').format(value = disk.get('free').get('value'), unit = disk.get('free').get('unit')))
		package_logger.critical(translator.get('metrics.utilization').format(value = disk.get('utilization').get('value'), unit = disk.get('utilization').get('unit')))

		return None

	package_logger.critical(translator.get('metrics.not_available'))

	return None
