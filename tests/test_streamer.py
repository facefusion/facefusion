from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy
import pytest

from facefusion import state_manager
from facefusion.logger import get_package_logger
from facefusion.streamer import process_stream_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('processors', [])


def test_process_stream_frame() -> None:
	source_vision_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	target_vision_frame = numpy.full((2, 2, 3), 100, numpy.uint8)
	output_vision_frame = process_stream_frame([ source_vision_frame ], target_vision_frame)

	assert output_vision_frame.tolist() == target_vision_frame.tolist()
	assert numpy.shares_memory(output_vision_frame, target_vision_frame) is False

	temp_vision_frame = numpy.full((2, 2, 3), 200, numpy.uint8)
	temp_vision_mask = numpy.zeros((2, 2), numpy.uint8)
	processor_module = SimpleNamespace(pre_process = Mock(return_value = True), process_frame = Mock(return_value = (temp_vision_frame, temp_vision_mask)))

	with patch('facefusion.streamer.get_processors_modules', return_value = [ processor_module, processor_module ]):
		output_vision_frame = process_stream_frame([ source_vision_frame ], target_vision_frame)

	process_frame_inputs = processor_module.process_frame.call_args_list[1].args[0]

	assert output_vision_frame is temp_vision_frame
	assert processor_module.pre_process.call_args.args == ('stream',)
	assert processor_module.process_frame.call_count == 2
	assert process_frame_inputs.get('source_vision_frames') == [ source_vision_frame ]
	assert process_frame_inputs.get('source_audio_frame').shape == (80, 16)
	assert process_frame_inputs.get('source_voice_frame').shape == (80, 16)
	assert process_frame_inputs.get('target_vision_frames') == [ target_vision_frame ]
	assert process_frame_inputs.get('temp_vision_frame') is temp_vision_frame
	assert process_frame_inputs.get('temp_vision_mask') is temp_vision_mask
	assert get_package_logger().disabled is False

	processor_module = SimpleNamespace(pre_process = Mock(return_value = False), process_frame = Mock())

	with patch('facefusion.streamer.get_processors_modules', return_value = [ processor_module ]):
		output_vision_frame = process_stream_frame([ source_vision_frame ], target_vision_frame)

	assert output_vision_frame.tolist() == target_vision_frame.tolist()
	assert processor_module.process_frame.call_count == 0
	assert get_package_logger().disabled is False
