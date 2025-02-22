from typing import List, Optional

import numpy

from facefusion import state_manager
from facefusion.common_helper import get_first
from facefusion.face_classifier import classify_face
from facefusion.face_detector import detect_faces, detect_rotated_faces
from facefusion.face_helper import apply_nms, convert_to_face_landmark_5, estimate_face_angle, get_nms_threshold
from facefusion.face_landmarker import detect_face_landmark, estimate_face_landmark_68_5
from facefusion.face_recognizer import calc_embedding
from facefusion.face_store import get_static_faces, set_static_faces
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
		embedding, normed_embedding = calc_embedding(vision_frame, face_landmark_set.get('5/68'))
		gender, age, race = classify_face(vision_frame, face_landmark_set.get('5/68'))
		faces.append(Face(
			bounding_box = bounding_box,
			score_set = face_score_set,
			landmark_set = face_landmark_set,
			angle = face_angle,
			embedding = embedding,
			normed_embedding = normed_embedding,
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


def get_average_face(faces : List[Face]) -> Optional[Face]:
	embeddings = []
	normed_embeddings = []

	if faces:
		first_face = get_first(faces)

		for face in faces:
			embeddings.append(face.embedding)
			normed_embeddings.append(face.normed_embedding)

		return Face(
			bounding_box = first_face.bounding_box,
			score_set = first_face.score_set,
			landmark_set = first_face.landmark_set,
			angle = first_face.angle,
			embedding = numpy.mean(embeddings, axis = 0),
			normed_embedding = numpy.mean(normed_embeddings, axis = 0),
			gender = first_face.gender,
			age = first_face.age,
			race = first_face.race
		)
	return None


def get_many_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	many_faces : List[Face] = []

	for vision_frame in vision_frames:
		if numpy.any(vision_frame):
			static_faces = get_static_faces(vision_frame)
			if static_faces:
				many_faces.extend(static_faces)
			else:
				all_bounding_boxes = []
				all_face_scores = []
				all_face_landmarks_5 = []

				for face_detector_angle in state_manager.get_item('face_detector_angles'):
					if face_detector_angle == 0:
						bounding_boxes, face_scores, face_landmarks_5 = detect_faces(vision_frame)
					else:
						bounding_boxes, face_scores, face_landmarks_5 = detect_rotated_faces(vision_frame, face_detector_angle)
					all_bounding_boxes.extend(bounding_boxes)
					all_face_scores.extend(face_scores)
					all_face_landmarks_5.extend(face_landmarks_5)

				if all_bounding_boxes and all_face_scores and all_face_landmarks_5 and state_manager.get_item('face_detector_score') > 0:
					faces = create_faces(vision_frame, all_bounding_boxes, all_face_scores, all_face_landmarks_5)

					if faces:
						many_faces.extend(faces)
						set_static_faces(vision_frame, faces)
	return many_faces
