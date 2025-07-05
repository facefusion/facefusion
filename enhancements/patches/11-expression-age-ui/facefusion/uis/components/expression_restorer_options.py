"""
Override for ExpressionRestorerOptionsPanel to add live parameter sliders.
"""

from facefusion.uis.components.expression_restorer_options import ExpressionRestorerOptionsPanel as BasePanel

class ExpressionRestorerOptionsPanel(BasePanel):
    """
    Live sliders for smile boost and eyebrow raise, with preview toggle.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.smile_slider = self.create_slider("Smile Boost", 0, 100, 50)
        self.eyebrow_slider = self.create_slider("Eyebrow Raise", 0, 100, 50)
        self.preview_toggle = self.create_toggle("Live Preview", default=True)
        self.smile_slider.on_change(self.on_change)
        self.eyebrow_slider.on_change(self.on_change)
        self.preview_toggle.on_change(self.on_toggle)

    def on_change(self, value):
        # TODO: update preview in real time
        pass

    def on_toggle(self, enabled):
        # TODO: enable/disable live preview
        pass
