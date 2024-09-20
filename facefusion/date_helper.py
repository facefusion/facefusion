from datetime import datetime, timedelta
from typing import Optional, Tuple

from facefusion import wording


def get_current_date_time() -> datetime:
	return datetime.now().astimezone()


def split_time_delta(time_delta : timedelta) -> Tuple[int, int, int, int]:
	days, hours = divmod(time_delta.total_seconds(), 86400)
	hours, minutes = divmod(hours, 3600)
	minutes, seconds = divmod(minutes, 60)
	return int(days), int(hours), int(minutes), int(seconds)


def describe_time_ago(date_time : datetime) -> Optional[str]:
	time_ago = datetime.now(date_time.tzinfo) - date_time
	days, hours, minutes, _ = split_time_delta(time_ago)

	if timedelta(days = 1) < time_ago:
		return wording.get('time_ago_days').format(days = days, hours = hours, minutes = minutes)
	if timedelta(hours = 1) < time_ago:
		return wording.get('time_ago_hours').format(hours = hours, minutes = minutes)
	if timedelta(minutes = 1) < time_ago:
		return wording.get('time_ago_minutes').format(minutes = minutes)
	return wording.get('time_ago_now')
