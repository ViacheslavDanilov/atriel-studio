from datetime import datetime

import gradio as gr

from src.app.functions import generate_csv_files, generate_images

# Create the Gradio app
with gr.Blocks(theme=gr.themes.Default(), title='Generation App') as app:
    with gr.Tab('Image Generation'):
        # Tab 1 - Row 1
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
        # Tab 1 - Row 2
        with gr.Row():
            num_images_per_bg = gr.Slider(
                label='Number of images for each background',
                minimum=1,
                maximum=20,
                step=1,
                value=3,
                info='Choose between 1 and 20',
            )
            scaling_factor = gr.Slider(
                label='Scaling',
                minimum=0.25,
                maximum=3,
                step=0.25,
                value=1,
                info='Choose between 0.5 and 5',
            )

        status_msg = gr.Textbox(label='Status')
        start_button_1 = gr.Button('Generate Images', variant='primary')
        start_button_1.click(
            fn=generate_images,
            inputs=[sample_dir, save_dir, num_images_per_bg, scaling_factor],
            outputs=status_msg,
        )

    with gr.Tab('CSV Generation'):
        # Tab 2 - Row 1
        with gr.Row():
            data_dir = gr.Textbox(
                label='Data Directory',
                value='data/csv_generation/',
                placeholder='Enter the directory with category folders inside',
            )
            save_dir = gr.Textbox(
                label='Save Directory',
                value='data/csv_generation/',
                placeholder='Enter the directory where the CSV files will be saved',
            )
        # Tab 2 - Row 2
        with gr.Row():
            num_csv_files = gr.Slider(
                label='Number of CSV Files',
                minimum=1,
                maximum=5,
                step=1,
                value=1,
                info='Choose between 1 and 5',
            )
            max_pins_per_csv = gr.Slider(
                label='Max Pins Per CSV',
                minimum=1,
                maximum=200,
                step=1,
                value=3,
                info='Choose between 1 and 200',
            )
            today = datetime.today().strftime('%Y-%m-%d')
            start_date = gr.Textbox(
                label='Start Date',
                value=today,  # Format: YYYY-MM-DD
                placeholder='Enter the start date',
                info='Enter the start date in the format YYYY-MM-DD',
            )
            copy_files_to_server = gr.Checkbox(
                label='Copy Files to Server',
                value=False,
                info='If checked, local files will be copied to the remote server',
            )
            remove_local_files = gr.Checkbox(
                label='Remove Local Files',
                value=False,
                info='If checked, local files will be removed after generation',
            )
        # Tab 2 - Row 3
        with gr.Row():
            pins_per_day_canva_instagram_templates = gr.Slider(
                label='Pins per day - Canva Instagram Templates',
                minimum=0,
                maximum=10,
                step=1,
                value=1,
                info='Choose between 0 and 10',
            )
            pins_per_day_instagram_highlight_covers = gr.Slider(
                label='Pins per day - Instagram Highlight Covers',
                minimum=0,
                maximum=10,
                step=1,
                value=1,
                info='Choose between 0 and 10',
            )
            pins_per_day_instagram_puzzle_feed = gr.Slider(
                label='Pins per day - Instagram Puzzle Feed',
                minimum=0,
                maximum=10,
                step=1,
                value=1,
                info='Choose between 0 and 10',
            )
        # Tab 2 - Row 4
        with gr.Row():
            pins_per_day_business_cards = gr.Slider(
                label='Pins per day - Business Cards',
                minimum=0,
                maximum=10,
                step=1,
                value=0,
                info='Choose between 0 and 10',
            )
            pins_per_day_airbnb_welcome_book = gr.Slider(
                label='Pins per day - Airbnb Welcome Book',
                minimum=0,
                maximum=10,
                step=1,
                value=0,
                info='Choose between 0 and 10',
            )
            pins_per_day_price_and_service_guide = gr.Slider(
                label='Pins per day - Price and Service Guide',
                minimum=0,
                maximum=10,
                step=1,
                value=0,
                info='Choose between 0 and 10',
            )

        status_msg = gr.Textbox(label='Status')
        start_button_2 = gr.Button('Generate CSVs', variant='primary')
        start_button_2.click(
            fn=generate_csv_files,
            inputs=[
                data_dir,
                save_dir,
                num_csv_files,
                max_pins_per_csv,
                start_date,
                copy_files_to_server,
                remove_local_files,
                pins_per_day_canva_instagram_templates,
                pins_per_day_instagram_highlight_covers,
                pins_per_day_instagram_puzzle_feed,
                pins_per_day_business_cards,
                pins_per_day_airbnb_welcome_book,
                pins_per_day_price_and_service_guide,
            ],
            outputs=status_msg,
        )


if __name__ == '__main__':
    app.launch(share=False)
