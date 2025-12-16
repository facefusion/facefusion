from typing import Optional

METADATA =\
{
	'name': '精通有道换脸demo',
	'description': 'Industry leading face manipulation platform',
	'version': '3.5.2',
	'license': 'OpenRAIL-AS',
	'author': 'Henry Ruhs',
	'url': 'https://u396531-9a75-6363c4e0.westc.gpuhub.com:8443/'
}


def get(key : str) -> Optional[str]:
	return METADATA.get(key)
