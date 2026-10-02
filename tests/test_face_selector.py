from typing import List

import numpy
import pytest

from facefusion import face_aligner, face_classifier, face_detector, face_recognizer, face_store, inference_manager, state_manager, video_manager
from facefusion.download import conditional_download
from facefusion.face_selector import calculate_face_distance, compare_faces, filter_faces_by_age, filter_faces_by_gender, filter_faces_by_race, find_match_faces, get_bounding_box_area, get_bounding_box_left, get_bounding_box_top, get_face_detector_score, select_faces, sort_and_filter_faces, sort_faces_by_order
from facefusion.types import Age, BoundingBox, Embedding, Face, Gender, Race, Score
from facefusion.vision import read_static_image, read_static_video_frame
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	face_store.init()

	video_manager.init()

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
	state_manager.init_item('face_aligner_model', 'many')
	state_manager.init_item('face_aligner_score', 0.5)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_aligner.clear_inference_pool()
	face_recognizer.clear_inference_pool()

	face_store.clear()

	state_manager.set_item('face_tracker_score', 0.0)
	state_manager.set_item('face_selector_mode', 'many')
	state_manager.set_item('face_selector_order', None)
	state_manager.set_item('face_selector_gender', None)
	state_manager.set_item('face_selector_race', None)
	state_manager.set_item('face_selector_age_start', None)
	state_manager.set_item('face_selector_age_end', None)
	state_manager.set_item('reference_face_position', 0)
	state_manager.set_item('reference_face_distance', 0.3)


def create_face(bounding_box : BoundingBox, detector_score : Score, gender : Gender, age : Age, race : Race, embedding_norm : Embedding) -> Face:
	return Face(
		origin = 'detect',
		bounding_box = bounding_box,
		score_set =
		{
			'detector': detector_score,
			'aligner': 0.0
		},
		landmark_set = {},
		angle = 0,
		embedding = embedding_norm,
		embedding_norm = embedding_norm,
		age = age,
		gender = gender,
		race = race
	)


def create_faces() -> List[Face]:
	return\
	[
		create_face(numpy.array([ 0, 0, 10, 10 ]), 0.6, 'female', range(20, 29), 'white', numpy.array([ 1.0, 0.0 ])),
		create_face(numpy.array([ 50, 10, 80, 40 ]), 0.9, 'male', range(30, 39), 'black', numpy.array([ 0.0, 1.0 ])),
		create_face(numpy.array([ 20, 60, 25, 65 ]), 0.7, 'female', range(60, 69), 'asian', numpy.array([ -1.0, 0.0 ])),
		create_face(numpy.array([ 30, 30, 60, 50 ]), 0.5, 'male', range(10, 19), 'white', numpy.array([ 0.6, 0.8 ]))
	]


def test_select_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	target_vision_frame = read_static_video_frame(get_test_example_file('target-240p.mp4'), 0)
	multi_face_vision_frame = numpy.hstack([ target_vision_frame, target_vision_frame ])
	empty_vision_frame = numpy.zeros_like(target_vision_frame)

	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ empty_vision_frame, source_vision_frame, empty_vision_frame ])) == 1
	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ source_vision_frame, empty_vision_frame, source_vision_frame ])) == 0
	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ multi_face_vision_frame, multi_face_vision_frame, multi_face_vision_frame ])) == 2

	state_manager.set_item('face_tracker_score', 0.3)

	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ multi_face_vision_frame, multi_face_vision_frame, multi_face_vision_frame ])) == 2
	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ source_vision_frame, empty_vision_frame, source_vision_frame ])) == 1

	state_manager.set_item('face_selector_mode', 'one')

	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ multi_face_vision_frame, multi_face_vision_frame, multi_face_vision_frame ])) == 1
	assert select_faces(source_vision_frame, [ source_vision_frame ], [ empty_vision_frame, empty_vision_frame, empty_vision_frame ]) == []

	state_manager.set_item('face_selector_mode', 'reference')

	assert len(select_faces(source_vision_frame, [ source_vision_frame ], [ source_vision_frame, source_vision_frame, source_vision_frame ])) == 1
	assert len(select_faces(target_vision_frame, [ source_vision_frame ], [ multi_face_vision_frame, multi_face_vision_frame, multi_face_vision_frame ])) == 2
	assert select_faces(target_vision_frame, [ source_vision_frame ], [ source_vision_frame, source_vision_frame, source_vision_frame ]) == []
	assert select_faces(empty_vision_frame, [ source_vision_frame ], [ source_vision_frame, source_vision_frame, source_vision_frame ]) == []

	state_manager.set_item('face_selector_mode', 'invalid')

	assert select_faces(source_vision_frame, [ source_vision_frame ], [ source_vision_frame, source_vision_frame, source_vision_frame ]) == []


