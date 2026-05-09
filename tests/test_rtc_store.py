import pytest

from facefusion.libraries import datachannel as datachannel_module


@pytest.fixture(scope = 'module')
def before_all() -> None:
	datachannel_module.pre_check()


# TODO: test create_rtc_stream, get_rtc_stream, destroy_rtc_stream lifecycle
def test_rtc_stream_lifecycle() -> None:
	pass


# TODO: test add_rtc_viewer with valid session and sdp offer
def test_add_rtc_viewer() -> None:
	pass
