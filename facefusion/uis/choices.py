from typing import List

from facefusion.uis.types import JobManagerAction, JobRunnerAction

job_manager_actions : List[JobManagerAction] = [ 'job-create', 'job-submit', 'job-delete', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]
job_runner_actions : List[JobRunnerAction] = [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]

common_options : List[str] = [ 'keep-temp' ]

