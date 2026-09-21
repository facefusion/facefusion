import threading
from contextvars import copy_context
from time import sleep
from typing import Optional

from facefusion import rtc, store_creator
from facefusion.session_manager import resolve_owner_id, validate_api_session
from facefusion.types import RtcPeer, Store

RTC_STORE : Store = store_creator.create_store(None)


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(RTC_STORE, owner_id)


def listen() -> None:
	threading.Thread(
		target = copy_context().run,
		args = (conditional_destroy,),
		daemon = True
	).start()


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


def conditional_destroy() -> None:
	owner_id = resolve_owner_id()

	while validate_api_session(owner_id):
		sleep(10)

	rtc_peer = store_creator.get_content(RTC_STORE, owner_id)

	if rtc_peer:
		rtc.delete_peer(rtc_peer)

	store_creator.delete_content(RTC_STORE, owner_id)
