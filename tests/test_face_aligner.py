import numpy
import pytest

from facefusion import face_aligner, face_detector, inference_manager, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.face_aligner import collect_model_downloads, conditional_optimize_contrast, detect_face_landmark, detect_with_2dfan4, detect_with_hrffa, detect_with_peppa_wutz, estimate_face_landmark_68_5
from facefusion.face_detector import detect_with_yolo_face
from facefusion.types import BoundingBox
from facefusion.vision import read_static_image
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_aligner_model', 'many')

	face_detector.pre_check()

	for face_aligner_model in [ 'many', 'hrffa' ]:
		state_manager.set_item('face_aligner_model', face_aligner_model)
		face_aligner.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_aligner.clear_inference_pool()


def get_bounding_box() -> BoundingBox:
	source_frame = read_static_image(get_test_example_file('source.jpg'))
	bounding_boxes, _, _ = detect_with_yolo_face(source_frame, '640x640')
	return bounding_boxes[0]


def test_collect_model_downloads() -> None:
	for face_aligner_model, model_names in [ ('many', [ 'fan_68_5', '2dfan4', 'peppa_wutz' ]), ('2dfan4', [ 'fan_68_5', '2dfan4' ]), ('hrffa', [ 'fan_68_5', 'hrffa' ]), ('peppa_wutz', [ 'fan_68_5', 'peppa_wutz' ]) ]:
		state_manager.set_item('face_aligner_model', face_aligner_model)
		model_hash_set, model_source_set = collect_model_downloads()

		assert list(model_hash_set.keys()) == model_names
		assert list(model_source_set.keys()) == model_names


def test_detect_face_landmark() -> None:
	source_frame = read_static_image(get_test_example_file('source.jpg'))
	bounding_box = get_bounding_box()

	for face_aligner_model in [ '2dfan4', 'hrffa', 'peppa_wutz', 'many' ]:
		state_manager.set_item('face_aligner_model', face_aligner_model)
		face_landmark_68, face_landmark_score_68 = detect_face_landmark(source_frame, bounding_box, 0)

		assert face_landmark_68.shape == (68, 2)
		assert face_landmark_score_68 > 0.9
		assert (face_landmark_68.min(axis = 0) > bounding_box[:2] - 10).tolist() == [ True, True ]
		assert (face_landmark_68.max(axis = 0) < bounding_box[2:] + 10).tolist() == [ True, True ]


def test_detect_with_2dfan4() -> None:
	state_manager.set_item('face_aligner_model', '2dfan4')
	face_landmark_68, face_landmark_score_68 = detect_with_2dfan4(read_static_image(get_test_example_file('source.jpg')), get_bounding_box(), 0)

	assert face_landmark_68.shape == (68, 2)
	assert face_landmark_score_68 > 0.9


def test_detect_with_hrffa() -> None:
	state_manager.set_item('face_aligner_model', 'hrffa')
	face_landmark_68, face_landmark_score_68 = detect_with_hrffa(read_static_image(get_test_example_file('source.jpg')), get_bounding_box())

	assert face_landmark_68.shape == (68, 2)
	assert face_landmark_score_68 == 1.0


def test_detect_with_peppa_wutz() -> None:
	state_manager.set_item('face_aligner_model', 'peppa_wutz')
	face_landmark_68, face_landmark_score_68 = detect_with_peppa_wutz(read_static_image(get_test_example_file('source.jpg')), get_bounding_box(), 0)

	assert face_landmark_68.shape == (68, 2)
	assert face_landmark_score_68 > 0.9


def test_conditional_optimize_contrast() -> None:
	vision_frame = numpy.full((64, 64, 3), 200, numpy.uint8)

	assert numpy.array_equal(conditional_optimize_contrast(vision_frame.copy()), vision_frame) is True

	vision_frame = numpy.zeros((64, 64, 3), numpy.uint8)
	vision_frame[:, 32:] = 20
	optimize_vision_frame = conditional_optimize_contrast(vision_frame.copy())

	assert optimize_vision_frame[0, 0].tolist() == [ 11, 11, 11 ]
	assert optimize_vision_frame[0, 40].tolist() == [ 26, 26, 26 ]


def test_estimate_face_landmark_68_5() -> None:
	state_manager.set_item('face_aligner_model', '2dfan4')
	source_frame = read_static_image(get_test_example_file('source.jpg'))
	bounding_boxes, _, face_landmarks_5 = detect_with_yolo_face(source_frame, '640x640')
	face_landmark_68_5 = estimate_face_landmark_68_5(face_landmarks_5[0])
	face_landmark_68, _ = detect_with_2dfan4(source_frame, bounding_boxes[0], 0)

	assert face_landmark_68_5.shape == (68, 2)
	assert numpy.linalg.norm(face_landmark_68_5 - face_landmark_68, axis = 1).mean() < 30
