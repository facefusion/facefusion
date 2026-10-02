import numpy

from facefusion.face_helper import WARP_TEMPLATE_SET, apply_nms, average_points, calculate_bounding_box_overlap, calculate_paste_area, convert_to_face_landmark_5, create_bounding_box, create_rotation_matrix_and_size, create_static_anchors, distance_to_bounding_box, distance_to_face_landmark_5, estimate_face_angle, estimate_matrix_by_face_landmark_5, get_nms_threshold, merge_matrix, normalize_bounding_box, paste_back, scale_face_landmark_5, transform_bounding_box, transform_points, warp_face_by_bounding_box, warp_face_by_face_landmark_5, warp_face_by_translation
from facefusion.types import Angle, FaceLandmark68, VisionFrame


def create_split_vision_frame() -> VisionFrame:
	vision_frame = numpy.zeros((300, 300, 3), numpy.uint8)
	vision_frame[:, 150:] = 255
	return vision_frame


def create_face_landmark_68() -> FaceLandmark68:
	face_landmark_68 = numpy.zeros((68, 2))
	face_landmark_68[:, 0] = numpy.arange(68)
	face_landmark_68[:, 1] = numpy.arange(68) * 2
	return face_landmark_68


def create_angle_face_landmark_68(angle : Angle) -> FaceLandmark68:
	face_landmark_68 = numpy.zeros((68, 2))
	face_landmark_68[16] = [ numpy.cos(numpy.radians(angle)) * 100, numpy.sin(numpy.radians(angle)) * 100 ]
	return face_landmark_68


def test_estimate_matrix_by_face_landmark_5() -> None:
	face_landmark_5 = WARP_TEMPLATE_SET.get('arcface_112_v2') * 112

	assert estimate_matrix_by_face_landmark_5(face_landmark_5, 'arcface_112_v2', (112, 112)).round(2).tolist() == [ [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ] ]

	face_landmark_5 = WARP_TEMPLATE_SET.get('arcface_112_v2') * 224 + 10

	assert estimate_matrix_by_face_landmark_5(face_landmark_5, 'arcface_112_v2', (112, 112)).round(2).tolist() == [ [ 0.5, 0.0, -5.0 ], [ 0.0, 0.5, -5.0 ] ]
	assert estimate_matrix_by_face_landmark_5(face_landmark_5, 'arcface_112_v2', (224, 224)).round(2).tolist() == [ [ 1.0, 0.0, -10.0 ], [ 0.0, 1.0, -10.0 ] ]


def test_warp_face_by_face_landmark_5() -> None:
	face_landmark_5 = WARP_TEMPLATE_SET.get('arcface_112_v2') * 224 + 10
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(create_split_vision_frame(), face_landmark_5, 'arcface_112_v2', (112, 112))

	assert crop_vision_frame.shape == (112, 112, 3)
	assert crop_vision_frame[56, 40].tolist() == [ 0, 0, 0 ]
	assert crop_vision_frame[56, 80].tolist() == [ 255, 255, 255 ]
	assert affine_matrix.round(2).tolist() == [ [ 0.5, 0.0, -5.0 ], [ 0.0, 0.5, -5.0 ] ]

	face_landmark_5 = WARP_TEMPLATE_SET.get('arcface_112_v2') * 112 - 30
	crop_vision_frame, _ = warp_face_by_face_landmark_5(numpy.full((300, 300, 3), 255, numpy.uint8), face_landmark_5, 'arcface_112_v2', (112, 112))

	assert crop_vision_frame[0, 0].tolist() == [ 255, 255, 255 ]


def test_warp_face_by_bounding_box() -> None:
	crop_vision_frame, affine_matrix = warp_face_by_bounding_box(create_split_vision_frame(), numpy.array([ 100, 50, 200, 150 ]), (50, 50))

	assert crop_vision_frame.shape == (50, 50, 3)
	assert crop_vision_frame[25, 24].tolist() == [ 0, 0, 0 ]
	assert crop_vision_frame[25, 26].tolist() == [ 255, 255, 255 ]
	assert affine_matrix.tolist() == [ [ 0.5, 0.0, -50.0 ], [ 0.0, 0.5, -25.0 ] ]

	crop_vision_frame, affine_matrix = warp_face_by_bounding_box(create_split_vision_frame(), numpy.array([ 125, 50, 175, 150 ]), (100, 50))

	assert crop_vision_frame.shape == (50, 100, 3)
	assert affine_matrix.tolist() == [ [ 2.0, 0.0, -250.0 ], [ 0.0, 0.5, -25.0 ] ]

	crop_vision_frame, affine_matrix = warp_face_by_bounding_box(create_split_vision_frame(), numpy.array([ 125, 100, 175, 150 ]), (100, 100))

	assert crop_vision_frame.shape == (100, 100, 3)
	assert crop_vision_frame[50, 48].tolist() == [ 0, 0, 0 ]
	assert crop_vision_frame[50, 50].tolist() == [ 255, 255, 255 ]
	assert affine_matrix.tolist() == [ [ 2.0, 0.0, -250.0 ], [ 0.0, 2.0, -200.0 ] ]


