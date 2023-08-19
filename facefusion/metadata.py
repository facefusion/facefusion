name = 'FaceFusion'
version = '1.0.0-beta'
website = 'https://facefusion.io'


METADATA =\
{
	'name': 'FaceFusion',
	'description': 'Next generation face swapper and enhancer',
	'version': '1.0.0-beta',
	'license': 'MIT',
	'author': 'Henry Ruhs',
	'url': 'https://facefusion.io'
}


def get(key : str) -> str:
	return METADATA[key]