def test_find_match_faces() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert find_match_faces([ face_a ], [ face_a, face_b, face_c, face_d ], 0.3) == [ face_a, face_d ]
	assert find_match_faces([ face_a ], [ face_a, face_b, face_c, face_d ], 0.6) == [ face_a, face_b, face_d ]
	assert find_match_faces([ face_a, face_b ], [ face_a, face_b, face_c ], 0.1) == [ face_a, face_b ]
	assert find_match_faces([ None ], [ face_a, face_b, face_c, face_d ], 0.3) == []
	assert find_match_faces([ face_a ], [], 0.3) == []


def test_compare_faces() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert compare_faces(face_a, face_a, 0.1) is True
	assert compare_faces(face_a, face_d, 0.3) is True
	assert compare_faces(face_a, face_d, 0.2) is False
	assert compare_faces(face_a, face_b, 0.5) is False
	assert compare_faces(face_a, face_b, 0.51) is True
	assert compare_faces(face_a, face_c, 1.0) is False


def test_calculate_face_distance() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert calculate_face_distance(face_a, face_a) == 0.0
	assert calculate_face_distance(face_a, face_b) == 1.0
	assert calculate_face_distance(face_a, face_c) == 2.0
	assert calculate_face_distance(face_d, face_a) == 0.4


def test_sort_and_filter_faces() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert sort_and_filter_faces([ face_a ], []) == []
	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_b, face_c, face_d ]

	state_manager.set_item('face_selector_order', 'left-right')

	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_c, face_d, face_b ]

	state_manager.set_item('face_selector_gender', 'female')

	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_c ]

	state_manager.set_item('face_selector_gender', 'auto')

	assert sort_and_filter_faces([ face_c, face_b ], [ face_a, face_b, face_c, face_d ]) == [ face_d, face_b ]
	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_c, face_d, face_b ]

	state_manager.set_item('face_selector_gender', None)
	state_manager.set_item('face_selector_race', 'white')

	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_d ]

	state_manager.set_item('face_selector_race', 'auto')

	assert sort_and_filter_faces([ face_c, face_b ], [ face_a, face_b, face_c, face_d ]) == [ face_b ]
	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_a, face_c, face_d, face_b ]

	state_manager.set_item('face_selector_race', None)
	state_manager.set_item('face_selector_order', 'large-small')
	state_manager.set_item('face_selector_age_start', 25)
	state_manager.set_item('face_selector_age_end', 35)

	assert sort_and_filter_faces([], [ face_a, face_b, face_c, face_d ]) == [ face_b, face_a ]


def test_sort_faces_by_order() -> None:
	face_a, face_b, face_c, face_d = create_faces()
	faces = [ face_a, face_b, face_c, face_d ]

	assert sort_faces_by_order(faces, 'left-right') == [ face_a, face_c, face_d, face_b ]
	assert sort_faces_by_order(faces, 'right-left') == [ face_b, face_d, face_c, face_a ]
	assert sort_faces_by_order(faces, 'top-bottom') == [ face_a, face_b, face_d, face_c ]
	assert sort_faces_by_order(faces, 'bottom-top') == [ face_c, face_d, face_b, face_a ]
	assert sort_faces_by_order(faces, 'small-large') == [ face_c, face_a, face_d, face_b ]
	assert sort_faces_by_order(faces, 'large-small') == [ face_b, face_d, face_a, face_c ]
	assert sort_faces_by_order(faces, 'best-worst') == [ face_b, face_c, face_a, face_d ]
	assert sort_faces_by_order(faces, 'worst-best') == [ face_d, face_a, face_c, face_b ]
	assert sort_faces_by_order(faces, 'invalid') == [ face_a, face_b, face_c, face_d ]


def test_get_bounding_box_left() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert get_bounding_box_left(face_b) == 50


def test_get_bounding_box_top() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert get_bounding_box_top(face_b) == 10


def test_get_bounding_box_area() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert get_bounding_box_area(face_b) == 900
	assert get_bounding_box_area(face_d) == 600


def test_get_face_detector_score() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert get_face_detector_score(face_b) == 0.9


def test_filter_faces_by_gender() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_gender([ face_a, face_b, face_c, face_d ], 'female') == [ face_a, face_c ]
	assert filter_faces_by_gender([ face_a, face_b, face_c, face_d ], 'male') == [ face_b, face_d ]
	assert filter_faces_by_gender([ face_a, face_c ], 'male') == []


def test_filter_faces_by_age() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 25, 35) == [ face_a, face_b ]
	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 0, 100) == [ face_a, face_b, face_c, face_d ]
	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 0, 10) == []
	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 0, 11) == [ face_d ]
	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 68, 100) == [ face_c ]
	assert filter_faces_by_age([ face_a, face_b, face_c, face_d ], 69, 100) == []


def test_filter_faces_by_race() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_race([ face_a, face_b, face_c, face_d ], 'white') == [ face_a, face_d ]
	assert filter_faces_by_race([ face_a, face_b, face_c, face_d ], 'asian') == [ face_c ]
	assert filter_faces_by_race([ face_a, face_b, face_c, face_d ], 'indian') == []
