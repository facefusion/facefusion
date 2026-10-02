import facefusion.choices


def test_face_detector_set() -> None:
	assert list(facefusion.choices.face_detector_set.keys()) == facefusion.choices.face_detector_models


def test_execution_provider_set() -> None:
	assert list(facefusion.choices.execution_provider_set.keys()) == facefusion.choices.execution_providers


def test_download_provider_set() -> None:
	assert list(facefusion.choices.download_provider_set.keys()) == facefusion.choices.download_providers


def test_log_level_set() -> None:
	assert list(facefusion.choices.log_level_set.keys()) == facefusion.choices.log_levels


def test_execution_thread_count_range() -> None:
	assert facefusion.choices.execution_thread_count_range[0] == 1
	assert facefusion.choices.execution_thread_count_range[-1] == 32


def test_face_detector_angles() -> None:
	assert facefusion.choices.face_detector_angles == [ 0, 90, 180, 270 ]


def test_output_image_scale_range() -> None:
	assert facefusion.choices.output_image_scale_range[0] == 0.25
	assert facefusion.choices.output_image_scale_range[-1] == 8.0


def test_output_video_scale_range() -> None:
	assert facefusion.choices.output_video_scale_range[0] == 0.25
	assert facefusion.choices.output_video_scale_range[-1] == 8.0
