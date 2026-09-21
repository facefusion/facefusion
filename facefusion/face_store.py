import threading
from typing import List, Optional

from facefusion import store_creator
from facefusion.hash_helper import create_hash
from facefusion.session_manager import resolve_owner_id
from facefusion.types import Face, SessionId, Store, VisionFrame
from facefusion.vision import is_vision_frame

FACE_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(FACE_STORE, owner_id)


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


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(FACE_STORE, session_id)