def test_warp_face_by_translation() -> None:
	crop_vision_frame, affine_matrix = warp_face_by_translation(create_split_vision_frame(), (-50, -25), 0.5, (100, 80))

	assert crop_vision_frame.shape == (80, 100, 3)
	assert crop_vision_frame[10, 24].tolist() == [ 0, 0, 0 ]
	assert crop_vision_frame[10, 26].tolist() == [ 255, 255, 255 ]
	assert affine_matrix.tolist() == [ [ 0.5, 0, -50 ], [ 0, 0.5, -25 ] ]


def test_paste_back() -> None:
	temp_vision_frame = numpy.zeros((100, 100, 3), numpy.uint8)
	crop_vision_frame = numpy.full((20, 20, 3), 200, numpy.uint8)
	affine_matrix = numpy.array([ [ 1.0, 0.0, -30.0 ], [ 0.0, 1.0, -40.0 ] ])
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, numpy.ones((20, 20), numpy.float32), affine_matrix)

	assert paste_vision_frame.dtype == numpy.uint8
	assert paste_vision_frame[40:60, 30:50].min() == 200
	assert paste_vision_frame[40:60, 30:50].max() == 200
	assert paste_vision_frame.sum() == 20 * 20 * 3 * 200
	assert temp_vision_frame.sum() == 0

	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, numpy.full((20, 20), 0.5, numpy.float32), affine_matrix)

	assert paste_vision_frame[50, 40].tolist() == [ 100, 100, 100 ]

	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, numpy.full((20, 20), 2.0, numpy.float32), affine_matrix)

	assert paste_vision_frame[50, 40].tolist() == [ 200, 200, 200 ]


def test_calculate_paste_area() -> None:
	temp_vision_frame = numpy.zeros((100, 100, 3), numpy.uint8)
	crop_vision_frame = numpy.zeros((20, 20, 3), numpy.uint8)

	paste_bounding_box, paste_matrix = calculate_paste_area(temp_vision_frame, crop_vision_frame, numpy.array([ [ 1.0, 0.0, -30.0 ], [ 0.0, 1.0, -40.0 ] ]))

	assert paste_bounding_box.tolist() == [ 30, 40, 50, 60 ]
	assert paste_matrix.tolist() == [ [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ] ]

	paste_bounding_box, paste_matrix = calculate_paste_area(temp_vision_frame, crop_vision_frame, numpy.array([ [ 1.0, 0.0, 10.0 ], [ 0.0, 1.0, 5.0 ] ]))

	assert paste_bounding_box.tolist() == [ 0, 0, 10, 15 ]
	assert paste_matrix.tolist() == [ [ 1.0, 0.0, -10.0 ], [ 0.0, 1.0, -5.0 ] ]

	paste_bounding_box, paste_matrix = calculate_paste_area(temp_vision_frame, crop_vision_frame, numpy.array([ [ 1.0, 0.0, -90.0 ], [ 0.0, 1.0, -95.0 ] ]))

	assert paste_bounding_box.tolist() == [ 90, 95, 100, 100 ]
	assert paste_matrix.tolist() == [ [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ] ]

	paste_bounding_box, paste_matrix = calculate_paste_area(temp_vision_frame, crop_vision_frame, numpy.array([ [ 2.0, 0.0, -60.0 ], [ 0.0, 2.0, -80.0 ] ]))

	assert paste_bounding_box.tolist() == [ 30, 40, 40, 50 ]
	assert paste_matrix.tolist() == [ [ 0.5, 0.0, 0.0 ], [ 0.0, 0.5, 0.0 ] ]

	paste_bounding_box, _ = calculate_paste_area(numpy.zeros((100, 200, 3), numpy.uint8), crop_vision_frame, numpy.array([ [ 1.0, 0.0, -190.0 ], [ 0.0, 1.0, -10.0 ] ]))

	assert paste_bounding_box.tolist() == [ 190, 10, 200, 30 ]


