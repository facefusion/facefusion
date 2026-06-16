from functools import partial
from typing import Dict, List
from unittest.mock import patch

import numpy

from facefusion.face_bridger import propagate_reference_face
from facefusion.types import Face


def create_face(bounding_box : List[int], embedding : List[float]) -> Face:
	embedding_norm = numpy.array(embedding, dtype = numpy.float32)
	embedding_norm = embedding_norm / numpy.linalg.norm(embedding_norm)
	return Face(bounding_box = numpy.array(bounding_box, dtype = numpy.float32), score_set = {}, landmark_set = {}, angle = 0, embedding = embedding_norm, embedding_norm = embedding_norm, age = None, gender = None, race = None)


def get_window_faces(window : Dict[int, List[Face]], vision_frames : List[int]) -> List[Face]:
	return window.get(vision_frames[0])


def test_propagate_reference_face_recovers_subject() -> None:
	reference_face = create_face([ 0, 0, 10, 10 ], [ 1, 0, 0, 0 ])
	subject_face = create_face([ 0, 0, 10, 10 ], [ 0.9, 0.3, 0, 0 ])
	subject_far_face = create_face([ 0, 0, 10, 10 ], [ -0.1, 0.5, 0.86, 0 ])
	coactor_face = create_face([ 100, 100, 110, 110 ], [ 0.2, 0.95, 0, 0 ])

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ subject_face ], 1: [ subject_face ], 2: [ subject_face ] })):
		result = propagate_reference_face(reference_face, [ reference_face ], [ 0, 1, 2 ])
		assert len(result) == 1
		assert result[0] is subject_face

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ subject_face, coactor_face ], 1: [ subject_face, coactor_face ], 2: [ subject_face, coactor_face ] })):
		result = propagate_reference_face(reference_face, [ reference_face, coactor_face ], [ 0, 1, 2 ])
		assert len(result) == 1
		assert result[0] is subject_face

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ subject_face ], 1: [ subject_far_face ], 2: [ subject_face ] })):
		result = propagate_reference_face(reference_face, [ reference_face ], [ 0, 1, 2 ])
		assert len(result) == 1
		assert result[0] is subject_far_face


def test_propagate_reference_face_rejects_non_subject() -> None:
	reference_face = create_face([ 0, 0, 10, 10 ], [ 1, 0, 0, 0 ])
	subject_face = create_face([ 0, 0, 10, 10 ], [ 0.9, 0.3, 0, 0 ])
	coactor_face = create_face([ 100, 100, 110, 110 ], [ 0.2, 0.95, 0, 0 ])
	stranger_face = create_face([ 0, 0, 10, 10 ], [ -0.3, 0, 0.95, 0 ])
	ceiling_face = create_face([ 0, 0, 10, 10 ], [ 0, 1, 0, 0 ])

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ coactor_face ], 1: [ coactor_face ], 2: [ coactor_face ] })):
		assert propagate_reference_face(reference_face, [ reference_face, coactor_face ], [ 0, 1, 2 ]) == []

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ ceiling_face ], 1: [ ceiling_face ], 2: [ ceiling_face ] })):
		assert propagate_reference_face(reference_face, [ reference_face ], [ 0, 1, 2 ]) == []

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ stranger_face ], 1: [ stranger_face ], 2: [ stranger_face ] })):
		assert propagate_reference_face(reference_face, [ reference_face ], [ 0, 1, 2 ]) == []

	with patch('facefusion.face_bridger.get_static_faces', side_effect = partial(get_window_faces, { 0: [ subject_face ], 1: [], 2: [ subject_face ] })):
		assert propagate_reference_face(reference_face, [ reference_face ], [ 0, 1, 2 ]) == []
