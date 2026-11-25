from typing import List

import numpy

from facefusion.face_creator import average_face_identity
from facefusion.face_selector import calculate_face_distance
from facefusion.types import Distance, DistanceMatrix, Face, FacePointer, FacePointerSet


def create_face_pointer_set(faces : List[Face], face_pointers : List[FacePointer], face_distance : Distance) -> FacePointerSet:
	face_total = len(faces)
	group_keys : List[str] = []
	merge_face_pointer_set : FacePointerSet = {}
	sort_face_pointer_set : FacePointerSet = {}

	for face_index, face_pointer in enumerate(face_pointers):
		group_key = str(face_index)
		group_keys.append(group_key)
		merge_face_pointer_set[group_key] = [ face_pointer ]

	if faces:
		group_distances = calculate_face_distances(faces)
		numpy.fill_diagonal(group_distances, numpy.inf)

		for _ in range(face_total - 1):
			group_distance_index = numpy.argmin(group_distances)
			group_index, merge_index = numpy.unravel_index(group_distance_index, group_distances.shape)

			if group_distances[group_index, merge_index] < face_distance:
				group_key = group_keys[group_index]
				merge_key = group_keys.pop(merge_index)
				group_total = len(merge_face_pointer_set.get(group_key))
				merge_total = len(merge_face_pointer_set.get(merge_key))
				group_distances = merge_group_distances(group_distances, group_index, group_total, merge_index, merge_total)

				merge_face_pointer_set[group_key].extend(merge_face_pointer_set.pop(merge_key))

	for group_key in group_keys:
		group_faces = []

		for face_pointer in merge_face_pointer_set.get(group_key):
			group_faces.append(faces[face_pointers.index(face_pointer)])

		merge_face_pointer_set[group_key] = sort_face_pointer_group(group_faces, merge_face_pointer_set.get(group_key))

	for face_pointer_group_index, face_pointer_group in enumerate(sorted(merge_face_pointer_set.values(), key = len, reverse = True)):
		sort_face_pointer_set[str(face_pointer_group_index)] = face_pointer_group

	return sort_face_pointer_set


def sort_face_pointer_group(faces : List[Face], face_pointers : List[FacePointer]) -> List[FacePointer]:
	average_face = average_face_identity(faces)
	average_distances : List[Distance] = []
	sort_face_pointers : List[FacePointer] = []

	for face in faces:
		average_distances.append(calculate_face_distance(face, average_face))

	sort_indexes = numpy.argsort(numpy.round(average_distances, 4), kind = 'stable').tolist()

	for sort_index in sort_indexes:
		sort_face_pointers.append(face_pointers[sort_index])

	return sort_face_pointers


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