def test_create_static_anchors() -> None:
	assert create_static_anchors(8, 1, 2, 2).tolist() == [ [ 0, 0 ], [ 8, 0 ], [ 0, 8 ], [ 8, 8 ] ]
	assert create_static_anchors(8, 2, 2, 2).tolist() == [ [ 0, 0 ], [ 0, 0 ], [ 8, 0 ], [ 8, 0 ], [ 0, 8 ], [ 0, 8 ], [ 8, 8 ], [ 8, 8 ] ]
	assert create_static_anchors(16, 1, 3, 3).shape == (9, 2)
	assert create_static_anchors(16, 1, 3, 3)[-1].tolist() == [ 32, 32 ]


def test_create_rotation_matrix_and_size() -> None:
	rotation_matrix, rotation_size = create_rotation_matrix_and_size(0, (200, 100))

	assert rotation_matrix.round(2).tolist() == [ [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ] ]
	assert rotation_size == (200, 100)

	rotation_matrix, rotation_size = create_rotation_matrix_and_size(90, (200, 100))

	assert rotation_matrix.round(2).tolist() == [ [ 0.0, 1.0, 0.0 ], [ -1.0, 0.0, 200.0 ] ]
	assert rotation_size == (100, 200)


def test_create_bounding_box() -> None:
	assert create_bounding_box(create_face_landmark_68()).tolist() == [ 0.0, 0.0, 67.0, 134.0 ]


def test_normalize_bounding_box() -> None:
	assert normalize_bounding_box(numpy.array([ 10, 20, 50, 60 ])).tolist() == [ 10, 20, 50, 60 ]
	assert normalize_bounding_box(numpy.array([ 50, 60, 10, 20 ])).tolist() == [ 10, 20, 50, 60 ]
	assert normalize_bounding_box(numpy.array([ 50, 20, 10, 60 ])).tolist() == [ 10, 20, 50, 60 ]


def test_transform_points() -> None:
	matrix = numpy.array([ [ 2.0, 0.0, 10.0 ], [ 0.0, 3.0, 20.0 ] ])

	assert transform_points(numpy.array([ [ 1, 2 ], [ 3, 4 ] ]), matrix).tolist() == [ [ 12, 26 ], [ 16, 32 ] ]


def test_transform_bounding_box() -> None:
	assert transform_bounding_box(numpy.array([ 10, 20, 30, 40 ]), numpy.array([ [ 2.0, 0.0, 10.0 ], [ 0.0, 3.0, 20.0 ] ])).tolist() == [ 30, 80, 70, 140 ]
	assert transform_bounding_box(numpy.array([ 10, 20, 30, 40 ]), numpy.array([ [ -1.0, 0.0, 100.0 ], [ 0.0, -1.0, 100.0 ] ])).tolist() == [ 70, 60, 90, 80 ]


def test_distance_to_bounding_box() -> None:
	assert distance_to_bounding_box(numpy.array([ [ 10, 20 ] ]), numpy.array([ [ 1, 2, 3, 4 ] ])).tolist() == [ [ 9, 18, 13, 24 ] ]


def test_distance_to_face_landmark_5() -> None:
	assert distance_to_face_landmark_5(numpy.array([ [ 10, 20 ] ]), numpy.array([ [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ] ])).tolist() == [ [ [ 11, 22 ], [ 13, 24 ], [ 15, 26 ], [ 17, 28 ], [ 19, 30 ] ] ]


def test_scale_face_landmark_5() -> None:
	face_landmark_5 = numpy.array([ [ 0.0, 0.0 ], [ 10.0, 0.0 ], [ 5.0, 5.0 ], [ 0.0, 10.0 ], [ 10.0, 10.0 ] ])

	assert scale_face_landmark_5(face_landmark_5, 2.0).tolist() == [ [ -5.0, -5.0 ], [ 15.0, -5.0 ], [ 5.0, 5.0 ], [ -5.0, 15.0 ], [ 15.0, 15.0 ] ]
	assert scale_face_landmark_5(face_landmark_5, 1.0).tolist() == face_landmark_5.tolist()
	assert face_landmark_5.tolist() == [ [ 0.0, 0.0 ], [ 10.0, 0.0 ], [ 5.0, 5.0 ], [ 0.0, 10.0 ], [ 10.0, 10.0 ] ]


def test_convert_to_face_landmark_5() -> None:
	assert convert_to_face_landmark_5(create_face_landmark_68()).tolist() == [ [ 38.5, 77.0 ], [ 44.5, 89.0 ], [ 30.0, 60.0 ], [ 48.0, 96.0 ], [ 54.0, 108.0 ] ]


