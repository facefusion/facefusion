"""
PersistentFaceStore with history & favorites.
"""

from facefusion.face_store import FaceStore
from datetime import datetime

class PersistentFaceStore(FaceStore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_max = 50
        self.history = []
        self.favorites = set()

    def add_face(self, face_id: str, thumbnail_path: str) -> None:
        self.history = [e for e in self.history if e[0] != face_id]
        now = datetime.now().timestamp()
        self.history.append((face_id, now, thumbnail_path))
        if len(self.history) > self.history_max:
            self.history.pop(0)

    def pin_favorite(self, face_id: str) -> None:
        if face_id in self.favorites:
            self.favorites.remove(face_id)
        else:
            self.favorites.add(face_id)
