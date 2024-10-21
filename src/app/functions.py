import datetime
import os
from glob import glob
from pathlib import Path

import gradio as gr
import pandas as pd
from tqdm import tqdm

from src.generate_csv_files import (
    create_df_per_day,
    filter_paths_by_category,
    load_credentials,
    save_csv_files,
    verify_pin_availability,
)
from src.image_data.image_generator import ImageGenerator
from src.image_data.image_matcher import ImageMatcher
from src.text_data.publish_date_generator import PublishDateGenerator
from src.text_data.sample_processor import SampleProcessor
from src.text_data.ssh_file_transfer import SSHFileTransfer
from src.utils import CSV_COLUMNS


def generate_images(
    sample_dir: str,
    save_dir: str,
    num_images_per_bg: int,
    scaling_factor: float,
    seed: int = 11,
) -> str:
    try:
        # Initialize ImageMatcher and ImageGenerator instances
        matcher = ImageMatcher()
        generator = ImageGenerator(
            num_images_per_bg=num_images_per_bg,
            scaling_factor=scaling_factor,
            seed=seed,
        )

        # Get metadata with layout and background pairs
        layout_dir = os.path.join(sample_dir, 'layouts')
        bg_dir = os.path.join(sample_dir, 'backgrounds')
        layout_paths = matcher.get_file_list(layout_dir, 'layout*.[jpPJ][nNpP][gG]')
        bg_paths = matcher.get_file_list(bg_dir, 'background*.[jpPJ][nNpP][gG]')
        df = matcher.create_dataframe(layout_paths, bg_paths)

        # Process sample
        generator.process_sample(
            df=df,
            sample_dir=sample_dir,
            save_dir=save_dir,
        )
        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(save_dir, sample_name)
        msg = f'Images generated successfully!\n\nDirectory: {sample_save_dir}'
    except Exception as e:
        msg = f'Something went wrong!\n\nError: {e}'

    return msg


def generate_csv_files(
    data_dir: str,
    save_dir: str,
    num_days: int,
    start_date: str,
    copy_files_to_server: bool,
    remove_local_files: bool,
    pins_per_day_canva_instagram_templates: int,
    pins_per_day_instagram_highlight_covers: int,
    pins_per_day_instagram_puzzle_feed: int,
    pins_per_day_blanket_mockup: int,
    pins_per_day_business_card_mockup: int,
    pins_per_day_carpet_mockup: int,
    seed: int = 11,
) -> str:

    try:
        pins_per_day = {
            'canva-instagram-templates': pins_per_day_canva_instagram_templates,
            'instagram-highlight-covers': pins_per_day_instagram_highlight_covers,
            'instagram-puzzle-feed': pins_per_day_instagram_puzzle_feed,
            'blanket-mockup': pins_per_day_blanket_mockup,
            'business-card-mockup': pins_per_day_business_card_mockup,
            'carpet-mockup': pins_per_day_carpet_mockup,
        }

        # Load credentials
        HOSTNAME, USERNAME, PASSWORD, PORT, REMOTE_ROOT_DIR, URL = load_credentials()

        # Get list of sample paths to process
        sample_dirs_ = glob(os.path.join(data_dir, '*/*'))
        sample_dirs = filter_paths_by_category(sample_dirs_, pins_per_day)

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
        verify_pin_availability(df, pins_per_day, num_days=num_days)

        # Create df_day_list with DataFrames representing pins for each day
        df_day_list = []
        df_remaining = df.copy()
        for _ in range(num_days):
            df_day, df_remaining = create_df_per_day(
                df=df_remaining,
                pins_per_day=pins_per_day,
                seed=seed,
            )
            df_day_list.append(df_day)

        # Add publish dates to the dataframe
        current_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        for day_idx, df_day in enumerate(df_day_list):
            publish_date_generator = PublishDateGenerator(date=current_date)
            publish_date_list = publish_date_generator.generate_times(num_pins_per_day=len(df_day))
            df_day['Publish date'] = publish_date_list
            df_day_list[day_idx] = df_day
            current_date += datetime.timedelta(days=1)

        # Upload images to the remote server
        df_out = pd.concat(df_day_list, ignore_index=True)
        if copy_files_to_server:
            ssh_file_transfer = SSHFileTransfer(
                username=USERNAME,
                hostname=HOSTNAME,
                port=PORT,
                password=PASSWORD,
                url=URL,
            )
            ssh_file_transfer.connect()
            ssh_file_transfer.remove_remote_dir(os.path.join(REMOTE_ROOT_DIR, '*'))
            total_pins = len(df_out)
            progress = gr.Progress(track_tqdm=True)
            progress(0, desc='Starting')
            for idx, row in enumerate(
                tqdm(
                    df_out.itertuples(),
                    desc='Uploading images',
                    unit='images',
                    total=total_pins,
                ),
            ):
                remote_dir = str(Path(row.dst_path).parent)
                ssh_file_transfer.create_remote_dir(remote_dir)
                ssh_file_transfer.upload_file(
                    local_path=row.src_path,
                    remote_path=row.dst_path,
                )
                # Update progress
                progress((idx + 1) / total_pins)
            ssh_file_transfer.disconnect()

        # Remove local files
        if remove_local_files:
            for row in df_out.itertuples():
                os.remove(row.src_path)

        # Save final CSVs
        df_out = df_out[CSV_COLUMNS]
        save_csv_files(
            df=df_out,
            save_dir=save_dir,
        )

        # Log summary
        total_pins = len(df_all)
        num_saved_pins = len(df_out)
        num_products = len(df_out['Link'].unique())
        msg = (
            f'CSV(s) generated successfully!\n\n'
            f'Saved directory: {save_dir}\n\n'
            f'Total pins available: {total_pins}\n\n'
            f'Saved pins: {num_saved_pins}\n\n'
            f'Products advertised: {num_products}\n\n'
        )
    except Exception as e:
        msg = f'Something went wrong!\n\nError: {e}'

    return msg
