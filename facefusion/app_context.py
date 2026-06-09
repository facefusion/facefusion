import os
import sys

from facefusion.types import AppContext


def detect_app_context() -> AppContext:
	jobs_path = os.path.join('facefusion', 'jobs')
	apis_path = os.path.join('facefusion', 'apis')
	frame = sys._getframe(1)

	while frame:
		if jobs_path in frame.f_code.co_filename:
			return 'cli'
		if apis_path in frame.f_code.co_filename:
			return 'api'
		frame = frame.f_back
	return 'cli'
