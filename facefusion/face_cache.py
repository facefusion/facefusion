from typing import Optional, List, Dict
import hashlib

from facefusion.typing import Frame, Face

FACES_CACHE : Dict[str, List[Face]] = {}


def get_faces_cache(frame : Frame) -> Optional[List[Face]]:
	frame_hash = create_frame_hash(frame)
	if frame_hash in FACES_CACHE:
		return FACES_CACHE[frame_hash]
	return None


def set_faces_cache(frame : Frame, faces : List[Face]) -> None:
	frame_hash = create_frame_hash(frame)
	if frame_hash:
		FACES_CACHE[frame_hash] = faces


def clear_faces_cache() -> None:
	global FACES_CACHE

	FACES_CACHE = {}


def create_frame_hash(frame : Frame) -> Optional[str]:
	return hashlib.sha256(frame.tobytes()).hexdigest() if frame is not None else None
