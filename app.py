import gradio as gr

from src.image_generator import ImageGenerator


def process_sample(
    sample_dir: str,
    save_dir: str,
    num_images: int,
    scaling_factor: float,
    seed: int,
) -> str:
    processor = ImageGenerator(
        num_images=num_images,
        scaling_factor=scaling_factor,
        seed=seed,
    )
    processor.process_sample(
        sample_dir=sample_dir,
        save_dir=save_dir,
    )
    return 'Processing completed'


iface = gr.Interface(
    fn=process_sample,
    inputs=[
        gr.Textbox(
            label='Sample Directory',
            value='data/input/highlights/01',
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
            value=10,
            step=1,
            label='Number of Images',
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
        ['data/input/highlights/01', 'data/output/highlights/', 10, 1.0, 11],
        ['data/input/stories/04', 'data/output/stories/', 5, 1.0, 11],
        ['data/input/posts/01', 'data/output/posts/', 10, 1.0, 11],
    ],
)

if __name__ == '__main__':
    iface.launch(share=True)
