
import cv2
import numpy
import pytest

from facefusion import face_aligner, face_classifier, face_detector, face_recognizer, face_store, ffmpeg, ffmpeg_builder, inference_manager, process_manager, state_manager
from facefusion.common_helper import get_first
from facefusion.download import conditional_download
from facefusion.face_creator import average_face_geometry, average_face_identity, create_faces, get_many_faces, get_one_face, get_static_faces, refill_faces, scale_face
from facefusion.face_detector import detect_faces
from facefusion.face_recognizer import calculate_face_embedding
from facefusion.vision import read_static_image
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()

	face_store.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	for crop_scale in [ 80, 70, 60 ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('source.jpg')),
				[
					'-vf',
					'crop=iw*0.' + str(crop_scale) + ':ih*0.' + str(crop_scale)
				],
				ffmpeg_builder.set_output(get_test_example_file('source-' + str(crop_scale) + 'crop.jpg'))
			)
		)

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'many')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_aligner_model', 'many')
	state_manager.init_item('face_aligner_score', 0.5)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_aligner.clear_inference_pool()
	face_recognizer.clear_inference_pool()

	face_store.clear()


def test_create_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	bounding_boxes, face_scores, face_landmarks_5 = detect_faces(source_vision_frame)
	faces = create_faces(source_vision_frame, bounding_boxes, face_scores, face_landmarks_5)
	face = get_one_face(faces)

	assert len(faces) == 1
	assert face.origin == 'detect'
	assert list(face.landmark_set.keys()) == [ '5', '5/68', '68', '68/5' ]
	assert face.landmark_set.get('5').shape == (5, 2)
	assert face.landmark_set.get('5/68').shape == (5, 2)
	assert face.landmark_set.get('68').shape == (68, 2)
	assert face.landmark_set.get('68/5').shape == (68, 2)
	assert face.score_set.get('detector') > 0.5
	assert face.score_set.get('aligner') > 0.5
	assert face.angle == 0
	assert face.embedding.shape == (512,)
	assert face.embedding_norm.shape == (512,)
	assert numpy.linalg.norm(face.embedding_norm).round(2) == 1.0
	assert numpy.array_equal(face.embedding, get_first(calculate_face_embedding(source_vision_frame, face.landmark_set.get('5/68')))) is True
	assert face.gender == 'female'
	assert face.race == 'white'
	assert face.age == range(20, 29)

	assert len(create_faces(source_vision_frame, bounding_boxes * 2, face_scores * 2, face_landmarks_5 * 2)) == 1
	assert create_faces(source_vision_frame, bounding_boxes, [ 0.1 ] * len(face_scores), face_landmarks_5) == []

	state_manager.set_item('face_aligner_score', 1.0)
	face = get_one_face(create_faces(source_vision_frame, bounding_boxes, face_scores, face_landmarks_5))

	assert face.landmark_set.get('5/68') is face.landmark_set.get('5')
	assert face.score_set.get('aligner') > 0.5

	state_manager.set_item('face_aligner_score', 0)
	face = get_one_face(create_faces(source_vision_frame, bounding_boxes, face_scores, face_landmarks_5))

	assert face.landmark_set.get('68') is face.landmark_set.get('68/5')
	assert face.score_set.get('aligner') == 0.0

	state_manager.set_item('face_aligner_score', 0.5)


def test_get_one_face() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_first = face._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]))
	face_last = face._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]))

	assert face.bounding_box.size == 4
	assert get_one_face([ face_first, face_last ]) is face_first
	assert get_one_face([ face_first, face_last ], 1) is face_last
	assert get_one_face([ face_first, face_last ], 5) is face_last
	assert get_one_face([]) is None


def test_get_many_faces() -> None:
	source_path = get_test_example_file('source.jpg')
	source_vision_frame = read_static_image(source_path)
	many_faces = get_many_faces([ source_vision_frame, source_vision_frame, source_vision_frame ])

	assert len(many_faces) == 3
	assert len(get_many_faces([ numpy.hstack([ source_vision_frame, source_vision_frame ]) ])) == 2
	assert get_many_faces([ numpy.zeros_like(source_vision_frame) ]) == []
	assert get_many_faces([ numpy.zeros((10, 10)) ]) == []

	state_manager.set_item('face_detector_score', 0)

	assert get_many_faces([ source_vision_frame ]) == []

	state_manager.set_item('face_detector_score', 0.5)
	state_manager.set_item('face_detector_angles', [ 90 ])

	many_faces = get_many_faces([ cv2.rotate(source_vision_frame, cv2.ROTATE_90_CLOCKWISE) ])
	bounding_box = many_faces[0].bounding_box

	assert len(many_faces) == 1
	assert bounding_box[2] - bounding_box[0] > bounding_box[3] - bounding_box[1]

	state_manager.set_item('face_detector_angles', [ 0 ])


