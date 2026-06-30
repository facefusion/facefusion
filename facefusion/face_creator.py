from typing import List, Optional

import numpy

from facefusion import face_store, state_manager
from facefusion.common_helper import get_first, get_middle
from facefusion.face_classifier import classify_face
from facefusion.face_detector import detect_faces, detect_faces_by_angle
from facefusion.face_helper import apply_nms, average_points, convert_to_face_landmark_5, estimate_face_angle, get_nms_threshold
from facefusion.face_landmarker import detect_face_landmark, estimate_face_landmark_68_5
from facefusion.face_recognizer import calculate_face_embedding
from facefusion.types import BoundingBox, Face, FaceLandmark5, FaceLandmarkSet, FaceScoreSet, Score, VisionFrame


def create_faces(vision_frame : VisionFrame, bounding_boxes : List[BoundingBox], face_scores : List[Score], face_landmarks_5 : List[FaceLandmark5]) -> List[Face]:
	faces = []
	nms_threshold = get_nms_threshold(state_manager.get_item('face_detector_model'), state_manager.get_item('face_detector_angles'))
	keep_indices = apply_nms(bounding_boxes, face_scores, state_manager.get_item('face_detector_score'), nms_threshold)

	for index in keep_indices:
		bounding_box = bounding_boxes[index]
		face_score = face_scores[index]
		face_landmark_5 = face_landmarks_5[index]
		face_landmark_5_68 = face_landmark_5
		face_landmark_68_5 = estimate_face_landmark_68_5(face_landmark_5_68)
		face_landmark_68 = face_landmark_68_5
		face_landmark_score_68 = 0.0
		face_angle = estimate_face_angle(face_landmark_68_5)

		if state_manager.get_item('face_landmarker_score') > 0:
			face_landmark_68, face_landmark_score_68 = detect_face_landmark(vision_frame, bounding_box, face_angle)
		if face_landmark_score_68 > state_manager.get_item('face_landmarker_score'):
			face_landmark_5_68 = convert_to_face_landmark_5(face_landmark_68)

		face_landmark_set : FaceLandmarkSet =\
		{
			'5': face_landmark_5,
			'5/68': face_landmark_5_68,
			'68': face_landmark_68,
			'68/5': face_landmark_68_5
		}
		face_score_set : FaceScoreSet =\
		{
			'detector': face_score,
			'landmarker': face_landmark_score_68
		}
		face_embedding, face_embedding_norm = calculate_face_embedding(vision_frame, face_landmark_set.get('5/68'))
		gender, age, race = classify_face(vision_frame, face_landmark_set.get('5/68'))

		faces.append(Face(
			origin = 'detect',
			bounding_box = bounding_box,
			score_set = face_score_set,
			landmark_set = face_landmark_set,
			angle = face_angle,
			embedding = face_embedding,
			embedding_norm = face_embedding_norm,
			gender = gender,
			age = age,
			race = race
		))
	return faces


def get_one_face(faces : List[Face], position : int = 0) -> Optional[Face]:
	if faces:
		position = min(position, len(faces) - 1)
		return faces[position]
	return None


def get_many_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	many_faces : List[Face] = []

	for vision_frame in vision_frames:
		if numpy.any(vision_frame):
			all_bounding_boxes = []
			all_face_scores = []
			all_face_landmarks_5 = []

			for face_detector_angle in state_manager.get_item('face_detector_angles'):
				if face_detector_angle == 0:
					bounding_boxes, face_scores, face_landmarks_5 = detect_faces(vision_frame)
				else:
					bounding_boxes, face_scores, face_landmarks_5 = detect_faces_by_angle(vision_frame, face_detector_angle)
				all_bounding_boxes.extend(bounding_boxes)
				all_face_scores.extend(face_scores)
				all_face_landmarks_5.extend(face_landmarks_5)

			if all_bounding_boxes and all_face_scores and all_face_landmarks_5 and state_manager.get_item('face_detector_score') > 0:
				faces = create_faces(vision_frame, all_bounding_boxes, all_face_scores, all_face_landmarks_5)

				if faces:
					many_faces.extend(faces)

	return many_faces


