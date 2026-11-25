from typing import List

import numpy

from facefusion.face_grouper import calculate_face_distances, group_faces, merge_group_distances
from facefusion.types import Face, FacePointer


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


def create_face_pointers() -> List[FacePointer]:
	return\
	[
		{
			'frame_index': 0,
			'face_position': 0
		},
		{
			'frame_index': 100,
			'face_position': 1
		},
		{
			'frame_index': 200,
			'face_position': 2
		},
		{
			'frame_index': 300,
			'face_position': 3
		}
	]


def test_create_face_pointer_set() -> None:
	faces = create_faces()
	face_pointers = create_face_pointers()

	assert group_faces([], [], 0.4) == {}
	assert group_faces(faces, face_pointers, 0.05) == \
		   {
		0: [ face_pointers[0] ],
		1: [ face_pointers[1] ],
		2: [ face_pointers[2] ],
		3: [ face_pointers[3] ]
	}
	assert group_faces(faces, face_pointers, 0.4) == \
		   {
		0: [ face_pointers[0], face_pointers[1], face_pointers[3] ],
		2: [ face_pointers[2] ]
	}
	assert group_faces([faces[2], faces[0], faces[1], faces[3]], [face_pointers[2], face_pointers[0], face_pointers[1], face_pointers[3]], 0.4) == \
		   {
		0: [ face_pointers[2] ],
		1: [ face_pointers[0], face_pointers[1], face_pointers[3] ]
	}
	assert group_faces(faces, face_pointers, 0.8) == \
		   {
		0: [ face_pointers[0], face_pointers[1], face_pointers[3], face_pointers[2] ]
	}


def test_calculate_face_distances() -> None:
	assert calculate_face_distances(create_faces()).round(2).tolist() == [ [ 0.0, 0.5, 1.0, 0.2 ], [ 0.5, 0.0, 0.5, 0.1 ], [ 1.0, 0.5, 0.0, 0.8 ], [ 0.2, 0.1, 0.8, 0.0 ] ]


def test_merge_group_distances() -> None:
	group_distances = calculate_face_distances(create_faces())
	numpy.fill_diagonal(group_distances, numpy.inf)

	assert merge_group_distances(group_distances, 1, 1, 3, 1).round(2).tolist() == [ [ numpy.inf, 0.35, 1.0 ], [ 0.35, numpy.inf, 0.65 ], [ 1.0, 0.65, numpy.inf ] ]

	group_distances = calculate_face_distances(create_faces())
	numpy.fill_diagonal(group_distances, numpy.inf)

	assert merge_group_distances(group_distances, 1, 2, 3, 1).round(2).tolist() == [ [ numpy.inf, 0.4, 1.0 ], [ 0.4, numpy.inf, 0.6 ], [ 1.0, 0.6, numpy.inf ] ]
