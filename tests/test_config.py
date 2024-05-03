from configparser import ConfigParser
import pytest

from facefusion import config, globals
from facefusion.uis.components import config as config_save


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	config.CONFIG = ConfigParser()
	config.CONFIG.read_dict(
	{
		'str':
		{
			'valid': 'a',
			'unset': ''
		},
		'int':
		{
			'valid': '1',
			'unset': ''
		},
		'float':
		{
			'valid': '1.0',
			'unset': ''
		},
		'bool':
		{
			'valid': 'True',
			'unset': ''
		},
		'str_list':
		{
			'valid': 'a b c',
			'unset': ''
		},
		'int_list':
		{
			'valid': '1 2 3',
			'unset': ''
		},
		'float_list':
		{
			'valid': '1.0 2.0 3.0',
			'unset': ''
		}
	})


def test_get_str_value() -> None:
	assert config.get_str_value('str.valid') == 'a'
	assert config.get_str_value('str.unset', 'b') == 'b'
	assert config.get_str_value('str.unset') is None
	assert config.get_str_value('str.invalid') is None


def test_get_int_value() -> None:
	assert config.get_int_value('int.valid') == 1
	assert config.get_int_value('int.unset', '1') == 1
	assert config.get_int_value('int.unset') is None
	assert config.get_int_value('int.invalid') is None


def test_get_float_value() -> None:
	assert config.get_float_value('float.valid') == 1.0
	assert config.get_float_value('float.unset', '1.0') == 1.0
	assert config.get_float_value('float.unset') is None
	assert config.get_float_value('float.invalid') is None


def test_get_bool_value() -> None:
	assert config.get_bool_value('bool.valid') is True
	assert config.get_bool_value('bool.unset', 'False') is False
	assert config.get_bool_value('bool.unset') is None
	assert config.get_bool_value('bool.invalid') is None


def test_get_str_list() -> None:
	assert config.get_str_list('str_list.valid') == [ 'a', 'b', 'c' ]
	assert config.get_str_list('str_list.unset', 'c b a') == [ 'c', 'b', 'a' ]
	assert config.get_str_list('str_list.unset') is None
	assert config.get_str_list('str_list.invalid') is None


def test_get_int_list() -> None:
	assert config.get_int_list('int_list.valid') == [ 1, 2, 3 ]
	assert config.get_int_list('int_list.unset', '3 2 1') == [ 3, 2, 1 ]
	assert config.get_int_list('int_list.unset') is None
	assert config.get_int_list('int_list.invalid') is None


def test_get_float_list() -> None:
	assert config.get_float_list('float_list.valid') == [ 1.0, 2.0, 3.0 ]
	assert config.get_float_list('float_list.unset', '3.0 2.0 1.0') == [ 3.0, 2.0, 1.0 ]
	assert config.get_float_list('float_list.unset') is None
	assert config.get_float_list('float_list.invalid') is None


def test_update_config() -> None:
    config.CONFIG = None
    globals.config_path = 'facefusion.ini'
    globals.execution_thread_count = 22
    globals.execution_queue_count = 4
    config_save.save_config()
    new = config.get_config()
    assert new['execution']['execution_thread_count'] == '22'
    assert new['execution']['execution_queue_count'] == '4'
    globals.execution_thread_count = None
    globals.execution_queue_count = None
    config_save.save_config()
    old = config.get_config()
    assert old['execution']['execution_thread_count'] == ''
    assert old['execution']['execution_queue_count'] == ''