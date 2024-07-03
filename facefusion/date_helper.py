from typing import Tuple, Optional
from datetime import datetime, timedelta
from facefusion import wording


def get_current_datetime() -> str:
	return datetime.now().astimezone().isoformat()


def get_datetime_components(delta: timedelta) -> Tuple[int, int, int, int]:
	total_seconds = int(delta.total_seconds())
	days, hours = divmod(total_seconds, 86400)
	hours, minutes = divmod(hours, 3600)
	minutes, seconds = divmod(minutes, 60)
	return days, hours, minutes, seconds


def describe_time_ago(date_time: str) -> Optional[str]:
	datetime_parsed = datetime.fromisoformat(date_time)
	datetime_current = datetime.now(datetime_parsed.tzinfo)
	datetime_difference = datetime_current - datetime_parsed
	days, hours, minutes, _ = get_datetime_components(datetime_difference)

	if timedelta(days = 1) < datetime_difference:
		return wording.get('time_ago_days').format(days = days, hours = hours, minutes = minutes)
	if timedelta(hours = 1) < datetime_difference:
		return wording.get('time_ago_hours').format(hours = hours, minutes = minutes)
	if timedelta(minutes = 1) < datetime_difference:
		return wording.get('time_ago_minutes').format(minutes = minutes)
	return wording.get('time_ago_now')
