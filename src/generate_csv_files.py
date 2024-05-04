import datetime
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
from src.text_data.publish_date_generator import PublishDateGenerator
from src.text_data.sample_processor import SampleProcessor
from src.text_data.ssh_file_transfer import SSHFileTransfer
from src.utils import CSV_COLUMNS

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def load_credentials(dotenv_path: str = '.env') -> Tuple[str, str, str, int, str, str]:
    load_dotenv(dotenv_path)
    HOSTNAME = os.environ.get('HOSTNAME')
    USERNAME = os.environ.get('USERNAME')
    PASSWORD = os.environ.get('PASSWORD')
    PORT = int(os.environ.get('PORT'))
    REMOTE_ROOT_DIR = os.environ.get('REMOTE_ROOT_DIR')
    URL = os.environ.get('URL')
    return HOSTNAME, USERNAME, PASSWORD, PORT, REMOTE_ROOT_DIR, URL


def filter_paths_by_category(
    paths: List[str],
    pins_per_day: Dict[str, int],
) -> List[str]:
    available_categories = set([os.path.basename(os.path.dirname(path)) for path in paths])
    non_zero_categories = set(
        [category for category, pins_per_day in pins_per_day.items() if pins_per_day != 0],
    )

    missing_categories = non_zero_categories - available_categories
    if missing_categories:
        log.info('Categories with non-zero pins per day not available in the provided directory:')
        for category in missing_categories:
            print('-', category)
        raise ValueError(
            'Some categories with non-zero pins per day are not available in the provided directory.',
        )

    filtered_paths = []
    for path in paths:
        category = os.path.basename(os.path.dirname(path))
        pins_per_day_for_category = pins_per_day.get(category, 0)  # type: ignore
        if pins_per_day_for_category != 0:
            filtered_paths.append(path)
    return filtered_paths


