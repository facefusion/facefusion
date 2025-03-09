from typing import Optional

METADATA =\
{
	'name': 'FaceFusion',
	'description': 'Industry leading face manipulation platform',
	'version': 'NEXT',
	'license': 'OpenRAIL-AS',
	'author': 'Henry Ruhs',
	'url': 'https://facefusion.io'
}


def get(key : str) -> Optional[str]:
	if key in METADATA:
		return METADATA.get(key)
	return None
