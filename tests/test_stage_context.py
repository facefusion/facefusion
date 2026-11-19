from contextvars import copy_context

from facefusion.stage_context import get_stage, reset_stage, set_stage
from facefusion.types import Stage


def create_stage() -> Stage:
	return\
	{
		'type': 'extract',
		'title': 'extracting',
		'progress':
		{
			'unit': 'frame',
			'current': 0,
			'started_at': 10.0,
			'updated_at': 10.0
		}
	}


def test_get_stage() -> None:
	assert copy_context().run(get_stage) is None


def test_set_stage() -> None:
	stage = create_stage()
	stage_token = set_stage(stage)

	assert get_stage() is stage

	reset_stage(stage_token)


def test_reset_stage() -> None:
	stage = create_stage()
	stage_token = set_stage(stage)
	reset_stage(stage_token)

	assert get_stage() is None
