from typing import Optional, List
import hashlib

from facefusion.typing import Frame, Face, FaceStore

FACE_STORE: FaceStore =\
{
    'static_faces': {},
    'reference_faces': []
}


def get_static_faces(frame : Frame) -> Optional[List[Face]]:
    frame_hash = create_frame_hash(frame)
    if frame_hash in FACE_STORE['static_faces']:
        return FACE_STORE['static_faces'][frame_hash]
    return None


def set_static_faces(frame : Frame, faces : List[Face]) -> None:
    frame_hash = create_frame_hash(frame)
    if frame_hash:
        FACE_STORE['static_faces'][frame_hash] = faces


def clear_static_faces() -> None:
    FACE_STORE['static_faces'] = {}


def create_frame_hash(frame: Frame) -> Optional[str]:
    return hashlib.sha1(frame.tobytes()).hexdigest() if frame.any() else None


def get_reference_faces() -> Optional[List[Face]]:
    if FACE_STORE['reference_faces']:
        return FACE_STORE['reference_faces']
    return None


def append_reference_face(face : Face) -> None:
    FACE_STORE['reference_faces'].append(face)


def clear_reference_faces() -> None:
    FACE_STORE['reference_faces'] = []
