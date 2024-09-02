import sys

from facefusion.typing import AppContext


def detect_app_context() -> AppContext:
	frame = sys._getframe(1)

	while frame:
		if 'facefusion/jobs' in frame.f_code.co_filename:
			return 'cli'
		if 'facefusion/uis' in frame.f_code.co_filename:
			return 'ui'
		frame = frame.f_back
	return 'cli'