def get_static_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	many_faces : List[Face] = []

	for vision_frame in vision_frames:
		faces = face_store.get_faces(vision_frame)

		if not faces:
			with face_store.resolve_lock(vision_frame):
				faces = face_store.get_faces(vision_frame)

				if not faces:
					faces = get_many_faces([ vision_frame ])

					if faces:
						face_store.set_faces(vision_frame, faces)

		many_faces.extend(faces)

	return many_faces


def refill_faces(faces : List[Optional[Face]]) -> List[Face]:
	fill_faces = []
	anchor_index_previous = -1

	for index, face in enumerate(faces):
		if face:
			for gap_index in range(anchor_index_previous + 1, index):
				average_factor = (gap_index - anchor_index_previous) / (index - anchor_index_previous)
				average_face = average_face_geometry([faces[anchor_index_previous], face], average_factor)
				fill_faces.append(average_face)

			fill_faces.append(face)
			anchor_index_previous = index

	return fill_faces


def average_face_geometry(faces : List[Face], average_factor : float) -> Face:
	face_first = get_first(faces)
	face_middle = get_middle(faces)
	face_anchor = face_middle

	if average_factor < 0.5:
		face_anchor = face_first

	landmark_set : FaceLandmarkSet =\
	{
		'5': average_points(face_first.landmark_set.get('5'), face_middle.landmark_set.get('5'), average_factor),
		'5/68': average_points(face_first.landmark_set.get('5/68'), face_middle.landmark_set.get('5/68'), average_factor),
		'68': average_points(face_first.landmark_set.get('68'), face_middle.landmark_set.get('68'), average_factor),
		'68/5': average_points(face_first.landmark_set.get('68/5'), face_middle.landmark_set.get('68/5'), average_factor)
	}

	return Face(
		origin = 'refill',
		bounding_box = average_points(face_first.bounding_box, face_middle.bounding_box, average_factor),
		score_set = face_anchor.score_set,
		landmark_set = landmark_set,
		angle = estimate_face_angle(landmark_set.get('68/5')),
		embedding = face_anchor.embedding,
		embedding_norm = face_anchor.embedding_norm,
		gender = face_anchor.gender,
		age = face_anchor.age,
		race = face_anchor.race
	)


def average_face_identity(faces : List[Face]) -> Optional[Face]:
	face_embeddings = []
	face_embeddings_norm = []

	if faces:
		first_face = get_first(faces)

		for face in faces:
			face_embeddings.append(face.embedding)
			face_embeddings_norm.append(face.embedding_norm)

		return Face(
			origin = first_face.origin,
			bounding_box = first_face.bounding_box,
			score_set = first_face.score_set,
			landmark_set = first_face.landmark_set,
			angle = first_face.angle,
			embedding = numpy.mean(face_embeddings, axis = 0),
			embedding_norm = numpy.mean(face_embeddings_norm, axis = 0),
			gender = first_face.gender,
			age = first_face.age,
			race = first_face.race
		)
	return None


def scale_face(target_face : Face, target_vision_frame : VisionFrame, temp_vision_frame : VisionFrame) -> Face:
	scale_x = temp_vision_frame.shape[1] / target_vision_frame.shape[1]
	scale_y = temp_vision_frame.shape[0] / target_vision_frame.shape[0]

	bounding_box = target_face.bounding_box * [ scale_x, scale_y, scale_x, scale_y ]
	landmark_set =\
	{
		'5': target_face.landmark_set.get('5') * numpy.array([ scale_x, scale_y ]),
		'5/68': target_face.landmark_set.get('5/68') * numpy.array([ scale_x, scale_y ]),
		'68': target_face.landmark_set.get('68') * numpy.array([ scale_x, scale_y ]),
		'68/5': target_face.landmark_set.get('68/5') * numpy.array([ scale_x, scale_y ])
	}

	return target_face._replace(
		bounding_box = bounding_box,
		landmark_set = landmark_set
	)
