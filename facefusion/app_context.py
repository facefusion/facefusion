import inspect

from facefusion.typing import AppContext


def detect_app_context() -> AppContext:
	for stack in inspect.stack():
		if 'facefusion/jobs' in stack.filename:
			return 'cli'
		if 'facefusion/uis' in stack.filename:
			return 'ui'
	return 'cli'
