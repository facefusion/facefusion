"""
Override for AgeModifierOptionsPanel to add intensity slider and before/after toggle.
"""

from facefusion.uis.components.age_modifier_options import AgeModifierOptionsPanel as BasePanel

class AgeModifierOptionsPanel(BasePanel):
    """
    Slider for age intensity and a before/after preview toggle.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intensity_slider = self.create_slider("Intensity", 0, 100, 50)
        self.before_after_toggle = self.create_toggle("Before/After", default=False)
        self.intensity_slider.on_change(self.update_preview)
        self.before_after_toggle.on_change(self.toggle_view)

    def update_preview(self, value):
        # TODO: refresh preview with new intensity
        pass

    def toggle_view(self, show_before):
        # TODO: swap between before and after images
        pass
