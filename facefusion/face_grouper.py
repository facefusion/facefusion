from typing import List

import numpy

from facefusion.face_selector import calculate_face_distance
from facefusion.types import Distance, DistanceMatrix, Face, FacePointer, FacePointerSet


def group_faces(faces : List[Face], face_pointers : List[FacePointer], face_distance : Distance) -> FacePointerSet:
	face_total = len(faces)
	face_pointer_set : FacePointerSet = {}

	for face_index, face_pointer in enumerate(face_pointers):
		face_pointer_set[face_index] = [ face_pointer ]

	if faces:
		group_distances = calculate_face_distances(faces)
		numpy.fill_diagonal(group_distances, numpy.inf)

		for _ in range(face_total - 1):
			group_distance_index = numpy.argmin(group_distances)
			group_index, merge_index = numpy.unravel_index(group_distance_index, group_distances.shape)

			if group_distances[group_index, merge_index] < face_distance:
				group_key = list(face_pointer_set.keys())[group_index]
				merge_key = list(face_pointer_set.keys())[merge_index]
				group_total = len(face_pointer_set.get(group_key))
				merge_total = len(face_pointer_set.get(merge_key))
				group_distances = merge_group_distances(group_distances, group_index, group_total, merge_index, merge_total)

				face_pointer_set[group_key].extend(face_pointer_set.pop(merge_key))

	return face_pointer_set


def calculate_face_distances(faces : List[Face]) -> DistanceMatrix:
	face_total = len(faces)
	face_distances = numpy.zeros((face_total, face_total))

	for face_index, face in enumerate(faces):
		for reference_index, reference_face in enumerate(faces):
			face_distances[face_index, reference_index] = calculate_face_distance(face, reference_face)

	return face_distances


def merge_group_distances(group_distances : DistanceMatrix, group_index : int, group_total : int, merge_index : int, merge_total : int) -> DistanceMatrix:
	merge_distances = (group_distances[group_index] * group_total + group_distances[merge_index] * merge_total) / (group_total + merge_total)
	group_distances[group_index] = merge_distances
	group_distances[:, group_index] = merge_distances
	group_distances[group_index, group_index] = numpy.inf
	return numpy.delete(numpy.delete(group_distances, merge_index, axis = 0), merge_index, axis = 1)
