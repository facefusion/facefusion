from typing import Optional, List

from facefusion.typing import Face

FACE_REFERENCES : List[Face] = []


def get_face_references() -> Optional[List[Face]]:
	if FACE_REFERENCES:
		return FACE_REFERENCES
	return None


def append_face_reference(face : Face) -> None:
	global FACE_REFERENCES

	FACE_REFERENCES.append(face)


def clear_face_references() -> None:
	global FACE_REFERENCES

	FACE_REFERENCES = []
