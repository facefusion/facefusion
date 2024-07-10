from typing import List

from facefusion.uis.typing import JobManagerAction, JobRunnerAction, WebcamMode

job_manager_actions : List[JobManagerAction] = [ 'job-create', 'job-submit', 'job-delete', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]
job_runner_actions : List[JobRunnerAction] = [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]

common_options : List[str] = [ 'keep-temp', 'skip-audio', 'skip-download' ]

webcam_modes : List[WebcamMode] = [ 'inline', 'udp', 'v4l2' ]
webcam_resolutions : List[str] = [ '320x240', '640x480', '800x600', '1024x768', '1280x720', '1280x960', '1920x1080', '2560x1440', '3840x2160' ]
