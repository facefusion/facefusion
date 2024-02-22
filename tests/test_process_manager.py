from typing import List

from facefusion.process_manager import set_process_state, is_processing, is_stopping, is_pending, start, stop, pause, manage
from facefusion.typing import QueuePayload


def test_start() -> None:
	set_process_state('pending')
	start()

	assert is_processing()


def test_stop() -> None:
	set_process_state('processing')
	stop()

	assert is_stopping()


def test_pause() -> None:
	set_process_state('processing')
	pause()

	assert is_pending()


def test_manage() -> None:
	queue_payloads =\
	[
		{
			'frame_number': 1,
			'frame_path': '.assets/examples/source.jpg'
		}
	]
	start()

	for _ in manage(queue_payloads):
		assert is_processing()
	assert is_pending()
