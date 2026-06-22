import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.common_helper import get_first
from facefusion.download import conditional_download
from facefusion.face_selector import select_faces
from facefusion.face_store import clear_faces
from facefusion.vision import read_static_image, read_static_video_chunk, read_static_video_frame
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_landmarker_model', 'many')
	state_manager.init_item('face_landmarker_score', 0.5)
	state_manager.init_item('face_selector_mode', 'many')
	state_manager.init_item('face_selector_order', None)
	state_manager.init_item('face_selector_gender', None)
	state_manager.init_item('face_selector_race', None)
	state_manager.init_item('face_selector_age_start', 0)
	state_manager.init_item('face_selector_age_end', 0)
	state_manager.init_item('target_frame_amount', 3)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_landmarker.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_landmarker.clear_inference_pool()
	face_recognizer.clear_inference_pool()
	clear_faces()


def test_select_faces_with_tracking() -> None:
	state_manager.set_item('target_frame_amount', 3)
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	video_frame_chunk = read_static_video_chunk(get_test_example_file('target-240p.mp4'), 0, 7)
	target_vision_frames = [ video_frame_chunk.get(frame_number) for frame_number in sorted(video_frame_chunk) ]
	empty_vision_frame = numpy.zeros_like(get_first(target_vision_frames))

	target_vision_frames[2] = empty_vision_frame
	target_vision_frames[3] = empty_vision_frame
	target_vision_frames[4] = empty_vision_frame
	target_vision_frames[5] = empty_vision_frame

	target_faces = select_faces(source_vision_frame, [ source_vision_frame ], target_vision_frames)

	assert len(target_faces) == 1
	assert target_faces[0].origin == 'refill'


def test_select_faces_without_tracking() -> None:
	state_manager.set_item('target_frame_amount', 0)
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	target_vision_frame = read_static_video_frame(get_test_example_file('target-240p.mp4'), 0)

	target_faces = select_faces(source_vision_frame, [ source_vision_frame ], [ target_vision_frame ])

	assert len(target_faces) == 1
	assert target_faces[0].origin == 'detect'