def test_get_static_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	empty_vision_frame = numpy.zeros_like(source_vision_frame)

	assert face_store.get_faces(source_vision_frame) is None

	static_faces = get_static_faces([ source_vision_frame ])

	assert len(static_faces) == 1
	assert face_store.get_faces(source_vision_frame) == static_faces
	assert get_one_face(get_static_faces([ source_vision_frame ])) is get_one_face(static_faces)
	assert len(get_static_faces([ source_vision_frame, empty_vision_frame, source_vision_frame ])) == 2
	assert get_static_faces([ empty_vision_frame ]) == []
	assert face_store.get_faces(empty_vision_frame) is None


def test_refill_faces() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_first = face._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]))
	face_middle = face._replace(bounding_box = numpy.array([ 40, 40, 50, 50 ]))
	face_last = face._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]))

	fill_faces = refill_faces([ face_first, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]

	fill_faces = refill_faces([ face_first, None, None, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 20.0, 20.0, 30.0, 30.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[3].bounding_box.tolist() == [ 60.0, 60.0, 70.0, 70.0 ]
	assert fill_faces[4].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]

	fill_faces = refill_faces([ face_first, None, face_middle, None, face_last ])

	assert fill_faces[0].bounding_box.tolist() == [ 0.0, 0.0, 10.0, 10.0 ]
	assert fill_faces[1].bounding_box.tolist() == [ 20.0, 20.0, 30.0, 30.0 ]
	assert fill_faces[2].bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert fill_faces[3].bounding_box.tolist() == [ 60.0, 60.0, 70.0, 70.0 ]
	assert fill_faces[4].bounding_box.tolist() == [ 80.0, 80.0, 90.0, 90.0 ]


def test_average_face_geometry() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face_previous = get_one_face(get_many_faces([ source_vision_frame ]))
	face_next = get_one_face(get_many_faces([ source_vision_frame ]))
	face_previous = face_previous._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]))
	face_next = face_next._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]))

	assert average_face_geometry([face_previous, face_next], 0.5).bounding_box.tolist() == [40.0, 40.0, 50.0, 50.0]
	assert average_face_geometry([face_previous, face_next], 0.5).angle == face_next.angle
	assert average_face_geometry([face_previous, face_next], 0.5).embedding is face_next.embedding
	assert average_face_geometry([face_previous, face_next], 0.25).embedding is face_previous.embedding


def test_average_face_identity() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face_first = face._replace(bounding_box = numpy.array([ 0, 0, 10, 10 ]), embedding = numpy.array([ 1.0, 3.0 ]), embedding_norm = numpy.array([ 1.0, 0.0 ]))
	face_last = face._replace(bounding_box = numpy.array([ 80, 80, 90, 90 ]), embedding = numpy.array([ 5.0, 9.0 ]), embedding_norm = numpy.array([ 1.0, 1.0 ]))
	average_face = average_face_identity([ face_first, face_last ])

	assert average_face.embedding.tolist() == [ 3.0, 6.0 ]
	assert average_face.embedding_norm.tolist() == [ 1.0, 0.5 ]
	assert average_face.bounding_box is face_first.bounding_box
	assert average_face.landmark_set is face_first.landmark_set
	assert average_face_identity([ face_last ]).embedding.tolist() == [ 5.0, 9.0 ]
	assert average_face_identity([]) is None


def test_scale_face() -> None:
	source_vision_frame = read_static_image(get_test_example_file('source.jpg'))
	face = get_one_face(get_many_faces([ source_vision_frame ]))
	face = face._replace(bounding_box = numpy.array([ 10, 20, 30, 40 ]), landmark_set =
	{
		'5': numpy.array([ [ 10, 20 ] ]),
		'5/68': numpy.array([ [ 12, 22 ] ]),
		'68': numpy.array([ [ 14, 24 ] ]),
		'68/5': numpy.array([ [ 16, 26 ] ])
	})
	scale_target_face = scale_face(face, numpy.zeros((100, 200, 3)), numpy.zeros((200, 100, 3)))

	assert scale_target_face.bounding_box.tolist() == [ 5.0, 40.0, 15.0, 80.0 ]
	assert scale_target_face.landmark_set.get('5').tolist() == [ [ 5.0, 40.0 ] ]
	assert scale_target_face.landmark_set.get('5/68').tolist() == [ [ 6.0, 44.0 ] ]
	assert scale_target_face.landmark_set.get('68').tolist() == [ [ 7.0, 48.0 ] ]
	assert scale_target_face.landmark_set.get('68/5').tolist() == [ [ 8.0, 52.0 ] ]
	assert scale_target_face.embedding is face.embedding
	assert face.bounding_box.tolist() == [ 10, 20, 30, 40 ]
