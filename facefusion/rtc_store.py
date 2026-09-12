from typing import Optional

from facefusion import rtc, store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import RtcPeer, Store

RTC_STORE : Store = store_creator.create_store(None)


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(RTC_STORE, owner_id)


def has_peer() -> bool:
	owner_id = resolve_owner_id()

	return bool(store_creator.get_content(RTC_STORE, owner_id))


def get_peer() -> Optional[RtcPeer]:
	owner_id = resolve_owner_id()

	return store_creator.get_content(RTC_STORE, owner_id)


def set_peer(rtc_peer : RtcPeer) -> None:
	owner_id = resolve_owner_id()
	store_creator.set_content(RTC_STORE, owner_id, rtc_peer)


def delete_peer() -> None:
	owner_id = resolve_owner_id()
	rtc_peer = store_creator.get_content(RTC_STORE, owner_id)

	if rtc_peer:
		rtc.delete_peer(rtc_peer)
		store_creator.init_content(RTC_STORE, owner_id)
