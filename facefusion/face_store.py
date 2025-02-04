from typing import Optional, List
import hashlib
import numpy

from facefusion.typing import VisionFrame, Face, FaceStore, FaceSet

FACE_STORE: FaceStore =\
{
	'static_faces': {},
	'reference_faces': {}
}


def get_static_faces(vision_frame : VisionFrame) -> Optional[List[Face]]:
	frame_hash = create_frame_hash(vision_frame)
	if frame_hash in FACE_STORE['static_faces']:
		return FACE_STORE['static_faces'][frame_hash]
	return None


def set_static_faces(vision_frame : VisionFrame, faces : List[Face]) -> None:
	frame_hash = create_frame_hash(vision_frame)
	if frame_hash:
		FACE_STORE['static_faces'][frame_hash] = faces


def clear_static_faces() -> None:
	FACE_STORE['static_faces'] = {}


def create_frame_hash(vision_frame : VisionFrame) -> Optional[str]:
	return hashlib.sha1(vision_frame.tobytes()).hexdigest() if numpy.any(vision_frame) else None


def get_reference_faces() -> Optional[FaceSet]:
	if FACE_STORE['reference_faces']:
		return FACE_STORE['reference_faces']
	return None


def append_reference_face(name : str, face : Face) -> None:
	if name not in FACE_STORE['reference_faces']:
		FACE_STORE['reference_faces'][name] = []
	FACE_STORE['reference_faces'][name].append(face)


def clear_reference_faces() -> None:
	FACE_STORE['reference_faces'] = {}
