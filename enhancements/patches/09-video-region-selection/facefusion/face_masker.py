"""
Override for FaceMasker to track arbitrary region masks across frames.
"""

from typing import Dict, List, Tuple
from facefusion.face_masker import FaceMasker as BaseMasker

class RegionTracker(BaseMasker):
    """
    Extends BaseMasker: allows adding named polygon regions and
    applies them persistently to every frame.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # regions[name] = list of (x,y) tuples
        self.regions: Dict[str, List[Tuple[int, int]]] = {}

    def add_region(self, name: str, polygon: List[Tuple[int, int]]) -> None:
        """
        Register a new polygon region under a name.
        """
        self.regions[name] = polygon

    def clear_regions(self) -> None:
        """
        Remove all defined regions.
        """
        self.regions.clear()

    def apply_mask(self, frame):
        """
        Apply all registered regions as masks on the frame.
        """
        for poly in self.regions.values():
            # TODO: fill polygon on mask and composite with frame
            pass
        # Fallback to face-based masking if no regions
        return super().apply_mask(frame)
