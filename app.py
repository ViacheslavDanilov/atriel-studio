import os

import gradio as gr

from src.app.utils import csv_generation_inputs, image_generation_inputs
from src.image_data.image_generator import ImageGenerator
from src.image_data.image_matcher import ImageMatcher


def generate_images(
    sample_dir: str,
    save_dir: str,
    num_images_per_bg: int,
    scaling_factor: float,
    seed: int,
) -> str:
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

    return 'Images generated successfully!'


def generate_csv(
    data_dir: str,
    save_dir: str,
    pins_per_day_canva_instagram_templates: int,
    pins_per_day_instagram_highlight_covers: int,
    pins_per_day_instagram_puzzle_feed: int,
    pins_per_day_business_cards: int,
    pins_per_day_airbnb_welcome_book: int,
    pins_per_day_price_and_service_guide: int,
    num_csv_files: int,
    max_pins_per_csv: int,
    remove_local_files: bool,
    start_date: str,
    seed: int,
) -> str:
    # Your processing code here

    return 'CSV(s) generated successfully!'


tab1 = gr.Interface(
    fn=generate_images,
    inputs=image_generation_inputs,
    outputs=gr.Textbox(label='Status'),
    description='Enter the sample directory, save directory, and parameters to process images.',
    examples=[
        ['data/input/highlights/neutral', 'data/output/highlights/', 10, 1.0, 11],
        ['data/input/stories/marketing_01', 'data/output/stories/', 5, 1.0, 11],
    ],
)

tab2 = gr.Interface(
    fn=generate_csv,
    inputs=csv_generation_inputs,
    outputs=gr.Textbox(label='Status'),
    title='CSV Generation',
    description='Enter the configuration for CSV generation.',
    # examples=[
    #     'data/csv_generation/', 'data/csv_generation/', 1, 1, 1, 0, 0, 0, 1, 3, True, '', 11
    # ],
)
iface = gr.TabbedInterface(
    interface_list=[tab1, tab2],
    tab_names=['Image Generation', 'CSV Generation'],
    title='Image & CSV Generation App for Pinterest',
    theme='default',
    analytics_enabled=True,
)

if __name__ == '__main__':
    iface.launch(share=False)