def create_df_per_day(
    df: pd.DataFrame,
    pins_per_day: Dict[str, int],
    seed: int = 11,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Initialize a dictionary to keep track of the number of pins added for each category
    pins_added_per_category = {category: 0 for category in pins_per_day}

    # Shuffle the DataFrame for randomness
    df_remaining = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Iterate over each row in the shuffled DataFrame
    unique_links = []
    df_per_day_list = []
    for row_idx, row in df_remaining.iterrows():
        category = row['category']
        num_pins = pins_per_day.get(category, 0)

        # Check if the maximum number of pins for the category has been reached and the link is unique
        if pins_added_per_category[category] < num_pins and row['Link'] not in unique_links:
            # Add the row to the DataFrame for the current day
            df_per_day_list.append(row)
            # Increment the count of pins added for the category
            pins_added_per_category[category] += 1
            # Delete the row from df_remaining
            df_remaining = df_remaining.drop(index=row_idx)
            # Add the link to the list of unique links
            unique_links.append(row['Link'])

        # Check if the pins for all categories have been added for the current day
        if all(
            count >= num_pins
            for count, num_pins in zip(pins_added_per_category.values(), pins_per_day.values())
        ):
            # If yes, break the loop
            break

    df_day = pd.DataFrame(df_per_day_list)
    df_remaining = df_remaining.reset_index(drop=True)

    return df_day, df_remaining


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
        log.info(
            f"Category: {category} - Pins needed: {pins_needed} - Pins available: {pins_available}",
        )

    # Check if there are any errors
    for category, pins_needed in pins_needed_per_category.items():
        pins_available = pins_available_per_category.get(category, 0)
        if pins_available < pins_needed:
            raise ValueError(
                f"Not enough pins available for category '{category}'. Needed: {pins_needed}, Available: {pins_available}",
            )
    log.info('All pins for each category are available.')


def save_csv_files(
    df: pd.DataFrame,
    save_dir: str,
) -> None:
    os.makedirs(save_dir, exist_ok=True)

    # Create a new column 'Auxiliary date' by converting 'Publish date' column to datetime
    df['Auxiliary date'] = pd.to_datetime(df['Publish date'])

    # Split DataFrame into chunks and save each chunk to a separate CSV file
    unique_dates = df['Auxiliary date'].dt.date.unique()
    for date in unique_dates:
        df_chunk = df[df['Auxiliary date'].dt.date == date]

        # Get the formatted date for the CSV filename
        formatted_date = date.strftime('%b-%d').lower()

        # Drop the 'Auxiliary date' column
        df_chunk = df_chunk.drop(columns=['Auxiliary date'])

        # Save chunk to CSV with filename based on the formatted date
        csv_filename = f'pins-{formatted_date}.csv'
        csv_filepath = os.path.join(save_dir, csv_filename)
        df_chunk.to_csv(
            csv_filepath,
            index=False,
            encoding='utf-8',
        )


@hydra.main(
    config_path=os.path.join(PROJECT_DIR, 'configs'),
    config_name='generate_csv_files',
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    log.info(f'Config:\n\n{OmegaConf.to_yaml(cfg)}')

    # Define absolute paths
    data_dir = str(os.path.join(PROJECT_DIR, cfg.data_dir))
    save_dir = str(os.path.join(PROJECT_DIR, cfg.save_dir))

    # Load credentials
    HOSTNAME, USERNAME, PASSWORD, PORT, REMOTE_ROOT_DIR, URL = load_credentials()

    # Get list of sample paths to process
    sample_dirs_ = glob(os.path.join(data_dir, '*/*'))
    sample_dirs = filter_paths_by_category(sample_dirs_, cfg.pins_per_day)

    # Process samples by their paths
    sample_processor = SampleProcessor(
        url=URL,
        remote_root_dir=REMOTE_ROOT_DIR,
        column_names=CSV_COLUMNS,
    )
    df_list = []
    for sample_dir in tqdm(sample_dirs, desc='Processing samples', unit='samples'):
        df_ = sample_processor.process_sample(sample_dir)
        df_list.append(df_)
    df_all = pd.concat(df_list, ignore_index=True)
    df = df_all.drop_duplicates(subset=['Title'], keep='first')

    # Check if there is enough samples for each category
    verify_pin_availability(df, cfg.pins_per_day, num_days=cfg.num_days)

    # Create df_day_list with DataFrames representing pins for each day
    df_day_list = []
    df_remaining = df.copy()
    for _ in range(cfg.num_days):
        df_day, df_remaining = create_df_per_day(
            df=df_remaining,
            pins_per_day=cfg.pins_per_day,
            seed=cfg.seed,
        )
        df_day_list.append(df_day)

    # Add publish dates to the dataframe
    current_date = datetime.datetime.strptime(cfg.start_date, '%Y-%m-%d')
    for day_idx, df_day in enumerate(df_day_list):
        publish_date_generator = PublishDateGenerator(date=current_date)
        publish_date_list = publish_date_generator.generate_times(num_pins_per_day=len(df_day))
        df_day['Publish date'] = publish_date_list
        df_day_list[day_idx] = df_day
        current_date += datetime.timedelta(days=1)

    # Upload images to the remote server
    df_out = pd.concat(df_day_list, ignore_index=True)
    if cfg.copy_files_to_server:
        ssh_file_transfer = SSHFileTransfer(
            username=USERNAME,
            hostname=HOSTNAME,
            port=PORT,
            password=PASSWORD,
            url=URL,
        )
        ssh_file_transfer.connect()
        ssh_file_transfer.remove_remote_dir(os.path.join(REMOTE_ROOT_DIR, '*'))
        for row in tqdm(df_out.itertuples(), desc='Uploading images', unit='images'):
            remote_dir = str(Path(row.dst_path).parent)
            ssh_file_transfer.create_remote_dir(remote_dir)
            ssh_file_transfer.upload_file(
                local_path=row.src_path,
                remote_path=row.dst_path,
            )
        ssh_file_transfer.disconnect()

    # Remove local files
    if cfg.remove_local_files:
        for row in df_out.itertuples():
            os.remove(row.src_path)

    # Save final CSVs
    df_out = df_out[CSV_COLUMNS]
    save_csv_files(
        df=df_out,
        save_dir=save_dir,
    )

    # Log summary
    saved_pins = len(df_out)
    total_pins = len(df_all)
    total_titles = len(df_all['Title'])
    total_links = len(df_all['Link'])
    unique_titles = len(df_all['Title'].unique())
    unique_links = len(df_all['Link'].unique())
    log.info(f'Total pins available: {total_pins}')
    log.info(f'Saved pins: {saved_pins}')
    log.info(f'Total titles: {total_titles}')
    log.info(f'Total links: {total_links}')
    log.info(f'Unique titles: {unique_titles}')
    log.info(f'Unique links: {unique_links}')

    log.info('Complete')


if __name__ == '__main__':
    main()
