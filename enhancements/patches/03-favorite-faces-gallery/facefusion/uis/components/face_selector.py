"""
MultiFaceSelector toggle.
"""

from facefusion.uis.components.face_selector import FaceSelector

class MultiFaceSelector(FaceSelector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_mode = False

    def toggle_mode(self) -> bool:
        self.multi_mode = not self.multi_mode
        return self.multi_mode
