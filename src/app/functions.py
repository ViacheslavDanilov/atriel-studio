import os
from pathlib import Path

from src.image_data.image_generator import ImageGenerator
from src.image_data.image_matcher import ImageMatcher


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
    num_csv_files: int,
    max_pins_per_csv: int,
    start_date: str,
    remove_local_files: bool,
    pins_per_day_canva_instagram_templates: int,
    pins_per_day_instagram_highlight_covers: int,
    pins_per_day_instagram_puzzle_feed: int,
    pins_per_day_business_cards: int,
    pins_per_day_airbnb_welcome_book: int,
    pins_per_day_price_and_service_guide: int,
    seed: int = 11,
) -> str:
    # TODO: Processing code goes here
    print(data_dir, save_dir, num_csv_files, max_pins_per_csv, start_date)
    print(remove_local_files, seed)
    pins_per_day = {
        'canva-instagram-templates': pins_per_day_canva_instagram_templates,
        'instagram-highlight-covers': pins_per_day_instagram_highlight_covers,
        'instagram-puzzle-feed': pins_per_day_instagram_puzzle_feed,
        'business-cards': pins_per_day_business_cards,
        'airbnb-welcome-book': pins_per_day_airbnb_welcome_book,
        'price-and-service-guide': pins_per_day_price_and_service_guide,
    }
    print(pins_per_day)
    return 'CSV(s) generated successfully!'
