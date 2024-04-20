#!/usr/bin/env python3

from facefusion import core
from pathlib import Path, PurePath
import os
import time
import multiprocessing as mp


def start(target: str, source: str, output: str) -> None:
	time1 = time.time()
	ROOT_DIR = os.getcwd()
	core.cli(os.path.join(ROOT_DIR, target),
			[os.path.join(ROOT_DIR, source)],
			 os.path.join(f'{ROOT_DIR}/output', output + PurePath(source).suffix))
	print(f"{time.time() - time1} sec")


if __name__ == '__main__':
	time1 = time.time()
	target = 's-3.webp'
	source = '2.jpg'

	for i in range(1):
		p = mp.Process(target=start, args=(target, source, str(i)))
		p.start()

	p.join()

	print(f"Время выполнения: {time.time() - time1} sec!!!!")
