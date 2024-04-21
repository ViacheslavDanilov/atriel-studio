import logging
import os
from glob import glob
from pathlib import Path
from typing import List

import hydra
import pandas as pd
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

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


def process_sample(
    sample_path: str,
    column_names: List[str] = CSV_COLUMNS,
) -> pd.DataFrame:
    # Initialize dataframe
    df = pd.DataFrame(columns=column_names)

    # Supplementary information
    img_paths = glob(os.path.join(sample_path, '*/*.[jpPJ][nNpP][gG]'))
    img_names = [Path(img_path).name for img_path in img_paths]
    category_list = [extract_id(img_path, 'category') for img_path in img_paths]
    sample_names = [extract_id(img_path, 'sample_name') for img_path in img_paths]
    sample_ids = [extract_id(img_path, 'sample_id') for img_path in img_paths]
    df['category'] = category_list
    df['sample_name'] = sample_names
    df['sample_id'] = sample_ids
    df['sample_id'] = df['sample_id'].astype(str)
    df['img_name'] = img_names
    df['src_path'] = img_paths

    # Image paths
    remote_img_path_list = [
        get_file_remote_path(img_path, REMOTE_ROOT_DIR) for img_path in img_paths
    ]
    df['dst_path'] = remote_img_path_list

    # Titles
    df_key = pd.read_csv(os.path.join(sample_path, 'keywords.csv'))
    title_generator = TitleGenerator(df_key)
    title_list = title_generator.generate_titles(num_titles=len(img_paths))
    df['Title'] = title_list

    # URLs
    url_list = [get_file_url(remote_img_path, URL) for remote_img_path in remote_img_path_list]
    df['Media URL'] = url_list

    # Pinterest boards
    board_list = [category.replace('_', ' ').title() for category in category_list]
    df['Pinterest board'] = board_list

    # Thumbnails
    thumbnail_list = [''] * len(img_paths)
    df['Thumbnail'] = thumbnail_list

    # Descriptions
    df_desc = pd.read_csv(os.path.join(sample_path, 'descriptions.csv'))
    desc_generator = DescriptionGenerator(df_desc)
    desc_list = desc_generator.generate_descriptions(num_descriptions=len(img_paths))
    df['Description'] = desc_list

    # Links
    df_links = pd.read_csv(os.path.join(sample_path, 'links.csv'), dtype={'sample_id': str})
    sample_id_to_link = df_links.set_index('sample_id')['link'].to_dict()
    df['Link'] = df['sample_id'].map(sample_id_to_link)

    # Keywords
    keyword_list = [''] * len(img_paths)
    df['Keywords'] = keyword_list

    return df


def save_csv_files(
    df: pd.DataFrame,
    save_dir: str,
    num_pins_per_csv: int = 200,
) -> None:
    # Calculate the number of CSV files needed
    num_csv_files = -(-len(df) // num_pins_per_csv)

    # Split DataFrame into chunks and save each chunk to a separate CSV file
    os.makedirs(save_dir, exist_ok=True)
    for i in range(num_csv_files):
        start_idx = i * num_pins_per_csv
        end_idx = min((i + 1) * num_pins_per_csv, len(df))
        df_chunk = df.iloc[start_idx:end_idx]

        # Get the earliest publish date in the chunk and format it as DDMMYY
        earliest_publish_date = pd.to_datetime(df_chunk['Publish date'].iloc[0])
        formatted_date = earliest_publish_date.strftime('%d%m%y')

        # Save chunk to CSV with filename based on the formatted date
        csv_filename = f'pins_{formatted_date}.csv'
        csv_filepath = os.path.join(save_dir, csv_filename)
        df_chunk.to_csv(
            csv_filepath,
            index=False,
            encoding='utf-8',
        )


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

    # Process samples by their paths
    df_list = []
    for sample_path in tqdm(sample_paths, desc='Processing samples', unit='samples'):
        df = process_sample(sample_path, column_names=CSV_COLUMNS)
        df_list.append(df)
    df = pd.concat(df_list, ignore_index=True)

    # Add publish dates to the dataframe
    publish_date_generator = PublishDateGenerator(
        num_times_per_day=cfg.num_pins_per_day,
        total_times=len(df),
        start_date=cfg.start_date,
    )
    publish_date_list = publish_date_generator.generate_times()
    df['Publish date'] = publish_date_list

    # Save final CSVs
    df = df[CSV_COLUMNS]
    save_csv_files(df=df, save_dir=save_dir, num_pins_per_csv=cfg.num_pins_per_csv)

    log.info('Complete')


if __name__ == '__main__':
    main()
