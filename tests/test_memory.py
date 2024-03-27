import platform

from facefusion.memory import limit_system_memory


def test_limit_system_memory() -> None:
	assert limit_system_memory(4) is True
	if platform.system().lower() == 'darwin' or platform.system().lower() == 'linux':
		assert limit_system_memory(1024) is False
