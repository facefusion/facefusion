import os
import sys

from facefusion.types import AppContext


def detect_app_context() -> AppContext:
	frame = sys._getframe(1)

	while frame:
		if os.path.join('facefusion', 'jobs') in frame.f_code.co_filename:
			return 'cli'
		if os.path.join('facefusion', 'apis') in frame.f_code.co_filename:
			return 'api'
		frame = frame.f_back
	return 'cli'
