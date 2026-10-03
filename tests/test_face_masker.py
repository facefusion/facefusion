import numpy
import pytest

from facefusion import face_aligner, face_classifier, face_detector, face_masker, face_recognizer, face_store, inference_manager, state_manager
from facefusion.download import conditional_download
from facefusion.face_creator import get_one_face, get_static_faces
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.face_masker import collect_model_downloads, create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.types import FaceLandmark68, VisionFrame
from facefusion.vision import read_static_image
from .assert_helper import get_test_example_file, get_test_examples_directory


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
	state_manager.init_item('face_aligner_model', 'many')
	state_manager.init_item('face_aligner_score', 0.5)
	state_manager.init_item('face_occluder_model', 'many')
	state_manager.init_item('face_parser_model', 'bisenet_resnet_34')

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()
	face_masker.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_aligner.clear_inference_pool()
	face_recognizer.clear_inference_pool()
	face_masker.clear_inference_pool()

	face_store.clear()

	state_manager.set_item('face_occluder_model', 'many')
	state_manager.set_item('face_parser_model', 'bisenet_resnet_34')


def get_crop_vision_frame() -> VisionFrame:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	source_face = get_one_face(get_static_faces([ source_vision_frame ]))
	crop_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'arcface_128', (256, 256))
	return crop_vision_frame


def create_face_landmark_68() -> FaceLandmark68:
	face_landmark_68 = numpy.zeros((68, 2))

	for index, point_x in enumerate(numpy.linspace(50, 200, 10)):
		face_landmark_68[17 + index] = [ point_x, 20 ]
	for index, point_x in enumerate(numpy.linspace(60, 190, 5)):
		face_landmark_68[31 + index] = [ point_x, 100 ]
	for index, point_x in enumerate(numpy.linspace(60, 190, 9)):
		face_landmark_68[4 + index] = [ point_x, 200 ]
	for index in range(48, 68):
		face_landmark_68[index] = [ [ 100, 140 ], [ 150, 140 ], [ 150, 170 ], [ 100, 170 ] ][index % 4]

	face_landmark_68[0] = [ 50, 20 ]
	face_landmark_68[1] = [ 50, 60 ]
	face_landmark_68[2] = [ 50, 100 ]
	face_landmark_68[3] = [ 50, 110 ]
	face_landmark_68[13] = [ 200, 110 ]
	face_landmark_68[14] = [ 200, 100 ]
	face_landmark_68[15] = [ 200, 60 ]
	face_landmark_68[16] = [ 200, 20 ]
	return face_landmark_68


def test_collect_model_downloads() -> None:
	model_hash_set, model_source_set = collect_model_downloads()

	assert list(model_hash_set.keys()) == [ 'xseg_1', 'xseg_2', 'xseg_3', 'bisenet_resnet_34' ]
	assert list(model_source_set.keys()) == [ 'xseg_1', 'xseg_2', 'xseg_3', 'bisenet_resnet_34' ]

	state_manager.set_item('face_occluder_model', 'xseg_2')
	state_manager.set_item('face_parser_model', 'bisenet_resnet_18')
	model_hash_set, model_source_set = collect_model_downloads()

	assert list(model_hash_set.keys()) == [ 'xseg_2', 'bisenet_resnet_18' ]
	assert model_source_set.get('xseg_2').get('path').endswith('xseg_2.onnx') is True
	assert model_source_set.get('bisenet_resnet_18').get('path').endswith('bisenet_resnet_18.onnx') is True


def test_create_box_mask() -> None:
	crop_vision_frame = numpy.zeros((100, 100, 3), numpy.uint8)
	box_mask = create_box_mask(crop_vision_frame, 0.0, (0, 0, 0, 0))

	assert box_mask.shape == (100, 100)
	assert box_mask.dtype == numpy.float32
	assert box_mask.sum() == 98 * 98
	assert box_mask[0].sum() == 0
	assert box_mask[-1].sum() == 0
	assert box_mask[:, 0].sum() == 0
	assert box_mask[:, -1].sum() == 0

	box_mask = create_box_mask(crop_vision_frame, 0.0, (10, 20, 30, 40))

	assert box_mask.sum() == 60 * 40
	assert box_mask[10:70, 40:80].min() == 1.0
	assert box_mask[9, 40:80].max() == 0.0
	assert box_mask[70, 40:80].max() == 0.0
	assert box_mask[10:70, 39].max() == 0.0
	assert box_mask[10:70, 80].max() == 0.0

	box_mask = create_box_mask(crop_vision_frame, 0.3, (0, 0, 0, 0))

	assert box_mask[50, 50].round(2) == 1.0
	assert box_mask[0, 0].round(2) == 0.01
	assert box_mask[50, 0] < box_mask[50, 10]
	assert box_mask[50, 10] < box_mask[50, 20]


