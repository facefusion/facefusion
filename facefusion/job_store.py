from argparse import ArgumentParser
from typing import Optional, List

from facefusion.typing import JobArgs, JobArgsRegistry

ARGS_STORE : JobArgsRegistry =\
{
	'job': [],
	'step': []
}


def register_job_args(step_args : List[str]) -> None:
	for step_arg in step_args:
		ARGS_STORE['step'].append(step_arg)


def register_step_args(job_args : List[str]) -> None:
	for job_arg in job_args:
		ARGS_STORE['job'].append(job_arg)


def find_argument_alias(program : ArgumentParser, argument : str) -> Optional[str]:
	for action in program._actions:
		if argument in action.option_strings:
			return action.dest
	return None


def filter_job_args(program : ArgumentParser) -> JobArgs: # todo: this is not used yet
	args = program.parse_args()
	step_args_keys = {find_argument_alias(program, arg) for arg in ARGS_STORE['job']}
	step_args = {}

	for key, value in vars(args).items():
		if key in step_args_keys:
			step_args[key] = value
	return step_args


def filter_step_args(program : ArgumentParser) -> JobArgs: # todo: join with filter job args
	args = program.parse_args()
	step_args_keys = {find_argument_alias(program, arg) for arg in ARGS_STORE['step']}
	step_args = {}

	for key, value in vars(args).items():
		if key in step_args_keys:
			step_args[key] = value
	return step_args
