import tempfile
from time import time

import pytest

from facefusion import ffmpeg, ffmpeg_builder, inference_manager, process_manager, state_manager, video_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_video_metadata
from facefusion.workflows.audio_to_image import process
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	inference_manager.init()
	video_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
		)
	)

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('execution_thread_count', 2)
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('temp_pixel_format', 'bgr24')
	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ])
	state_manager.init_item('target_path', get_test_example_file('target-240p.jpg'))
	state_manager.init_item('workflow_mode', 'audio-to-image:video')
	state_manager.init_item('reference_frame_index', 0)
	state_manager.init_item('target_frame_amount', 1)
	state_manager.init_item('trim_frame_start', 0)
	state_manager.init_item('trim_frame_end', 10)
	state_manager.init_item('output_audio_encoder', 'aac')
	state_manager.init_item('output_audio_quality', 100)
	state_manager.init_item('output_audio_volume', 100)
	state_manager.init_item('output_video_encoder', 'libx264')
	state_manager.init_item('output_video_quality', 100)
	state_manager.init_item('output_video_preset', 'ultrafast')
	state_manager.init_item('output_video_fps', 25)
	state_manager.init_item('output_video_scale', 1.0)
	state_manager.init_item('output_audio_fps', 25)
	state_manager.init_item('voice_extractor_model', 'kim_vocal_2')
	state_manager.init_item('output_image_scale', 1.0)
	state_manager.init_item('processors', [])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_process() -> None:
	state_manager.set_item('output_path', get_test_output_path('test-process.mp4'))

	assert process(time()) == 0
	assert extract_video_metadata(get_test_output_path('test-process.mp4')).get('frame_total') == 10
	assert process_manager.is_pending() is True

	state_manager.set_item('trim_frame_start', 10)
	state_manager.set_item('output_path', get_test_output_path('test-process-empty.mp4'))

	assert process(time()) == 1
	assert is_test_output_file('test-process-empty.mp4') is False
	assert process_manager.is_pending() is True

	state_manager.set_item('trim_frame_start', 0)
