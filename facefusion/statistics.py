from typing import Any, Dict
import numpy

import facefusion.globals
from facefusion.face_store import FACE_STORE
from facefusion.typing import FaceSet
from facefusion import logger


def create_statistics(static_faces : FaceSet) -> Dict[str, Any]:
	face_detector_score_list = []
	face_landmarker_score_list = []
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
			face_detector_score_list.append(face.scores.get('detector'))
			face_landmarker_score_list.append(face.scores.get('landmarker'))
			if numpy.array_equal(face.landmarks.get('5'), face.landmarks.get('5/68')):
				statistics['total_face_landmark_5_fallbacks'] = statistics.get('total_face_landmark_5_fallbacks') + 1

	if face_detector_score_list:
		statistics['min_face_detector_score'] = round(min(face_detector_score_list), 2)
		statistics['max_face_detector_score'] = round(max(face_detector_score_list), 2)
		statistics['average_face_detector_score'] = round(numpy.mean(face_detector_score_list), 2)
	if face_landmarker_score_list:
		statistics['min_face_landmarker_score'] = round(min(face_landmarker_score_list), 2)
		statistics['max_face_landmarker_score'] = round(max(face_landmarker_score_list), 2)
		statistics['average_face_landmarker_score'] = round(numpy.mean(face_landmarker_score_list), 2)
	return statistics


def conditional_log_statistics() -> None:
	if facefusion.globals.log_level == 'debug':
		statistics = create_statistics(FACE_STORE.get('static_faces'))

		for name, value in statistics.items():
			logger.debug(str(name) + ': ' + str(value), __name__.upper())
