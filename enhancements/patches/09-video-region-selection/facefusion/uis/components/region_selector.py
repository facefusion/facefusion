"""
Override UI panel to draw and manage region selections.
"""

from facefusion.uis.components.trim_frame import TrimFramePanel as BasePanel

class RegionSelectorPanel(BasePanel):
    """
    Provides tools to draw, name, and clear polygon regions on frames.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: add drawing canvas, region list, and clear button

    def get_regions(self):
        """
        Return currently defined regions as {name: polygon}.
        """
        # TODO: return actual region dict
        return {}
