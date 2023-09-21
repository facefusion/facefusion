from typing import List

from facefusion.uis.typing import WebcamMode

settings : List[str] = [ 'keep-fps', 'keep-temp', 'skip-audio', 'skip-download' ]
webcam_mode : List[WebcamMode] = [ 'inline', 'stream_udp', 'stream_v4l2' ]
webcam_resolution : List[str] = [ '320x240', '640x480', '1280x720', '1920x1080', '2560x1440', '3840x2160' ]
