import platform

if platform.system().lower() == 'windows':
	import ctypes
else:
	import resource


def limit_system_memory(max_system_memory : int = 1) -> bool:
	if platform.system().lower() == 'darwin':
		max_system_memory = max_system_memory * 1024 ** 6
	else:
		max_system_memory = max_system_memory * 1024 ** 3
	try:
		if platform.system().lower() == 'windows':
			ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(max_system_memory), ctypes.c_size_t(max_system_memory)) # type: ignore[attr-defined]
		else:
			resource.setrlimit(resource.RLIMIT_DATA, (max_system_memory, max_system_memory))
		return True
	except Exception:
		return False
