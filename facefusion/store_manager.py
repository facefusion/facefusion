import threading
from functools import partial
from time import sleep
from types import ModuleType
from typing import List

from facefusion import content_store, face_store, inference_manager, process_manager, rtc_store, session_manager, state_manager, video_manager
from facefusion.apis import asset_store
from facefusion.types import SessionId


def get_stores() -> List[ModuleType]:
	return [ state_manager, asset_store, content_store, face_store, inference_manager, process_manager, rtc_store, video_manager ]


def observe_session(session_id : SessionId) -> None:
	threading.Thread(
		target = partial(conditional_destroy, session_id),
		daemon = True
	).start()


def conditional_destroy(session_id : SessionId) -> None:
	while session_manager.validate_api_session(session_id):
		sleep(10)

	destroy(session_id)


def destroy(session_id : SessionId) -> None:
	for store in get_stores():
		store.destroy(session_id)
