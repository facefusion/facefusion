from datetime import datetime, timedelta

from facefusion.date_helper import describe_time_ago


def get_time_ago(days : int, hours : int, minutes : int) -> datetime:
	previous_time = datetime.now() - timedelta(days = days, hours = hours, minutes = minutes)
	return previous_time.astimezone()


def test_describe_time_ago() -> None:
	assert describe_time_ago(get_time_ago(0, 0, 0)) == 'just now'
	assert describe_time_ago(get_time_ago(0, 0, 5)) == '5 minutes ago'
	assert describe_time_ago(get_time_ago(0, 5, 10)) == '5 hours and 10 minutes ago'
	assert describe_time_ago(get_time_ago(5, 10, 15)) == '5 days, 10 hours and 15 minutes ago'
