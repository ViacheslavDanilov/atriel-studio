import os
from glob import glob
from pathlib import Path
from typing import List

import pandas as pd

from src.text_data.description_generator import DescriptionGenerator
from src.text_data.title_generator import TitleGenerator


class SampleProcessor:
    """A class to process sample data and generate a DataFrame.

    This class provides methods to process sample data stored in a directory
    and generate a DataFrame containing information extracted from the samples.
    """

    def __init__(
        self,
        url: str,
        remote_root_dir: str,
        column_names: List[str],
    ):
        self.url = url
        self.remote_root_dir = remote_root_dir
        self.column_names = column_names

    @staticmethod
    def _extract_id(
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

    @staticmethod
    def _get_file_remote_path(
        img_path: str,
        remote_root_dir: str,
    ) -> str:
        parts = list(Path(img_path).parts[-4:])
        img_stem = str(Path(img_path).stem)
        parts[-2] = f'{parts[-2]}-{img_stem}'
        relative_path = '/'.join(parts)
        img_remote_path = os.path.join(remote_root_dir, relative_path)
        return img_remote_path

    @staticmethod
    def _get_file_url(
        remote_path: str,
        url: str,
    ) -> str:
        file_path = Path(remote_path)
        truncated_path = Path(*file_path.parts[4:])
        file_url = os.path.join(url, truncated_path)
        return file_url

    def process_sample(self, sample_dir: str) -> pd.DataFrame:
        # Initialize dataframe
        df = pd.DataFrame(columns=self.column_names)

        # Supplementary information
        img_paths = glob(os.path.join(sample_dir, '*/*.[jpPJ][nNpP][gG]'))
        img_names = [Path(img_path).name for img_path in img_paths]
        category_list = [self._extract_id(img_path, 'category') for img_path in img_paths]
        sample_names = [self._extract_id(img_path, 'sample_name') for img_path in img_paths]
        sample_ids = [self._extract_id(img_path, 'sample_id') for img_path in img_paths]
        df['category'] = category_list
        df['sample_name'] = sample_names
        df['sample_id'] = sample_ids
        df['sample_id'] = df['sample_id'].astype(str)
        df['img_name'] = img_names
        df['src_path'] = img_paths

        # Image paths
        remote_img_path_list = [
            self._get_file_remote_path(img_path, self.remote_root_dir) for img_path in img_paths
        ]
        df['dst_path'] = remote_img_path_list

        # Titles
        df_key = pd.read_csv(os.path.join(sample_dir, 'keywords.csv'))
        title_generator = TitleGenerator(df_key)
        title_list = title_generator.generate_titles(num_titles=len(img_paths))
        df['Title'] = title_list

        # URLs
        url_list = [
            self._get_file_url(remote_img_path, self.url)
            for remote_img_path in remote_img_path_list
        ]
        df['Media URL'] = url_list

        # Pinterest boards
        board_list = [category.replace('-', ' ').title() for category in category_list]
        df['Pinterest board'] = board_list

        # Thumbnails
        thumbnail_list = [''] * len(img_paths)
        df['Thumbnail'] = thumbnail_list

        # Descriptions
        df_desc = pd.read_csv(os.path.join(sample_dir, 'descriptions.csv'))
        desc_generator = DescriptionGenerator(df_desc)
        desc_list = desc_generator.generate_descriptions(num_descriptions=len(img_paths))
        df['Description'] = desc_list

        # Links
        df_links = pd.read_csv(os.path.join(sample_dir, 'links.csv'), dtype={'sample_id': str})
        sample_id_to_link = df_links.set_index('sample_id')['link'].to_dict()
        df['Link'] = df['sample_id'].map(sample_id_to_link)

        # Keywords
        keyword_list = [''] * len(img_paths)
        df['Keywords'] = keyword_list

        return df