def test_create_occlusion_mask() -> None:
	crop_vision_frame = get_crop_vision_frame()
	occlusion_mask = create_occlusion_mask(crop_vision_frame)

	assert occlusion_mask.shape == (256, 256)
	assert occlusion_mask.dtype == numpy.float32
	assert occlusion_mask.min() == 0.0
	assert occlusion_mask.max().round(2) == 1.0
	assert occlusion_mask[128, 128].round(2) == 1.0
	assert occlusion_mask[0, 0] == 0.0
	assert occlusion_mask.mean().round(3) == 0.374

	state_manager.set_item('face_occluder_model', 'xseg_1')
	occlusion_mask_xseg_1 = create_occlusion_mask(crop_vision_frame)

	assert numpy.max(occlusion_mask - occlusion_mask_xseg_1) < 0.001
	assert occlusion_mask_xseg_1.mean().round(3) == 0.383
	assert numpy.mean(create_occlusion_mask(numpy.zeros((256, 256, 3), numpy.uint8)) > 0.5) < 0.2


def test_create_area_mask() -> None:
	crop_vision_frame = numpy.zeros((256, 256, 3), numpy.uint8)
	face_landmark_68 = create_face_landmark_68()
	upper_face_mask = create_area_mask(crop_vision_frame, face_landmark_68, [ 'upper-face' ])
	lower_face_mask = create_area_mask(crop_vision_frame, face_landmark_68, [ 'lower-face' ])
	mouth_mask = create_area_mask(crop_vision_frame, face_landmark_68, [ 'mouth' ])

	assert upper_face_mask.shape == (256, 256)
	assert upper_face_mask[60, 125].round(2) == 1.0
	assert upper_face_mask[150, 125].round(2) == 0.0
	assert lower_face_mask[60, 125].round(2) == 0.0
	assert lower_face_mask[150, 125].round(2) == 1.0
	assert mouth_mask[155, 125].round(2) == 1.0
	assert mouth_mask[60, 125].round(2) == 0.0
	assert mouth_mask[155, 90].round(2) == 0.0
	assert numpy.array_equal(create_area_mask(crop_vision_frame, face_landmark_68, [ 'invalid', 'mouth' ]), mouth_mask) is True #type:ignore[list-item]

	face_mask = create_area_mask(crop_vision_frame, face_landmark_68, [ 'upper-face', 'lower-face' ])

	assert face_mask[60, 125].round(2) == 1.0
	assert face_mask[150, 125].round(2) == 1.0
	assert face_mask[10, 125].round(2) == 0.0
	assert face_mask[150, 20].round(2) == 0.0


def test_create_region_mask() -> None:
	crop_vision_frame = get_crop_vision_frame()
	skin_mask = create_region_mask(crop_vision_frame, [ 'skin' ])
	nose_mask = create_region_mask(crop_vision_frame, [ 'nose' ])
	skin_nose_mask = create_region_mask(crop_vision_frame, [ 'skin', 'nose' ])

	assert skin_mask.shape == (256, 256)
	assert skin_mask.min() == 0.0
	assert skin_mask.max().round(2) == 1.0
	assert skin_mask[0, 0] == 0.0
	assert skin_mask.mean().round(3) == 0.274
	assert nose_mask.mean().round(3) == 0.016
	assert skin_nose_mask.mean().round(3) == 0.31
	assert numpy.min(skin_nose_mask - skin_mask) > -0.001
	assert numpy.min(skin_nose_mask - nose_mask) > -0.001
	assert numpy.mean(create_region_mask(crop_vision_frame, [ 'glasses' ]) > 0.5) == 0.0
