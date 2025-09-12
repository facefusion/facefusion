from typing import List, Optional

from facefusion.hash_helper import create_hash
from facefusion.types import Face, FaceStore, VisionFrame

FACE_STORE : FaceStore =\
{
	'static_faces': {}
}


def get_face_store() -> FaceStore:
	return FACE_STORE


def get_static_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	vision_hash = create_hash(vision_frame.tobytes())
	return FACE_STORE.get('static_faces').get(vision_hash)


def set_static_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	vision_hash = create_hash(vision_frame.tobytes())
	if vision_hash:
		FACE_STORE['static_faces'][vision_hash] = faces


def clear_static_faces() -> None:
	FACE_STORE['static_faces'].clear()
