from typing import List, Optional

from facefusion.hash_helper import create_hash
from facefusion.types import Face, FaceSet, FaceStore, VisionFrame

FACE_STORE : FaceStore =\
{
	'static_faces': {},
	'reference_faces': {}
}


def get_face_store() -> FaceStore:
	return FACE_STORE


def get_static_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	vision_area = crop_vision_area(vision_frame)
	vision_hash = create_hash(vision_area.tobytes())
	if vision_hash in FACE_STORE['static_faces']:
		return FACE_STORE['static_faces'][vision_hash]
	return None


def set_static_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	vision_area = crop_vision_area(vision_frame)
	vision_hash = create_hash(vision_area.tobytes())
	if vision_hash:
		FACE_STORE['static_faces'][vision_hash] = faces


def clear_static_faces() -> None:
	FACE_STORE['static_faces'].clear()


def get_reference_faces() -> Optional[FaceSet]:
	if FACE_STORE['reference_faces']:
		return FACE_STORE['reference_faces']
	return None


def append_reference_face(name : str, face : Face) -> None:
	if name not in FACE_STORE['reference_faces']:
		FACE_STORE['reference_faces'][name] = []
	FACE_STORE['reference_faces'][name].append(face)


def clear_reference_faces() -> None:
	FACE_STORE['reference_faces'].clear()


def crop_vision_area(vision_frame : VisionFrame) -> VisionFrame:
	height, width = vision_frame.shape[:2]
	center_y, center_x = height // 2, width // 2
	vision_area = vision_frame[center_y - 16 : center_y + 16, center_x - 16 : center_x + 16]
	return vision_area
