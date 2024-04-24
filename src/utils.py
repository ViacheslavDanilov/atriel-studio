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


def extract_id(
    path: str,
    type: str = 'category',
) -> str:

    parts = Path(path).parts
    if type == 'category':
        return parts[-4]
    elif type == 'sample_name':
        return parts[-3]
    elif type == 'sample_id':
        return parts[-2]
    else:
        raise ValueError('Invalid type')


def get_file_remote_path(
    img_path: str,
    remote_root_dir: str,
) -> str:
    parts = Path(img_path).parts[-5:]
    relative_path = '/'.join(parts)
    img_remote_path = os.path.join(remote_root_dir, relative_path)
    return img_remote_path


def get_file_url(
    remote_path: str,
    url: str,
) -> str:
    file_path = Path(remote_path)
    truncated_path = Path(*file_path.parts[4:])
    file_url = os.path.join(url, truncated_path)
    return file_url
