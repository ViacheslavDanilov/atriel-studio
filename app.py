import os

import gradio as gr

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
    inputs=[
        gr.Textbox(
            label='Sample Directory',
            value='data/image_generation/input/highlights/neutral',
            placeholder='Enter path to the sample directory',
        ),
        gr.Textbox(
            label='Save Directory',
            value='data/image_generation/output/highlights',
            placeholder='Enter path to the save directory',
        ),
        gr.Slider(
            minimum=1,
            maximum=20,
            value=3,
            step=1,
            label='Number of images for each background',
            info='Choose between 1 and 20',
        ),
        gr.Slider(
            minimum=0.25,
            maximum=3,
            value=1,
            step=0.25,
            label='Scaling',
            info='Choose between 0.5 and 5',
        ),
        gr.Slider(
            minimum=1,
            maximum=50,
            value=11,
            step=1,
            label='Seed',
            info='Choose between 1 and 100',
        ),
    ],
    outputs=gr.Textbox(label='Status'),
    description='Enter the sample directory, save directory, and parameters to process images.',
    examples=[
        ['data/input/highlights/neutral', 'data/output/highlights/', 10, 1.0, 11],
        ['data/input/stories/marketing_01', 'data/output/stories/', 5, 1.0, 11],
    ],
)

inputs = [
    gr.Textbox(
        label='Data Directory',
        value='data/csv_generation/',
        placeholder='Enter the data directory',
    ),
    gr.Textbox(
        label='Save Directory',
        value='data/csv_generation/',
        placeholder='Enter the save directory',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=1,
        step=1,
        label='Canva Instagram Templates',
        info='Choose the number of pins per day for Canva Instagram Templates',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=1,
        step=1,
        label='Instagram Highlight Covers',
        info='Choose the number of pins per day for Instagram Highlight Covers',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=1,
        step=1,
        label='Instagram Puzzle Feed',
        info='Choose the number of pins per day for Instagram Puzzle Feed',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=0,
        step=1,
        label='Business Cards',
        info='Choose the number of pins per day for Business Cards',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=0,
        step=1,
        label='Airbnb Welcome Book',
        info='Choose the number of pins per day for Airbnb Welcome Book',
    ),
    gr.Slider(
        minimum=0,
        maximum=20,
        value=0,
        step=1,
        label='Price and Service Guide',
        info='Choose the number of pins per day for Price and Service Guide',
    ),
    gr.Textbox(
        label='Number of CSV Files',
        value='1',
        placeholder='Enter the number of CSV files',
    ),
    gr.Textbox(
        label='Max Pins Per CSV',
        value='3',
        placeholder='Enter the max pins per CSV',
    ),
    gr.Checkbox(
        label='Remove Local Files',
        value=True,
    ),
    gr.Textbox(
        label='Start Date',
        value='',
        placeholder='Enter the start date',
    ),
    gr.Textbox(
        label='Seed',
        value='11',
        placeholder='Enter the seed value',
    ),
]

tab2 = gr.Interface(
    fn=generate_csv,
    inputs=inputs,
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
