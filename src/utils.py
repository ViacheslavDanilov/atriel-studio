import fnmatch
import os
from pathlib import Path
from typing import List

CSV_COLUMNS = [
    'Title',
    'Media URL',
    'Pinterest board',
    'Thumbnail',
    'Description',
    'Link',
    'Publish date',
    'Keywords',
]


def get_file_list(
    directory: str,
    file_template: str,
) -> List[str]:
    file_list = []
    for root, dirs, files in os.walk(directory):
        file_list.extend(
            [os.path.join(root, file) for file in fnmatch.filter(files, file_template)],
        )
    file_list.sort()
    return file_list


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
