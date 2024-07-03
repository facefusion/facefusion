from typing import Tuple, Optional
from datetime import datetime, timedelta
from facefusion import wording


def get_current_datetime() -> str:
	return datetime.now().astimezone().isoformat()


def get_datetime_components(date_time: timedelta) -> Tuple[int, int, int, int]:
	total_seconds = int(date_time.total_seconds())
	days, hours = divmod(total_seconds, 86400)
	hours, minutes = divmod(hours, 3600)
	minutes, seconds = divmod(minutes, 60)
	return days, hours, minutes, seconds


def describe_time_ago(date_time: str) -> Optional[str]:
	date_time_parsed = datetime.fromisoformat(date_time)
	date_time_current = datetime.now(date_time_parsed.tzinfo)
	date_time_difference = date_time_current - date_time_parsed
	days, hours, minutes, _ = get_datetime_components(date_time_difference)

	if timedelta(days = 1) < date_time_difference:
		return wording.get('time_ago_days').format(days = days, hours = hours, minutes = minutes)
	if timedelta(hours = 1) < date_time_difference:
		return wording.get('time_ago_hours').format(hours = hours, minutes = minutes)
	if timedelta(minutes = 1) < date_time_difference:
		return wording.get('time_ago_minutes').format(minutes = minutes)
	return wording.get('time_ago_now')
