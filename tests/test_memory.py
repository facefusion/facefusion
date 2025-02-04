from facefusion.common_helper import is_linux, is_macos
from facefusion.memory import limit_system_memory


def test_limit_system_memory() -> None:
	assert limit_system_memory(4) is True
	if is_linux() or is_macos():
		assert limit_system_memory(1024) is False
