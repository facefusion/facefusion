from typing import Any, Dict

import numpy

from facefusion import logger, state_manager
from facefusion.face_store import get_face_store
from facefusion.typing import FaceSet


def create_statistics(static_faces : FaceSet) -> Dict[str, Any]:
	face_detector_scores = []
	face_landmarker_scores = []
	statistics =\
	{
		'min_face_detector_score': 0,
		'min_face_landmarker_score': 0,
		'max_face_detector_score': 0,
		'max_face_landmarker_score': 0,
		'average_face_detector_score': 0,
		'average_face_landmarker_score': 0,
		'total_face_landmark_5_fallbacks': 0,
		'total_frames_with_faces': 0,
		'total_faces': 0
	}

	for faces in static_faces.values():
		statistics['total_frames_with_faces'] = statistics.get('total_frames_with_faces') + 1
		for face in faces:
			statistics['total_faces'] = statistics.get('total_faces') + 1
			face_detector_scores.append(face.score_set.get('detector'))
			face_landmarker_scores.append(face.score_set.get('landmarker'))
			if numpy.array_equal(face.landmark_set.get('5'), face.landmark_set.get('5/68')):
				statistics['total_face_landmark_5_fallbacks'] = statistics.get('total_face_landmark_5_fallbacks') + 1

	if face_detector_scores:
		statistics['min_face_detector_score'] = round(min(face_detector_scores), 2)
		statistics['max_face_detector_score'] = round(max(face_detector_scores), 2)
		statistics['average_face_detector_score'] = round(numpy.mean(face_detector_scores), 2)
	if face_landmarker_scores:
		statistics['min_face_landmarker_score'] = round(min(face_landmarker_scores), 2)
		statistics['max_face_landmarker_score'] = round(max(face_landmarker_scores), 2)
		statistics['average_face_landmarker_score'] = round(numpy.mean(face_landmarker_scores), 2)
	return statistics


def conditional_log_statistics() -> None:
	if state_manager.get_item('log_level') == 'debug':
		statistics = create_statistics(get_face_store().get('static_faces'))

		for name, value in statistics.items():
			logger.debug(str(name) + ': ' + str(value), __name__)
