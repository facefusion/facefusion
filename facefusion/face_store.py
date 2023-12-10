from typing import Optional, List, Dict
import hashlib

from facefusion.typing import Frame, Face

STATIC_FACES : Dict[str, List[Face]] = {}
REFERENCE_FACES : List[Face] = []


def get_static_faces(frame : Frame) -> Optional[List[Face]]:
	frame_hash = create_frame_hash(frame)
	if frame_hash in STATIC_FACES:
		return STATIC_FACES[frame_hash]
	return None


def set_static_faces(frame : Frame, faces : List[Face]) -> None:
	frame_hash = create_frame_hash(frame)
	if frame_hash:
		STATIC_FACES[frame_hash] = faces


def clear_static_faces() -> None:
	global STATIC_FACES

	STATIC_FACES = {}


def create_frame_hash(frame : Frame) -> Optional[str]:
	return hashlib.sha1(frame.tobytes()).hexdigest() if frame.any() else None


def get_reference_faces() -> Optional[List[Face]]:
	if REFERENCE_FACES:
		return REFERENCE_FACES
	return None


def append_reference_face(face : Face) -> None:
	global REFERENCE_FACES

	REFERENCE_FACES.append(face)


def clear_reference_faces() -> None:
	global REFERENCE_FACES

	REFERENCE_FACES = []
