import pytest

from facefusion import state_manager
from facefusion.apis.state_helper import normalize_argument_value, validate_argument_key, validate_argument_value
from facefusion.program import create_program


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	create_program()


def test_validate_argument_key() -> None:
	assert validate_argument_key('face_detector_score') is True
	assert validate_argument_key('face_swapper_model') is True
	assert validate_argument_key('jobs_path') is False
	assert validate_argument_key('temp_path') is False
	assert validate_argument_key('api_session_limit') is False
	assert validate_argument_key('invalid') is False


def test_validate_argument_value() -> None:
	assert validate_argument_value('output_video_quality', 50) is True
	assert validate_argument_value('output_video_quality', 101) is False
	assert validate_argument_value('output_video_quality', -1) is False
	assert validate_argument_value('output_video_quality', '50') is False
	assert validate_argument_value('output_video_quality', 50.5) is False
	assert validate_argument_value('reference_face_position', 3) is True
	assert validate_argument_value('reference_face_position', 'invalid') is False
	assert validate_argument_value('reference_face_position', None) is False
	assert validate_argument_value('face_detector_score', 0.5) is True
	assert validate_argument_value('face_detector_score', 0.51) is False
	assert validate_argument_value('face_detector_score', 'invalid') is False
	assert validate_argument_value('output_video_fps', 25.0) is True
	assert validate_argument_value('output_video_fps', 'invalid') is False
	assert validate_argument_value('face_detector_size', '640x640') is True
	assert validate_argument_value('face_detector_size', 'invalid') is False
	assert validate_argument_value('face_detector_size', 640) is False
	assert validate_argument_value('face_mask_types', [ 'box', 'occlusion' ]) is True
	assert validate_argument_value('face_mask_types', []) is True
	assert validate_argument_value('face_mask_types', [ 'box', 'invalid' ]) is False
	assert validate_argument_value('face_mask_types', 'box') is False
	assert validate_argument_value('face_detector_margin', (0, 0, 0, 0)) is True
	assert validate_argument_value('face_detector_margin', [ 0, 0, 0, 0 ]) is False
	assert validate_argument_value('face_detector_margin', None) is False
	assert validate_argument_value('face_selector_mode', 'one') is True
	assert validate_argument_value('face_selector_mode', 'invalid') is False
	assert validate_argument_value('face_selector_mode', 1) is False
	assert validate_argument_value('face_selector_mode', [ 'one' ]) is False


def test_normalize_argument_value() -> None:
	assert normalize_argument_value('output_video_quality', '50') == 50
	assert normalize_argument_value('output_video_quality', 50.7) == 50
	assert normalize_argument_value('output_video_quality', 'invalid') is None
	assert normalize_argument_value('face_detector_score', '0.5') == 0.5
	assert normalize_argument_value('face_detector_score', 1) == 1.0
	assert normalize_argument_value('face_detector_score', 'invalid') is None
	assert normalize_argument_value('halt_on_error', 'True') is True
	assert normalize_argument_value('halt_on_error', 'False') is False
	assert normalize_argument_value('halt_on_error', 'invalid') is None
	assert normalize_argument_value('background_remover_fill_color', [ 255 ]) == (255, 255, 255, 255)
	assert normalize_argument_value('background_remover_despill_color', [ 0, 255, 0 ]) == (0, 255, 0, 255)
	assert normalize_argument_value('background_remover_fill_color', 'invalid') is None
	assert normalize_argument_value('face_detector_margin', [ 1, 2 ]) == (1, 2, 1, 2)
	assert normalize_argument_value('face_mask_padding', [ 1 ]) == (1, 1, 1, 1)
	assert normalize_argument_value('face_mask_padding', 'invalid') is None
	assert normalize_argument_value('face_selector_mode', 'one') == 'one'
	assert normalize_argument_value('face_mask_types', [ 'box' ]) == [ 'box' ]
