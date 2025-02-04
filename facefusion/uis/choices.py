from typing import List

from facefusion.uis.typing import WebcamMode

common_options : List[str] = [ 'keep-temp', 'skip-audio', 'skip-download' ]
webcam_modes : List[WebcamMode] = [ 'inline', 'udp', 'v4l2' ]
webcam_resolutions : List[str] = [ '320x240', '640x480', '800x600', '1024x768', '1280x720', '1280x960', '1920x1080', '2560x1440', '3840x2160' ]
