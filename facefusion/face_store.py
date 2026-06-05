from typing import List, Optional

from facefusion.hash_helper import create_hash
from facefusion.types import Face, FaceStore, VisionFrame

FACE_STORE : FaceStore = {}


def get_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	vision_hash = create_hash(vision_frame.tobytes())
	return FACE_STORE.get(vision_hash)


def set_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	vision_hash = create_hash(vision_frame.tobytes())
	if vision_hash:
		FACE_STORE[vision_hash] = faces


def clear_faces() -> None:
	FACE_STORE.clear()
