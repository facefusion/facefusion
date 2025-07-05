"""
Override for SmartSwapMapper UI component.
"""

from facefusion.uis.components.swap_mapper import SwapMapper
from facefusion.face_landmarker import LandmarkMappingHelper

class SmartSwapMapper(SwapMapper):
    """
    Extends SwapMapper with 3D auto-alignment and fine-tune controls.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = LandmarkMappingHelper()
        # TODO: add 3D view widget and alignment buttons

    def auto_align(self):
        """
        Compute optimal 3D mapping based on detected landmarks.
        """
        mapping = self.helper.compute_3d_mapping(self.source_landmarks, self.target_landmarks)
        self.set_mapping(mapping)

    def fine_tune(self, adjustments):
        """
        Apply user adjustments to the current mapping.
        """
        self.helper.apply_adjustments(self.current_mapping, adjustments)
