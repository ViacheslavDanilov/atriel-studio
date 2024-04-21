import logging
import os
from glob import glob
from pathlib import Path

import hydra
import pandas as pd
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf

from src import PROJECT_DIR
from src.generators import DescriptionGenerator, PublishDateGenerator, TitleGenerator
from src.utils import CSV_COLUMNS

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

load_dotenv()
HOSTNAME = os.environ.get('HOSTNAME')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
PORT = int(os.environ.get('PORT'))
REMOTE_ROOT_DIR = os.environ.get('REMOTE_ROOT_DIR')
URL = os.environ.get('URL')


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


@hydra.main(
    config_path=os.path.join(PROJECT_DIR, 'configs'),
    config_name='generate_pintereset_csv',
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    log.info(f'Config:\n\n{OmegaConf.to_yaml(cfg)}')

    # Define absolute paths
    data_dir = str(os.path.join(PROJECT_DIR, cfg.data_dir))
    save_dir = str(os.path.join(PROJECT_DIR, cfg.save_dir))
    print(save_dir)

    sample_paths = glob(os.path.join(data_dir, '*/*'))
    for sample_path in sample_paths:

        # Initialize dataframe
        df = pd.DataFrame(columns=CSV_COLUMNS)

        # Get list of image paths
        img_paths = glob(os.path.join(sample_path, '*/*.[jpPJ][nNpP][gG]'))
        img_names = [Path(img_path).name for img_path in img_paths]
        category_list = [extract_id(img_path, 'category') for img_path in img_paths]
        sample_names = [extract_id(img_path, 'sample_name') for img_path in img_paths]
        sample_ids = [extract_id(img_path, 'sample_id') for img_path in img_paths]
        df['category'] = category_list
        df['sample_name'] = sample_names
        df['sample_id'] = sample_ids
        df['img_name'] = img_names
        df['src_path'] = img_paths

        # Prepare a list of remote image paths
        remote_img_path_list = [
            get_file_remote_path(img_path, REMOTE_ROOT_DIR) for img_path in img_paths
        ]
        df['dst_path'] = remote_img_path_list

        # Prepare a list of titles
        df_key = pd.read_csv(os.path.join(sample_path, 'keywords.csv'))
        title_generator = TitleGenerator(df_key)
        title_list = title_generator.generate_titles(num_titles=len(img_paths))
        df['Title'] = title_list

        # Prepare a list of image URLs
        url_list = [get_file_url(remote_img_path, URL) for remote_img_path in remote_img_path_list]
        df['Media URL'] = url_list

        # Prepare a list of pinterest boards
        board_list = [category.replace('_', ' ').title() for category in category_list]
        df['Pinterest board'] = board_list

        # Prepare a list of thumbnails
        thumbnail_list = [''] * len(img_paths)
        df['Thumbnail'] = thumbnail_list

        # Prepare a list of descriptions
        df_desc = pd.read_csv(os.path.join(sample_path, 'descriptions.csv'))
        desc_generator = DescriptionGenerator(df_desc)
        desc_list = desc_generator.generate_descriptions(num_descriptions=len(img_paths))
        df['Description'] = desc_list

        # Prepare a list of links
        link_list = [URL] * len(img_paths)  # TODO: Replace current URL with ad links
        df['Link'] = link_list

        # TODO: Prepare a list of publish dates
        publish_date_generator = PublishDateGenerator(
            num_times_per_day=cfg.num_pins_per_day,
            total_times=len(img_paths),
            start_date=cfg.start_date,
        )
        publish_date_list = publish_date_generator.generate_times()
        df['Publish date'] = publish_date_list

        # Prepare a list of keywords
        keyword_list = [''] * len(img_paths)
        df['Keywords'] = keyword_list

    # TODO: Save final CSVs with emojis
    os.makedirs(save_dir, exist_ok=True)
    df.to_csv(
        os.path.join(save_dir, 'pins.csv'),
        index=False,
        encoding='utf-8',
    )

    log.info('Complete')


if __name__ == '__main__':
    main()
