from typing import List

import cv2
import numpy
import pytest

from facefusion import face_aligner, face_classifier, face_detector, face_recognizer, face_store, ffmpeg, ffmpeg_builder, inference_manager, process_manager, state_manager
from facefusion.common_helper import get_first, get_last
from facefusion.download import conditional_download
from facefusion.face_creator import get_static_faces
from facefusion.face_selector import calculate_face_distance, collect_source_faces, compare_faces, decode_face_selector_map, decode_face_selector_maps, filter_faces_by_age, filter_faces_by_gender, filter_faces_by_race, find_match_faces, select_faces, sort_and_filter_faces, sort_faces_by_order
from facefusion.types import Face
from facefusion.vision import read_static_image
from tests.assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	face_store.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
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
	).wait()

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'many')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_aligner_model', 'many')
	state_manager.init_item('face_aligner_score', 0.5)
	state_manager.init_item('face_tracker_score', 0)
	state_manager.init_item('reference_face_distance', 0.3)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()


def create_faces() -> List[Face]:
	landmark_generator = numpy.random.default_rng(0)

	return\
	[
		Face(
			origin = 'detect',
			bounding_box = numpy.array([ 0, 0, 10, 10 ]),
			score_set =
			{
				'detector': 0.6,
				'aligner': 0.0
			},
			landmark_set =
			{
				'5': landmark_generator.random((5, 2)),
				'5/68': landmark_generator.random((5, 2)),
				'68': landmark_generator.random((68, 2))
			},
			angle = 0,
			embedding = numpy.array([ 1.0, 0.0 ]),
			embedding_norm = numpy.array([ 1.0, 0.0 ]),
			age = range(20, 29),
			gender = 'female',
			race = 'white'
		),
		Face(
			origin = 'detect',
			bounding_box = numpy.array([ 50, 10, 80, 40 ]),
			score_set =
			{
				'detector': 0.9,
				'aligner': 0.0
			},
			landmark_set =
			{
				'5': landmark_generator.random((5, 2)),
				'5/68': landmark_generator.random((5, 2)),
				'68': landmark_generator.random((68, 2))
			},
			angle = 0,
			embedding = numpy.array([ 0.0, 1.0 ]),
			embedding_norm = numpy.array([ 0.0, 1.0 ]),
			age = range(30, 39),
			gender = 'male',
			race = 'black'
		),
		Face(
			origin = 'detect',
			bounding_box = numpy.array([ 20, 60, 25, 65 ]),
			score_set =
			{
				'detector': 0.7,
				'aligner': 0.0
			},
			landmark_set =
			{
				'5': landmark_generator.random((5, 2)),
				'5/68': landmark_generator.random((5, 2)),
				'68': landmark_generator.random((68, 2))
			},
			angle = 0,
			embedding = numpy.array([ -1.0, 0.0 ]),
			embedding_norm = numpy.array([ -1.0, 0.0 ]),
			age = range(60, 69),
			gender = 'female',
			race = 'asian'
		),
		Face(
			origin = 'detect',
			bounding_box = numpy.array([ 30, 30, 50, 50 ]),
			score_set =
			{
				'detector': 0.5,
				'aligner': 0.0
			},
			landmark_set =
			{
				'5': landmark_generator.random((5, 2)),
				'5/68': landmark_generator.random((5, 2)),
				'68': landmark_generator.random((68, 2))
			},
			angle = 0,
			embedding = numpy.array([ 0.6, 0.8 ]),
			embedding_norm = numpy.array([ 0.6, 0.8 ]),
			age = range(10, 19),
			gender = 'male',
			race = 'white'
		)
	]


