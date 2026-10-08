import pytest

from facefusion import face_aligner, face_classifier, face_detector, face_masker, face_recognizer, face_store, inference_manager, state_manager
from facefusion.download import conditional_download
from facefusion.face_creator import get_one_face, get_static_faces
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.vision import read_static_image
from tests.assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	face_store.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_aligner_model', '2dfan4')
	state_manager.init_item('face_aligner_score', 0.5)
	state_manager.init_item('face_occluder_model', 'xseg_1')
	state_manager.init_item('face_parser_model', 'bisenet_resnet_34')

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()
	face_masker.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_masker.clear_inference_pool()


def test_create_box_mask() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	source_face = get_one_face(get_static_faces([ source_vision_frame ]))
	crop_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'arcface_128', (256, 256))

	assert create_box_mask(crop_vision_frame, 0.3, (0, 0, 0, 0)).sum() == pytest.approx(47546.383, rel = 1e-3)


def test_create_occlusion_mask() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	source_face = get_one_face(get_static_faces([ source_vision_frame ]))
	crop_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'arcface_128', (256, 256))

	assert create_occlusion_mask(crop_vision_frame).sum() == pytest.approx(25111.992, rel = 1e-3)

	state_manager.set_item('face_occluder_model', 'many')

	assert create_occlusion_mask(crop_vision_frame).sum() == pytest.approx(24492.172, rel = 1e-3)


def test_create_area_mask() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	source_face = get_one_face(get_static_faces([ source_vision_frame ]))

	assert create_area_mask(source_vision_frame, source_face.landmark_set.get('68'), [ 'mouth' ]).sum() == pytest.approx(15442.252, rel = 1e-3)


def test_create_region_mask() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	source_face = get_one_face(get_static_faces([ source_vision_frame ]))
	crop_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'arcface_128', (256, 256))

	assert create_region_mask(crop_vision_frame, [ 'skin' ]).sum() == pytest.approx(17950.344, rel = 1e-3)
