"""
Override TrimFrame component to render start/end sliders and preview button.
"""

from facefusion.uis.components.trim_frame import TrimFramePanel as BaseTrimPanel

class TrimFramePanel(BaseTrimPanel):
    """
    Adds range sliders and a Preview Trim button.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add sliders for start and end frames (assumes create_slider exists)
        self.start_slider = self.create_slider("Start Frame", min_value=0, max_value=self.video_length)
        self.end_slider = self.create_slider("End Frame", min_value=0, max_value=self.video_length)
        # Add a preview button (assumes create_button exists)
        self.preview_button = self.create_button("Preview Trim")
        self.preview_button.on_click(self.on_preview_click)

    def on_preview_click(self):
        """
        Handle Preview Trim button click to show trimmed segment.
        """
        start = self.start_slider.value
        end = self.end_slider.value
        # TODO: implement preview logic, e.g.:
        # self.video_manager.set_frame_range(start, end)
        # self.video_manager.run_preview()
