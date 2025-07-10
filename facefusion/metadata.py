from typing import Optional

METADATA =\
{
	'name': 'FaceFusion',
	'description': 'Industry leading face manipulation platform',
	'version': '3.3.2',
	'license': 'OpenRAIL-AS',
	'author': 'Henry Ruhs',
	'url': 'https://facefusion.io'
}


def get(key : str) -> Optional[str]:
	if key in METADATA:
		return METADATA.get(key)
	return None
