#!/usr/bin/env python3

from facefusion import core
from pathlib import Path, PurePath
import os
import time
import multiprocessing as mp

ROOT_DIR = os.getcwd()


def start(target: str, source: str, output: str) -> None:
	time_ = time.time()

	core.cli(os.path.join(ROOT_DIR, target),
			[os.path.join(ROOT_DIR, source)],
			 os.path.join(ROOT_DIR, output))

	print(f"{time.time() - time_} sec")


if __name__ == '__main__':
	time1 = time.time()
	target = 'temp/target_2720.jpg'
	source = 'temp/source_2720.png'

	start(target, source, '1')

	print(f"Время выполнения: {time.time() - time1} sec!!!!")
