from datetime import datetime, timedelta
from facefusion.date_helper import describe_time_ago


def get_previous_time(days : int, hours : int, minutes : int) -> str:
	previous_time = datetime.now() - timedelta(days = days, hours = hours, minutes = minutes)
	return previous_time.astimezone().isoformat()


def test_describe_time_ago() -> None:
	date_time = get_previous_time(0, 0, 0)
	assert describe_time_ago(date_time) == 'Just now'

	date_time = get_previous_time(0, 0, 5)
	assert describe_time_ago(date_time) == '5 minutes ago'

	date_time = get_previous_time(0, 5, 10)
	assert describe_time_ago(date_time) == '5 hours and 10 minutes ago'

	date_time = get_previous_time(5, 10, 15)
	assert describe_time_ago(date_time) == '5 days, 10 hours and 15 minutes ago'
