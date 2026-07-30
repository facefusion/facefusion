import threading
from typing import List, Optional

from facefusion.hash_helper import create_hash
from facefusion.types import Face, FaceStore, VisionFrame
from facefusion.vision import is_vision_frame

FACE_STORE : FaceStore = {}


def get_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())

		if FACE_STORE.get(vision_hash):
			return FACE_STORE.get(vision_hash).get('faces')

	return None


def set_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())
		FACE_STORE.setdefault(vision_hash,
		{
			'lock': threading.Lock()
		})['faces'] = faces


def resolve_lock(vision_frame : VisionFrame) -> threading.Lock:
	if is_vision_frame(vision_frame):
		vision_hash = create_hash(vision_frame.tobytes())
		return FACE_STORE.setdefault(vision_hash,
		{
			'lock': threading.Lock()
		}).get('lock')
	return threading.Lock()


def clear_faces() -> None:
	FACE_STORE.clear()
