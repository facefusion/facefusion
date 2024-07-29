from facefusion import process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.filesystem import is_file
from facefusion.typing import SourceSet


def conditional_download_sources(download_directory_path : str, model_sources : SourceSet) -> bool:
	model_urls = [ model_sources.get(model_source).get('url') for model_source in model_sources.keys() ]
	model_paths = [ model_sources.get(model_source).get('path') for model_source in model_sources.keys() ]

	if not state_manager.get_item('skip_download'):
		process_manager.check()
		conditional_download(download_directory_path, model_urls)
		process_manager.end()
	return all(is_file(model_path) for model_path in model_paths)
