import numpy

from facefusion.face_creator import interpolate_array, interpolate_face
from .helper import create_face_from_bounding_box


def test_interpolate_face() -> None:
	face_before = create_face_from_bounding_box([0, 0, 10, 10])
	face_after = create_face_from_bounding_box([80, 80, 90, 90])

	assert interpolate_face(face_before, face_after, 0.5).bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert interpolate_face(face_before, face_after, 0.5).angle == 0
	assert interpolate_face(face_before, face_after, 0.5).embedding is face_after.embedding
	assert interpolate_face(face_before, face_after, 0.25).embedding is face_before.embedding


def test_interpolate_array() -> None:
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 0.5).tolist() == [ 5.0, 10.0 ]
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 0.0).tolist() == [ 0.0, 0.0 ]
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 1.0).tolist() == [ 10.0, 20.0 ]
