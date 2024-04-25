import os
from pathlib import Path

import gradio as gr

from src.image_data.image_generator import ImageGenerator
from src.image_data.image_matcher import ImageMatcher


def generate_images(
    sample_dir: str,
    save_dir: str,
    num_images_per_bg: int,
    scaling_factor: float,
    seed: int = 11,
) -> str:
    # Initialize ImageMatcher and ImageGenerator instances
    try:
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


# Create the Gradio app
with gr.Blocks(theme=gr.themes.Soft()) as app:
    # Create the tabs
    with gr.Tab('Image Generation'):
        with gr.Row():
            sample_dir = gr.Textbox(
                label='Sample Directory',
                value='data/image_generation/input/highlights/neutral',
                placeholder='Enter path to the sample directory',
            )
            save_dir = gr.Textbox(
                label='Save Directory',
                value='data/image_generation/output/highlights',
                placeholder='Enter path to the save directory',
            )
        with gr.Row():
            num_images_per_bg = gr.Slider(
                minimum=1,
                maximum=20,
                value=3,
                step=1,
                label='Number of images for each background',
                info='Choose between 1 and 20',
            )
            scaling_factor = gr.Slider(
                minimum=0.25,
                maximum=3,
                value=1,
                step=0.25,
                label='Scaling',
                info='Choose between 0.5 and 5',
            )

        output = gr.Textbox(label='Output Message')
        tab1_submit_button = gr.Button('Generate Images')
        tab1_submit_button.click(
            fn=generate_images,
            inputs=[sample_dir, save_dir, num_images_per_bg, scaling_factor],
            outputs=output,
        )

    with gr.Tab('CSV Generation'):
        with gr.Row():
            input3 = gr.Textbox(label='Input 3')
            input4 = gr.Textbox(label='Input 4')
        output3, output4 = gr.Textbox(label='Output 3'), gr.Textbox(label='Output 4')
        tab2_button = gr.Button('Process Tab 2')
        tab2_button.click(fn=tab2_func, inputs=[input3, input4], outputs=[output3, output4])


if __name__ == '__main__':
    app.launch(share=False)
