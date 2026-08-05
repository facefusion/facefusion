from facefusion import translator
from facefusion.locales import LOCALES


def test_load() -> None:
	translator.load(LOCALES, __name__)

	assert __name__ in translator.LOCALE_POOL_SET


def test_get() -> None:
	assert translator.get('python_not_supported').format(version = '3.12') == 'python version is not supported, upgrade to 3.12 or higher'
	assert translator.get('help.run') == 'run the program'
	assert translator.get('invalid') is None
