import os
import sys

from testingss.types import AppContext


def detect_app_context() -> AppContext:
	frame = sys._getframe(1)

	while frame:
		if os.path.join('testingss', 'jobs') in frame.f_code.co_filename:
			return 'cli'
		if os.path.join('testingss', 'uis') in frame.f_code.co_filename:
			return 'ui'
		frame = frame.f_back
	return 'cli'
