from typing import Dict, List

from facefusion.types import Color, WebcamMode
from facefusion.uis.types import JobManagerAction, JobRunnerAction, PreviewMode

job_manager_actions : List[JobManagerAction] = [ 'job-create', 'job-submit', 'job-delete', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]
job_runner_actions : List[JobRunnerAction] = [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]

common_options : List[str] = [ 'keep-temp' ]

preview_modes : List[PreviewMode] = [ 'default', 'frame-by-frame', 'face-by-face' ]
preview_resolutions : List[str] = [ '512x512', '768x768', '1024x1024' ]

webcam_modes : List[WebcamMode] = [ 'inline', 'udp', 'v4l2' ]
webcam_resolutions : List[str] = [ '320x240', '640x480', '800x600', '1024x768', '1280x720', '1280x960', '1920x1080' ]

background_remover_colors : Dict[str, Color] =\
{
	'red' : (255, 0, 0, 255),
	'green' : (0, 255, 0, 255),
	'blue' : (0, 0, 255, 255),
	'black' : (0, 0, 0, 255),
	'white' : (255, 255, 255, 255),
	'alpha' : (0, 0, 0, 0)
}