def test_select_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	target_vision_frame = read_static_image(get_test_example_file('target-240p.jpg'))
	reference_vision_frame = numpy.hstack([ cv2.resize(source_vision_frame, (226, 226)), target_vision_frame ])

	state_manager.set_item('face_selector_mode', 'many')
	state_manager.set_item('face_selector_maps', [ 'invalid' ])

	source_faces, target_faces = select_faces([], [ source_vision_frame ], [ source_vision_frame ])

	assert len(source_faces) == 1
	assert len(target_faces) == 1

	state_manager.set_item('face_selector_mode', 'reference')
	state_manager.set_item('face_selector_maps', [ '0:0 to 0:0', '1:1 to 1:1' ])

	source_faces, target_faces = select_faces([ source_vision_frame, reference_vision_frame ], [ source_vision_frame, reference_vision_frame ], [ reference_vision_frame ])

	assert compare_faces(get_first(source_faces), get_first(get_static_faces([ source_vision_frame ])), 0.3) is True
	assert compare_faces(get_last(source_faces), get_first(get_static_faces([ target_vision_frame ])), 0.3) is True
	assert compare_faces(get_first(target_faces), get_first(get_static_faces([ source_vision_frame ])), 0.3) is True
	assert compare_faces(get_last(target_faces), get_first(get_static_faces([ target_vision_frame ])), 0.3) is True

	state_manager.set_item('face_selector_maps', [ '1:1 to 0:0', '0:0 to 1:1' ])

	source_faces, target_faces = select_faces([ source_vision_frame, reference_vision_frame ], [ source_vision_frame, reference_vision_frame ], [ reference_vision_frame ])

	assert compare_faces(get_first(source_faces), get_first(get_static_faces([ target_vision_frame ])), 0.3) is True
	assert compare_faces(get_last(source_faces), get_first(get_static_faces([ source_vision_frame ])), 0.3) is True
	assert compare_faces(get_first(target_faces), get_first(get_static_faces([ source_vision_frame ])), 0.3) is True
	assert compare_faces(get_last(target_faces), get_first(get_static_faces([ target_vision_frame ])), 0.3) is True

	state_manager.set_item('face_selector_maps', [ '0:0 to 0:0', '1:1 to 0:0' ])

	source_faces, target_faces = select_faces([ source_vision_frame, source_vision_frame ], [ source_vision_frame, reference_vision_frame ], [ reference_vision_frame ])

	assert len(source_faces) == 1
	assert len(target_faces) == 1
	assert compare_faces(get_first(source_faces), get_first(get_static_faces([ target_vision_frame ])), 0.3) is True
	assert compare_faces(get_first(target_faces), get_first(get_static_faces([ source_vision_frame ])), 0.3) is True

	state_manager.clear_item('face_selector_mode')
	state_manager.clear_item('face_selector_maps')


def test_decode_face_selector_maps() -> None:
	assert decode_face_selector_maps([ '0:0 1:0 to 120:1', '2:0' ]) == [ { 'source_faces': [ { 'frame_index': 0, 'face_position': 0 }, { 'frame_index': 1, 'face_position': 0 } ], 'reference_faces': [ { 'frame_index': 120, 'face_position': 1 } ] }, { 'source_faces': [ { 'frame_index': 2, 'face_position': 0 } ], 'reference_faces': [] } ]
	assert decode_face_selector_maps([ 'to 120:1', 'invalid' ]) == [ { 'source_faces': [], 'reference_faces': [ { 'frame_index': 120, 'face_position': 1 } ] } ]
	assert decode_face_selector_maps([]) == []
	assert decode_face_selector_maps(None) == []


def test_decode_face_selector_map() -> None:
	assert decode_face_selector_map('0:0 to 100:1 200:0') == { 'source_faces': [ { 'frame_index': 0, 'face_position': 0 } ], 'reference_faces': [ { 'frame_index': 100, 'face_position': 1 }, { 'frame_index': 200, 'face_position': 0 } ] }
	assert decode_face_selector_map('0:0 1 1,2 -1:0 0:0:0 to') == { 'source_faces': [ { 'frame_index': 0, 'face_position': 0 } ], 'reference_faces': [] }


def test_collect_source_faces() -> None:
	assert collect_source_faces(decode_face_selector_maps([ '0:0 to 120:1', '1:0 2:1 to 300:0' ])) == [ { 'frame_index': 0, 'face_position': 0 }, { 'frame_index': 1, 'face_position': 0 }, { 'frame_index': 2, 'face_position': 1 } ]
	assert collect_source_faces(decode_face_selector_maps([ 'to 0:0' ])) == []


def test_find_match_faces() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert find_match_faces([ face_a ], faces, 0.3) == [ face_a, face_d ]
	assert find_match_faces([ face_a ], faces, 0.6) == [ face_a, face_b, face_d ]
	assert find_match_faces([ face_a, face_b ], [ face_a, face_b, face_c ], 0.1) == [ face_a, face_b ]
	assert find_match_faces([ face_a ], [], 0.3) == []


