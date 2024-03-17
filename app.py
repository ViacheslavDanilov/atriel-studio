import os

import gradio as gr

from src.image_generator import ImageGenerator, ImageMatcher


def process_sample(
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

    return 'Processing completed'


iface = gr.Interface(
    fn=process_sample,
    inputs=[
        gr.Textbox(
            label='Sample Directory',
            value='data/input/highlights/neutral',
            placeholder='Enter path to the sample directory',
        ),
        gr.Textbox(
            label='Save Directory',
            value='data/output/highlights',
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
    title='Pinterest Image Generation App',
    description='Enter the sample directory, save directory, and parameters to process images.',
    examples=[
        ['data/input/highlights/neutral', 'data/output/highlights/', 10, 1.0, 11],
        ['data/input/stories/marketing_01', 'data/output/stories/', 5, 1.0, 11],
    ],
)

if __name__ == '__main__':
    iface.launch(share=True)
