from datetime import datetime, timedelta
from time import time

from facefusion.time_helper import calculate_end_time, describe_time_ago, get_current_date_time, split_time_delta


def get_time_ago(days : int, hours : int, minutes : int) -> datetime:
	time_ago = datetime.now() - timedelta(days = days, hours = hours, minutes = minutes)
	return time_ago.astimezone()


def test_get_current_date_time() -> None:
	assert get_current_date_time().utcoffset() == datetime.now().astimezone().utcoffset()
	assert get_current_date_time() - datetime.now().astimezone() < timedelta(seconds = 1)


def test_calculate_end_time() -> None:
	assert calculate_end_time(time()) == 0.0
	assert calculate_end_time(time() - 2) == 2.0
	assert calculate_end_time(time() - 1.234) in [ 1.23, 1.24 ]


def test_split_time_delta() -> None:
	assert split_time_delta(timedelta()) == (0, 0, 0, 0)
	assert split_time_delta(timedelta(seconds = 59)) == (0, 0, 0, 59)
	assert split_time_delta(timedelta(minutes = 10, seconds = 30)) == (0, 0, 10, 30)
	assert split_time_delta(timedelta(hours = 25)) == (1, 1, 0, 0)
	assert split_time_delta(timedelta(days = 1, hours = 5, minutes = 10, seconds = 30)) == (1, 5, 10, 30)


def test_describe_time_ago() -> None:
	assert describe_time_ago(get_time_ago(0, 0, 0)) == 'just now'
	assert describe_time_ago(get_time_ago(0, 0, 1)) == '1 minutes ago'
	assert describe_time_ago(get_time_ago(0, 0, 10)) == '10 minutes ago'
	assert describe_time_ago(get_time_ago(0, 1, 0)) == '1 hours and 0 minutes ago'
	assert describe_time_ago(get_time_ago(0, 5, 10)) == '5 hours and 10 minutes ago'
	assert describe_time_ago(get_time_ago(1, 0, 0)) == '1 days, 0 hours and 0 minutes ago'
	assert describe_time_ago(get_time_ago(1, 5, 10)) == '1 days, 5 hours and 10 minutes ago'
