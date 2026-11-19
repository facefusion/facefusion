from contextvars import ContextVar, Token
from typing import Optional

from facefusion.types import Stage

STAGE_CONTEXT : ContextVar[Optional[Stage]] = ContextVar('STAGE_CONTEXT', default = None)


def get_stage() -> Optional[Stage]:
	return STAGE_CONTEXT.get()


def set_stage(stage : Stage) -> Token[Optional[Stage]]:
	return STAGE_CONTEXT.set(stage)


def reset_stage(stage_token : Token[Optional[Stage]]) -> None:
	STAGE_CONTEXT.reset(stage_token)
