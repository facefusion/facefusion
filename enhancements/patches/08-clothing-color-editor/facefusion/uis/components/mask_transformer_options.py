"""
Override MaskTransformerOptionsPanel to provide segmentation overlay
and HSL color sliders for clothing regions.
"""

from facefusion.uis.components.mask_transformer_options import MaskTransformerOptionsPanel as BasePanel

class ClothingColorEditorPanel(BasePanel):
    """
    Adds segmentation overlay toggle and Hue/Saturation/Lightness sliders
    for color-adjusting clothing regions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segmentation_toggle = self.create_toggle(
            "Show Segmentation Overlay", default=False
        )
        self.hue_slider = self.create_slider(
            "Hue", min_value=-180, max_value=180, default=0
        )
        self.saturation_slider = self.create_slider(
            "Saturation", min_value=-100, max_value=100, default=0
        )
        self.lightness_slider = self.create_slider(
            "Lightness", min_value=-100, max_value=100, default=0
        )
        self.apply_button = self.create_button("Apply Color Adjustments")
        self.apply_button.on_click(self.on_apply_click)

    def on_apply_click(self):
        """
        Apply current HSL adjustments to the selected clothing regions.
        """
        hue = self.hue_slider.value
        sat = self.saturation_slider.value
        light = self.lightness_slider.value
        # TODO: implement application of HSL adjustments to self.regions
