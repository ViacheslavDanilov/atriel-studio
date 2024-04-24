import logging
import os
from glob import glob
from pathlib import Path
from typing import Dict, List, Tuple

import hydra
import pandas as pd
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src import PROJECT_DIR
from src.text_generators.description_generator import DescriptionGenerator
from src.text_generators.publish_date_generator import PublishDateGenerator
from src.text_generators.title_generator import TitleGenerator
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


def filter_paths_by_category(
    paths: List[str],
    pins_dict: dict,
) -> List[str]:
    filtered_paths = []
    for path in paths:
        category = os.path.basename(os.path.dirname(path))
        pins_per_day = pins_dict.get(category, 0)
        if pins_per_day != 0:
            filtered_paths.append(path)
    return filtered_paths


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
    board_list = [category.replace('-', ' ').title() for category in category_list]
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
    num_csv_files: int = 2,
) -> None:
    if len(df) % num_csv_files != 0:
        raise ValueError(
            f'Cannot split DataFrame evenly. Number of rows: {len(df)}. Number of CSV files: {num_csv_files}.',
        )

    # Calculate the number of rows per CSV file
    rows_per_csv = len(df) // num_csv_files

    # Split DataFrame into chunks and save each chunk to a separate CSV file
    os.makedirs(save_dir, exist_ok=True)
    for idx in range(num_csv_files):
        start_idx = idx * rows_per_csv
        end_idx = (idx + 1) * rows_per_csv
        df_chunk = df.iloc[start_idx:end_idx]

        # Get the earliest publishing date in the chunk and format it as DDMMYY
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


def create_df_per_day(
    df: pd.DataFrame,
    pins_per_day: Dict[str, int],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Initialize a dictionary to keep track of the number of pins added for each category
    pins_added_per_category = {category: 0 for category in pins_per_day}

    # Shuffle the DataFrame for randomness
    df = df.sample(frac=1).reset_index(drop=True)

    # Iterate over each row in the shuffled DataFrame
    df_per_day_list = []
    for _, row in df.iterrows():
        category = row['category']
        num_pins = pins_per_day.get(category, 0)

        # Check if the maximum number of pins for the category has been reached
        if pins_added_per_category[category] < num_pins:
            # Add the row to the DataFrame for the current day
            df_per_day_list.append(row)
            # Increment the count of pins added for the category
            pins_added_per_category[category] += 1
            # Remove the selected row from consideration
            df = df[df.index != row.name]

        # Check if the pins for all categories have been added for the current day
        if all(
            count >= num_pins
            for count, num_pins in zip(pins_added_per_category.values(), pins_per_day.values())
        ):
            # If yes, break the loop
            break

    df_day = pd.DataFrame(df_per_day_list)

    return df_day, df


def verify_pin_availability(
    df: pd.DataFrame,
    pins_per_day: Dict[str, int],
    num_days: int,
) -> None:
    # Count the number of pins available for each category in the DataFrame
    pins_available_per_category = {}
    for category in pins_per_day:
        pins_available_per_category[category] = df[df['category'] == category].shape[0]

    pins_needed_per_category = {}
    for category, num_pins in pins_per_day.items():
        pins_needed_per_category[category] = num_pins * num_days

    # Print the number of pins needed and available for each category
    for category in pins_per_day:
        pins_needed = pins_needed_per_category[category]
        pins_available = pins_available_per_category.get(category, 0)
        print(
            f"Category: {category} - Pins needed: {pins_needed} - Pins available: {pins_available}",
        )

    # Check if there are any errors
    for category, pins_needed in pins_needed_per_category.items():
        pins_available = pins_available_per_category.get(category, 0)
        if pins_available < pins_needed:
            raise ValueError(
                f"Not enough pins available for category '{category}'. Needed: {pins_needed}, Available: {pins_available}",
            )
    print('All pins for each category are available.')


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

    # Get list of sample paths to process
    sample_paths_ = glob(os.path.join(data_dir, '*/*'))
    sample_paths = filter_paths_by_category(sample_paths_, cfg.pins_per_day)

    # Process samples by their paths
    df_list = []
    for sample_path in tqdm(sample_paths, desc='Processing samples', unit='samples'):
        df = process_sample(sample_path, column_names=CSV_COLUMNS)
        df_list.append(df)
    df = pd.concat(df_list, ignore_index=True)

    # Check if there is enough sample for each category
    num_days = (cfg.max_pins_per_csv * cfg.num_csv_files) // sum(cfg.pins_per_day.values())
    verify_pin_availability(df, cfg.pins_per_day, num_days=num_days)

    # Create df_day_list with DataFrames representing pins for each day
    df_day_list = []
    df_remaining = df.copy()
    for day_id in range(num_days):
        df_day, df_remaining = create_df_per_day(df_remaining, cfg.pins_per_day)
        df_day['day_id'] = day_id + 1
        df_day_list.append(df_day)
    df_output = pd.concat(df_day_list, ignore_index=True)

    # Add publish dates to the dataframe
    publish_date_generator = PublishDateGenerator(start_date=cfg.start_date)
    publish_date_list = publish_date_generator.generate_times(
        total_pins=len(df_output),
        num_pins_per_day=sum(cfg.pins_per_day.values()),
    )
    df_output['Publish date'] = publish_date_list

    # Save final CSVs
    df_output = df_output[CSV_COLUMNS]
    save_csv_files(
        df=df_output,
        save_dir=save_dir,
        num_csv_files=cfg.num_csv_files,
    )

    log.info('Complete')


if __name__ == '__main__':
    main()
