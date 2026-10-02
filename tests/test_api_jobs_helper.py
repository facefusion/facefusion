from typing import Iterator

import pytest

from facefusion import session_context, state_manager
from facefusion.apis import asset_store
from facefusion.apis.jobs_helper import capture_output_asset
from facefusion.download import conditional_download
from facefusion.jobs.job_manager import add_step, clear_jobs, create_job, init_jobs
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	asset_store.delete_assets()
	clear_jobs(get_test_jobs_directory())
	init_jobs(state_manager.get_jobs_path())

	yield

	session_context.set_session_id(local_id)


def test_capture_output_asset() -> None:
	capture_output_asset('job-test-unknown')

	assert asset_store.get_assets() == {}

	create_job('job-test-capture-output-asset')
	capture_output_asset('job-test-capture-output-asset')

	assert asset_store.get_assets() == {}

	add_step('job-test-capture-output-asset',
	{
		'output_path': get_test_example_file('source.jpg')
	})
	add_step('job-test-capture-output-asset',
	{
		'output_path': get_test_example_file('invalid.jpg')
	})
	capture_output_asset('job-test-capture-output-asset')

	assert asset_store.get_assets() == {}

	create_job('job-test-capture-output-asset-2')
	add_step('job-test-capture-output-asset-2',
	{
		'output_path': get_test_example_file('invalid.jpg')
	})
	add_step('job-test-capture-output-asset-2',
	{
		'output_path': get_test_example_file('source.jpg')
	})
	capture_output_asset('job-test-capture-output-asset-2')
	assets = list(asset_store.get_assets().values())

	assert len(assets) == 1
	assert assets[0].get('type') == 'output'
	assert assets[0].get('media') == 'image'
	assert assets[0].get('path') == get_test_example_file('source.jpg')
