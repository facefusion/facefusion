import threading
from contextvars import copy_context
from time import sleep
from typing import List, Optional

from facefusion import store_creator
from facefusion.hash_helper import create_hash
from facefusion.session_manager import resolve_owner_id, validate_api_session
from facefusion.types import Face, Store, VisionFrame
from facefusion.vision import is_vision_frame

FACE_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(FACE_STORE, owner_id)


def listen() -> None:
	threading.Thread(
		target = copy_context().run,
		args = (conditional_destroy,),
		daemon = True
	).start()


def get_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	owner_id = resolve_owner_id()
	face_store = store_creator.get_content(FACE_STORE, owner_id)

	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())

		if face_store.get(vision_hash):
			return face_store.get(vision_hash).get('faces')

	return None


def set_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	owner_id = resolve_owner_id()
	face_store = store_creator.get_content(FACE_STORE, owner_id)

	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())
		face_store.setdefault(vision_hash,
		{
			'lock': threading.Lock()
		})['faces'] = faces


def resolve_lock(vision_frame : VisionFrame) -> threading.Lock:
	owner_id = resolve_owner_id()
	face_store = store_creator.get_content(FACE_STORE, owner_id)

	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())
		return face_store.setdefault(vision_hash,
		{
			'lock': threading.Lock()
		}).get('lock')
	return threading.Lock()


def clear() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(FACE_STORE, owner_id)


def conditional_destroy() -> None:
	owner_id = resolve_owner_id()

	while validate_api_session(owner_id):
		sleep(10)

	store_creator.delete_content(FACE_STORE, owner_id)
