from typing import List

import numpy
import pytest

from facefusion import state_manager
from facefusion.face_selector import calculate_face_distance, compare_faces, filter_faces_by_age, filter_faces_by_gender, filter_faces_by_race, find_match_faces, sort_and_filter_faces, sort_faces_by_order
from facefusion.types import Face


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()


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
