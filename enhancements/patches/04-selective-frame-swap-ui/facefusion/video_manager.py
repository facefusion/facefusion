"""
Override for VideoManager to support selective frame swapping.
"""

from facefusion.video_manager import VideoManager as BaseVideoManager

class VideoManager(BaseVideoManager):
    """
    Extended VideoManager that respects start/end frame settings.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_frame: int | None = None
        self.end_frame: int | None = None

    def set_frame_range(self, start: int, end: int) -> None:
        """
        Define the inclusive frame range to process.
        """
        self.start_frame = start
        self.end_frame = end

    def run(self, *args, **kwargs):
        """
        Override run to optionally trim the video before processing.
        """
        if self.start_frame is not None or self.end_frame is not None:
            # TODO: trim input video to frames [start_frame, end_frame]
            # e.g. using FFmpeg or slicing frame list
            pass
        return super().run(*args, **kwargs)
