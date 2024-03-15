import logging
import os
from glob import glob
from pathlib import Path
from typing import List, Union


def get_file_list(
    src_dirs: Union[List[str], str],
    ext_list: Union[List[str], str],
) -> List[str]:
    """Get list of files with the specified extensions.

    Args:
        src_dirs: directory(s) with files inside
        ext_list: extension(s) used for a search
    Returns:
        all_files: a list of file paths
    """
    all_files = []
    src_dirs = [src_dirs] if isinstance(src_dirs, str) else src_dirs
    ext_list = [ext_list] if isinstance(ext_list, str) else ext_list
    for src_dir in src_dirs:
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                file_ext = Path(file).suffix
                file_ext = file_ext.lower()
                if file_ext in ext_list:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
    all_files.sort()
    return all_files


def get_dir_list(
    data_dir: str,
    include_dirs: List[str],
    exclude_dirs: List[str],
) -> List[str]:
    dir_list = []
    _dir_list = glob(data_dir + '/*/')
    for series_dir in _dir_list:
        if include_dirs and Path(series_dir).name not in include_dirs:
            logging.info(
                f'Skip {Path(series_dir).name} because it is not in the included_dirs list',
            )
            continue

        if exclude_dirs and Path(series_dir).name in exclude_dirs:
            logging.info(
                f'Skip {Path(series_dir).name} because it is in the excluded_dirs list',
            )
            continue

        dir_list.append(series_dir)
    dir_list.sort()
    return dir_list
