from facefusion.process_manager import end, is_pending, is_processing, is_stopping, set_process_state, start, stop


def test_start() -> None:
	set_process_state('pending')
	start()

	assert is_processing()


def test_stop() -> None:
	set_process_state('processing')
	stop()

	assert is_stopping()


def test_end() -> None:
	set_process_state('processing')
	end()

	assert is_pending()
