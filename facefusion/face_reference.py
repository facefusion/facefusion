from typing import Optional

from facefusion.typing import Face

FACE_REFERENCE = None


def get_face_reference() -> Optional[Face]:
	return FACE_REFERENCE


def set_face_reference(face : Face) -> None:
	global FACE_REFERENCE

	FACE_REFERENCE = face


def clear_face_reference() -> None:
	global FACE_REFERENCE

	FACE_REFERENCE = None
