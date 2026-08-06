import pytest

from facefusion import state_manager
from facefusion.download import conditional_download
from facefusion.workflows.core import detect_workflow_mode
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


def test_detect_workflow_mode() -> None:
	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('target-240p.mp4'))
	state_manager.init_item('output_path', 'output.mp4')

	assert detect_workflow_mode() == 'image-to-video'

	state_manager.init_item('output_path', 'output')

	assert detect_workflow_mode() == 'image-to-video:frames'

	state_manager.init_item('source_paths', [ get_test_example_file('source.mp3') ])
	state_manager.init_item('target_path', get_test_example_file('source.jpg'))
	state_manager.init_item('output_path', 'output.jpg')

	assert detect_workflow_mode() == 'audio-to-image:video'

	state_manager.init_item('output_path', 'output')

	assert detect_workflow_mode() == 'audio-to-image:frames'

	state_manager.init_item('source_paths', [ get_test_example_file('source.jpg') ])
	state_manager.init_item('target_path', get_test_example_file('source.jpg'))

	assert detect_workflow_mode() == 'image-to-image'
