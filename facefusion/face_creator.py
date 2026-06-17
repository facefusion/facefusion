from facefusion.face_helper import estimate_face_angle
from facefusion.types import Face, FaceLandmarkSet, Points


def interpolate_face(anchor_face_before : Face, anchor_face_after : Face, ratio : float) -> Face:
	bounding_box = interpolate_points(anchor_face_before.bounding_box, anchor_face_after.bounding_box, ratio)
	landmark_set : FaceLandmarkSet =\
	{
		'5': interpolate_points(anchor_face_before.landmark_set.get('5'), anchor_face_after.landmark_set.get('5'), ratio),
		'5/68': interpolate_points(anchor_face_before.landmark_set.get('5/68'), anchor_face_after.landmark_set.get('5/68'), ratio),
		'68': interpolate_points(anchor_face_before.landmark_set.get('68'), anchor_face_after.landmark_set.get('68'), ratio),
		'68/5': interpolate_points(anchor_face_before.landmark_set.get('68/5'), anchor_face_after.landmark_set.get('68/5'), ratio)
	}
	anchor_face = anchor_face_after

	if ratio < 0.5:
		anchor_face = anchor_face_before

	return anchor_face._replace(
		bounding_box = bounding_box,
		landmark_set = landmark_set,
		angle = estimate_face_angle(landmark_set.get('68/5'))
	)


def interpolate_points(array_before : Points, array_after : Points, ratio : float) -> Points:
	return array_before * (1 - ratio) + array_after * ratio