def test_compare_faces() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert compare_faces(face_a, face_a, 0.1) is True
	assert compare_faces(face_a, face_d, 0.3) is True
	assert compare_faces(face_a, face_d, 0.2) is False
	assert compare_faces(face_a, face_b, 0.5) is False
	assert compare_faces(face_a, face_b, 0.6) is True
	assert compare_faces(face_a, face_c, 1.0) is False


def test_calculate_face_distance() -> None:
	face_a, face_b, face_c, face_d = create_faces()

	assert calculate_face_distance(face_a, face_a) == 0.0
	assert calculate_face_distance(face_a, face_b) == 1.0
	assert calculate_face_distance(face_a, face_c) == 2.0
	assert calculate_face_distance(face_d, face_a) == 0.4


def test_sort_and_filter_faces() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert sort_and_filter_faces([ face_a ], []) == []
	assert sort_and_filter_faces([], faces) == faces

	state_manager.set_item('face_selector_order', 'left-right')

	assert sort_and_filter_faces([], faces) == [ face_a, face_c, face_d, face_b ]

	state_manager.set_item('face_selector_gender', 'female')

	assert sort_and_filter_faces([], faces) == [ face_a, face_c ]

	state_manager.set_item('face_selector_gender', 'auto')

	assert sort_and_filter_faces([ face_c, face_b ], faces) == [ face_d, face_b ]
	assert sort_and_filter_faces([], faces) == [ face_a, face_c, face_d, face_b ]

	state_manager.clear_item('face_selector_gender')
	state_manager.set_item('face_selector_race', 'white')

	assert sort_and_filter_faces([], faces) == [ face_a, face_d ]

	state_manager.set_item('face_selector_race', 'auto')

	assert sort_and_filter_faces([ face_c, face_b ], faces) == [ face_b ]
	assert sort_and_filter_faces([], faces) == [ face_a, face_c, face_d, face_b ]

	state_manager.clear_item('face_selector_race')
	state_manager.set_item('face_selector_order', 'large-small')
	state_manager.set_item('face_selector_age_start', 25)
	state_manager.set_item('face_selector_age_end', 35)

	assert sort_and_filter_faces([], faces) == [ face_b, face_a ]


def test_sort_faces_by_order() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert sort_faces_by_order(faces, 'left-right') == [ face_a, face_c, face_d, face_b ]
	assert sort_faces_by_order(faces, 'right-left') == [ face_b, face_d, face_c, face_a ]
	assert sort_faces_by_order(faces, 'top-bottom') == [ face_a, face_b, face_d, face_c ]
	assert sort_faces_by_order(faces, 'bottom-top') == [ face_c, face_d, face_b, face_a ]
	assert sort_faces_by_order(faces, 'small-large') == [ face_c, face_a, face_d, face_b ]
	assert sort_faces_by_order(faces, 'large-small') == [ face_b, face_d, face_a, face_c ]
	assert sort_faces_by_order(faces, 'best-worst') == [ face_b, face_c, face_a, face_d ]
	assert sort_faces_by_order(faces, 'worst-best') == [ face_d, face_a, face_c, face_b ]
	assert sort_faces_by_order(faces, 'invalid') == faces #type:ignore[arg-type]


def test_filter_faces_by_gender() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_gender(faces, 'female') == [ face_a, face_c ]
	assert filter_faces_by_gender(faces, 'male') == [ face_b, face_d ]
	assert filter_faces_by_gender([ face_a, face_c ], 'male') == []


def test_filter_faces_by_age() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_age(faces, 25, 35) == [ face_a, face_b ]
	assert filter_faces_by_age(faces, 0, 100) == faces
	assert filter_faces_by_age(faces, 0, 10) == []
	assert filter_faces_by_age(faces, 0, 11) == [ face_d ]
	assert filter_faces_by_age(faces, 68, 100) == [ face_c ]
	assert filter_faces_by_age(faces, 69, 100) == []


def test_filter_faces_by_race() -> None:
	faces = face_a, face_b, face_c, face_d = create_faces()

	assert filter_faces_by_race(faces, 'white') == [ face_a, face_d ]
	assert filter_faces_by_race(faces, 'asian') == [ face_c ]
	assert filter_faces_by_race(faces, 'indian') == []
