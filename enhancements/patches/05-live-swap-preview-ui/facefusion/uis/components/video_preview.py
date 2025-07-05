"""
Override for VideoPreview component to embed a live swap preview
with scrub-bar and playback controls.
"""

import threading
from facefusion.uis.components.video_preview import VideoPreview as BasePreview

class LiveSwapPreview(BasePreview):
    """
    Embeds a player that streams swapped frames in real time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preview_running = False
        # Slider to scrub through frames
        self.scrub_slider = self.create_slider("Frame", min_value=0, max_value=self.video_manager.total_frames)
        self.scrub_slider.on_change(self.on_slider_move)
        # Play/Pause button
        self.play_button = self.create_button("Play")
        self.play_button.on_click(self.toggle_playback)

    def start_preview(self):
        """
        Begin streaming swapped frames to the UI widget.
        Runs in a background thread to avoid blocking the UI.
        """
        if self._preview_running:
            return
        self._preview_running = True

        def _loop():
            for frame_idx, frame in self.video_manager.run_preview():
                if not self._preview_running:
                    break
                self.update_frame_display(frame)
                # Update slider without triggering event
                self.scrub_slider.set_value(frame_idx, silent=True)

        threading.Thread(target=_loop, daemon=True).start()

    def toggle_playback(self):
        """
        Toggle preview on/off.
        """
        if self._preview_running:
            self._preview_running = False
            self.play_button.set_label("Play")
        else:
            self.play_button.set_label("Pause")
            self.start_preview()

    def on_slider_move(self, frame_index: int):
        """
        Seek to a particular frame in the preview.
        """
        frame = self.video_manager.get_frame(frame_index)
        self.update_frame_display(frame)
"""