def test_estimate_face_angle() -> None:
	assert estimate_face_angle(create_angle_face_landmark_68(0)) == 0
	assert estimate_face_angle(create_angle_face_landmark_68(44)) == 0
	assert estimate_face_angle(create_angle_face_landmark_68(46)) == 90
	assert estimate_face_angle(create_angle_face_landmark_68(90)) == 90
	assert estimate_face_angle(create_angle_face_landmark_68(180)) == 180
	assert estimate_face_angle(create_angle_face_landmark_68(270)) == 270
	assert estimate_face_angle(create_angle_face_landmark_68(300)) == 270
	assert estimate_face_angle(create_angle_face_landmark_68(350)) == 0


def test_apply_nms() -> None:
	bounding_boxes =\
	[
		numpy.array([ 0, 0, 10, 10 ]),
		numpy.array([ 1, 1, 11, 11 ]),
		numpy.array([ 50, 50, 60, 60 ])
	]

	assert list(apply_nms(bounding_boxes, [ 0.9, 0.8, 0.7 ], 0.5, 0.4)) == [ 0, 2 ]
	assert list(apply_nms(bounding_boxes, [ 0.8, 0.9, 0.7 ], 0.5, 0.4)) == [ 1, 2 ]
	assert list(apply_nms(bounding_boxes, [ 0.9, 0.8, 0.4 ], 0.5, 0.4)) == [ 0 ]
	assert list(apply_nms(bounding_boxes, [ 0.8, 0.9, 0.7 ], 0.5, 0.9)) == [ 1, 0, 2 ]


def test_get_nms_threshold() -> None:
	assert get_nms_threshold('many', [ 0 ]) == 0.1
	assert get_nms_threshold('many', [ 0, 90 ]) == 0.1
	assert get_nms_threshold('retinaface', [ 0 ]) == 0.4
	assert get_nms_threshold('retinaface', [ 0, 90 ]) == 0.3
	assert get_nms_threshold('retinaface', [ 0, 90, 180 ]) == 0.2
	assert get_nms_threshold('retinaface', [ 0, 90, 180, 270 ]) == 0.1


def test_merge_matrix() -> None:
	translate_matrix = numpy.array([ [ 1.0, 0.0, 10.0 ], [ 0.0, 1.0, 20.0 ] ])
	scale_matrix = numpy.array([ [ 2.0, 0.0, 0.0 ], [ 0.0, 2.0, 0.0 ] ])

	assert merge_matrix([ translate_matrix ]).tolist() == [ [ 1.0, 0.0, 10.0 ], [ 0.0, 1.0, 20.0 ] ]
	assert merge_matrix([ translate_matrix, scale_matrix ]).tolist() == [ [ 2.0, 0.0, 20.0 ], [ 0.0, 2.0, 40.0 ] ]
	assert merge_matrix([ scale_matrix, translate_matrix ]).tolist() == [ [ 2.0, 0.0, 10.0 ], [ 0.0, 2.0, 20.0 ] ]
	assert merge_matrix([ translate_matrix, scale_matrix, translate_matrix ]).tolist() == [ [ 2.0, 0.0, 30.0 ], [ 0.0, 2.0, 60.0 ] ]


def test_calculate_bounding_box_overlap() -> None:
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 0, 0, 10, 10 ])) == 1.0
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 5, 0, 15, 10 ])) == 50 / 150
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 0, 5, 10, 15 ])) == 50 / 150
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 2, 2, 6, 6 ])) == 0.16
	assert calculate_bounding_box_overlap(numpy.array([ 2, 2, 6, 6 ]), numpy.array([ 0, 0, 10, 10 ])) == 0.16
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 20, 20, 30, 30 ])) == 0.0
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 10, 10 ]), numpy.array([ 20, 0, 30, 10 ])) == 0.0
	assert calculate_bounding_box_overlap(numpy.array([ 0, 0, 0, 0 ]), numpy.array([ 0, 0, 0, 0 ])) == 0.0
	assert calculate_bounding_box_overlap(numpy.array([ 0.0, 0.0, 0.5, 0.5 ]), numpy.array([ 0.0, 0.0, 0.5, 0.5 ])) == 1.0


def test_average_points() -> None:
	assert average_points(numpy.array([ 0.0, 10.0 ]), numpy.array([ 10.0, 30.0 ]), 0.0).tolist() == [ 0.0, 10.0 ]
	assert average_points(numpy.array([ 0.0, 10.0 ]), numpy.array([ 10.0, 30.0 ]), 0.25).tolist() == [ 2.5, 15.0 ]
	assert average_points(numpy.array([ 0.0, 10.0 ]), numpy.array([ 10.0, 30.0 ]), 1.0).tolist() == [ 10.0, 30.0 ]
