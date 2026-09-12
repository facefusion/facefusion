from typing import Iterator

import pytest

from facefusion import session_context, session_manager, state_manager
from facefusion.apis.asset_store import create_asset, delete_asset, delete_assets, get_asset, get_assets, init
from facefusion.download import conditional_download
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	local_id = session_context.resolve_local_id()
	asset_id = create_asset('source', get_test_example_file('source.jpg')).get('id')

	session_context.set_session_id('session-a')
	init()

	assert get_asset(asset_id) is None

	session_manager.fork_session()

	assert get_assets() == {}

	session_manager.join_session()
	session_context.set_session_id(local_id)
	session_manager.fork_session()

	assert get_asset(asset_id).get('id') == asset_id

	session_manager.join_session()


def test_create_asset() -> None:
	asset = create_asset('source', get_test_example_file('source.jpg'))

	assert asset.get('type') == 'source'
	assert asset.get('media') == 'image'
	assert asset.get('name') == 'source'
	assert asset.get('format') == 'jpeg'
	assert asset.get('path') == get_test_example_file('source.jpg')


def test_get_assets() -> None:
	assert get_assets() == {}

	asset_id = create_asset('source', get_test_example_file('source.jpg')).get('id')

	assert list(get_assets().keys()) == [ asset_id ]


def test_get_asset() -> None:
	asset_id = create_asset('source', get_test_example_file('source.jpg')).get('id')

	assert get_asset(asset_id).get('id') == asset_id
	assert get_asset('invalid') is None


def test_delete_asset() -> None:
	asset_id = create_asset('source', get_test_example_file('source.jpg')).get('id')
	delete_asset(asset_id)

	assert get_asset(asset_id) is None

	delete_asset(asset_id)

	assert get_assets() == {}


def test_delete_assets() -> None:
	create_asset('source', get_test_example_file('source.jpg'))
	create_asset('target', get_test_example_file('source.jpg'))
	delete_assets()

	assert get_assets() == {}
