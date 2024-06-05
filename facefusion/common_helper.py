import os
import multiprocessing
from typing import List, Any
import platform


def create_metavar(ranges : List[Any]) -> str:
	return '[' + str(ranges[0]) + '-' + str(ranges[-1]) + ']'


def create_int_range(start : int, end : int, step : int) -> List[int]:
	int_range = []
	current = start

	while current <= end:
		int_range.append(current)
		current += step
	return int_range


def create_float_range(start : float, end : float, step : float) -> List[float]:
	float_range = []
	current = start

	while current <= end:
		float_range.append(round(current, 2))
		current = round(current + step, 2)
	return float_range


def is_linux() -> bool:
	return to_lower_case(platform.system()) == 'linux'


def is_macos() -> bool:
	return to_lower_case(platform.system()) == 'darwin'


def is_windows() -> bool:
	return to_lower_case(platform.system()) == 'windows'


def to_lower_case(__string__ : Any) -> str:
	return str(__string__).lower()


def get_first(__list__ : Any) -> Any:
	return next(iter(__list__), None)


def get_cpu_thread_count():
    try:
        cpu_count_os = os.cpu_count()
        cpu_count_mp = multiprocessing.cpu_count()
        if cpu_count_os is not None:
            print(f"Number of CPU threads (using os): {cpu_count_os}")
        else:
            print("os.cpu_count() returned None")

        if cpu_count_mp is not None:
            print(f"Number of CPU threads (using multiprocessing): {cpu_count_mp}")
        else:
            print("multiprocessing.cpu_count() returned None")

        # Ensure both methods return the same result
        if cpu_count_os == cpu_count_mp:
            return cpu_count_os
        else:
            print("Warning: os.cpu_count() and multiprocessing.cpu_count() returned different results")
            return min(cpu_count_os, cpu_count_mp)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
