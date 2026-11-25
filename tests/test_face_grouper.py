from typing import List

import numpy

from facefusion.face_grouper import calculate_face_distances, create_face_pointer_group_set, merge_group_distances, sort_face_pointer_group
from facefusion.types import Face, FacePointer


def create_faces() -> List[Face]:
	faces = []

	for embedding in [ [ 1.0, 0.0 ], [ 0.0, 1.0 ], [ -1.0, 0.0 ], [ 0.6, 0.8 ] ]:
		faces.append(Face(
			origin = 'detect',
			bounding_box = numpy.array([ 0, 0, 10, 10 ]),
			score_set =
			{
				'detector': 0.5,
				'aligner': 0.0
			},
			landmark_set = {},
			angle = 0,
			embedding = numpy.array(embedding),
			embedding_norm = numpy.array(embedding),
			age = range(20, 29),
			gender = 'female',
			race = 'white'
		))

	return faces


def create_face_pointers() -> List[FacePointer]:
	face_pointers : List[FacePointer] = []

	for frame_index in range(4):
		face_pointers.append(
		{
			'frame_index': frame_index,
			'face_position': 0
		})

	return face_pointers


def test_create_face_pointer_group_set() -> None:
	faces = create_faces()
	face_pointers = create_face_pointers()

	assert create_face_pointer_group_set([], [], 0.4) == {}
	assert create_face_pointer_group_set(faces, face_pointers, 0.05) ==\
	{
		'0': [ face_pointers[0] ],
		'1': [ face_pointers[1] ],
		'2': [ face_pointers[2] ],
		'3': [ face_pointers[3] ]
	}
	assert create_face_pointer_group_set(faces, face_pointers, 0.4) ==\
	{
		'0': [ face_pointers[3], face_pointers[1], face_pointers[0] ],
		'1': [ face_pointers[2] ]
	}
	assert create_face_pointer_group_set([ faces[2], faces[0], faces[1], faces[3] ], [ face_pointers[2], face_pointers[0], face_pointers[1], face_pointers[3] ], 0.4) ==\
	{
		'0': [ face_pointers[3], face_pointers[1], face_pointers[0] ],
		'1': [ face_pointers[2] ]
	}
	assert create_face_pointer_group_set(faces, face_pointers, 0.8) ==\
	{
		'0': [ face_pointers[1], face_pointers[3], face_pointers[0], face_pointers[2] ]
	}


def test_sort_face_pointer_group() -> None:
	faces = create_faces()
	face_pointers = create_face_pointers()

	assert sort_face_pointer_group([ faces[0], faces[1], faces[3] ], [ face_pointers[0], face_pointers[1], face_pointers[3] ]) == [ face_pointers[3], face_pointers[1], face_pointers[0] ]
	assert sort_face_pointer_group([ faces[2] ], [ face_pointers[2] ]) == [ face_pointers[2] ]


def test_calculate_face_distances() -> None:
	assert calculate_face_distances(create_faces()).round(2).tolist() == [ [ 0.0, 0.5, 1.0, 0.2 ], [ 0.5, 0.0, 0.5, 0.1 ], [ 1.0, 0.5, 0.0, 0.8 ], [ 0.2, 0.1, 0.8, 0.0 ] ]


def test_merge_group_distances() -> None:
	group_distances = calculate_face_distances(create_faces())
	numpy.fill_diagonal(group_distances, numpy.inf)

	assert merge_group_distances(group_distances, 1, 1, 3, 1).round(2).tolist() == [ [ numpy.inf, 0.35, 1.0 ], [ 0.35, numpy.inf, 0.65 ], [ 1.0, 0.65, numpy.inf ] ]

	group_distances = calculate_face_distances(create_faces())
	numpy.fill_diagonal(group_distances, numpy.inf)

	assert merge_group_distances(group_distances, 1, 2, 3, 1).round(2).tolist() == [ [ numpy.inf, 0.4, 1.0 ], [ 0.4, numpy.inf, 0.6 ], [ 1.0, 0.6, numpy.inf ] ]
