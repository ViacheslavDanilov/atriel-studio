import os
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
    include_dirs: List[str] = [],
    exclude_dirs: List[str] = [],
) -> List[str]:
    dir_list = []

    for series_dir in os.listdir(data_dir):
        series_path = Path(os.path.join(data_dir, series_dir))
        if not series_path.is_dir():
            continue

        if include_dirs and series_dir not in include_dirs:
            continue

        if exclude_dirs and series_dir in exclude_dirs:
            continue

        dir_list.append(str(series_path))

    dir_list.sort()

    return dir_list
