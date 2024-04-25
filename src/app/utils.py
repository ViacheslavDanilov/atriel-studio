from datetime import datetime

import gradio as gr

today = datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD


image_generation_inputs = [
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
]

csv_generation_inputs = [
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
    gr.Number(
        label='Number of CSV Files',
        value=1,
        precision=0,
        show_label=True,
    ),
    gr.Number(
        label='Max Pins Per CSV',
        value=3,
        precision=0,
        show_label=True,
    ),
    gr.Textbox(
        label='Start Date',
        value=today,
        placeholder='Enter the start date',
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
    gr.Slider(
        minimum=1,
        maximum=50,
        value=11,
        step=1,
        label='Seed',
        info='Choose between 1 and 100',
    ),
]
