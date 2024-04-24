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

load_dotenv()
HOSTNAME = os.environ.get('HOSTNAME')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
PORT = int(os.environ.get('PORT'))
REMOTE_ROOT_DIR = os.environ.get('REMOTE_ROOT_DIR')
URL = os.environ.get('URL')


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


def create_df_per_day(
    df: pd.DataFrame,
    pins_per_day: Dict[str, int],
    seed: int = 11,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Initialize a dictionary to keep track of the number of pins added for each category
    pins_added_per_category = {category: 0 for category in pins_per_day}

    # Shuffle the DataFrame for randomness
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

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
        formatted_date = earliest_publish_date.strftime('%b-%d').lower()

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
    config_name='generate_pintereset_csv',
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    log.info(f'Config:\n\n{OmegaConf.to_yaml(cfg)}')

    # Define absolute paths
    data_dir = str(os.path.join(PROJECT_DIR, cfg.data_dir))
    save_dir = str(os.path.join(PROJECT_DIR, cfg.save_dir))

    # Get list of sample paths to process
    sample_dirs_ = glob(os.path.join(data_dir, '*/*'))
    sample_dirs = filter_paths_by_category(sample_dirs_, cfg.pins_per_day)

    # Process samples by their paths
    df_list = []
    sample_processor = SampleProcessor(
        url=URL,
        remote_root_dir=REMOTE_ROOT_DIR,
        column_names=CSV_COLUMNS,
    )
    for sample_dir in tqdm(sample_dirs, desc='Processing samples', unit='samples'):
        df = sample_processor.process_sample(sample_dir)
        df_list.append(df)
    df = pd.concat(df_list, ignore_index=True)

    # Check if there is enough sample for each category
    num_days = (cfg.max_pins_per_csv * cfg.num_csv_files) // sum(cfg.pins_per_day.values())
    verify_pin_availability(df, cfg.pins_per_day, num_days=num_days)

    # Create df_day_list with DataFrames representing pins for each day
    df_day_list = []
    df_remaining = df.copy()
    for _ in range(num_days):
        df_day, df_remaining = create_df_per_day(
            df=df_remaining,
            pins_per_day=cfg.pins_per_day,
            seed=cfg.seed,
        )
        df_day_list.append(df_day)
    df_output = pd.concat(df_day_list, ignore_index=True)

    # Add publish dates to the dataframe
    publish_date_generator = PublishDateGenerator(start_date=cfg.start_date)
    publish_date_list = publish_date_generator.generate_times(
        total_pins=len(df_output),
        num_pins_per_day=sum(cfg.pins_per_day.values()),
    )
    df_output['Publish date'] = publish_date_list

    # Upload images to the remote server
    ssh_file_transfer = SSHFileTransfer(
        username=USERNAME,
        hostname=HOSTNAME,
        port=PORT,
        password=PASSWORD,
        url=URL,
    )
    ssh_file_transfer.connect()
    ssh_file_transfer.remove_remote_dir(os.path.join(REMOTE_ROOT_DIR, '*'))
    for row in tqdm(df_output.itertuples(), desc='Uploading images', unit='images'):
        remote_dir = str(Path(row.dst_path).parent)
        ssh_file_transfer.create_remote_dir(remote_dir)
        ssh_file_transfer.upload_file(
            local_path=row.src_path,
            remote_path=row.dst_path,
        )
    ssh_file_transfer.disconnect()

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
