"""
FavoriteMemoryPanel UI logic.
"""

from facefusion.uis.components.memory import MemoryPanel
from facefusion.face_store import PersistentFaceStore

class FavoriteMemoryPanel(MemoryPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = PersistentFaceStore()
        self.selected = []
        self.build_ui()

    def build_ui(self):
        self.clear_thumbnails()
        for fid, _, thumb in self.store.history:
            self.add_thumbnail(fid, thumb)

    def on_click(self, face_id):
        self.selected = [face_id]
