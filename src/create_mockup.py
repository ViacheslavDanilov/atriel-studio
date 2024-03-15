import logging
import os
import random
from pathlib import Path
from typing import List, Tuple

import cv2
import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src import PROJECT_DIR
from src.utils import get_file_list, get_dir_list

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def select_elements(
        lst: List[str],
        n: int,
        seed=None,
):
    if seed is not None:
        random.seed(seed)

    if n > len(lst):
        raise ValueError("N is greater than the length of the list")

    selected_elements = random.sample(lst, n)
    random.shuffle(selected_elements)

    return selected_elements


def process_sample(
        sample_dir: str,
        num_images: int,
        scaling_factor: float,
        save_dir: str,
        seed: int,
) -> None:
    # Get list of image paths
    img_paths = get_file_list(
        src_dirs=os.path.join(sample_dir, 'img'),
        ext_list='.png'
    )

    # Load layout image
    layout_path = os.path.join(sample_dir, 'layout.png')
    layout = cv2.imread(layout_path, cv2.IMREAD_UNCHANGED)

    # Convert layout to grayscale
    gray_layout = cv2.cvtColor(layout, cv2.COLOR_BGR2GRAY)

    # Threshold to create binary image
    ret, thresh = cv2.threshold(gray_layout, 127, 255, cv2.THRESH_BINARY)

    # Resize the thresholded binary image
    thresh_resized = cv2.resize(
        thresh,
        dsize=None,
        fx=scaling_factor,
        fy=scaling_factor,
        interpolation=cv2.INTER_NEAREST,
    )

    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh_resized, connectivity=8)

    for img_num in tqdm(range(num_images), desc="Generate images", unit=' images'):
        # Create a new image with transparent background
        img_res = np.zeros((thresh_resized.shape[0], thresh_resized.shape[1], 4), dtype=np.uint8)

        # Iterate through each component (excluding background)
        img_paths_selected = select_elements(
            lst=img_paths,
            n=num_labels-1,
            seed=seed + img_num,  # Adjust seed for each image
        )
        for label in range(1, num_labels):
            # Get centroid coordinates
            cx, cy = centroids[label]

            # Select an image from the list
            img_path = img_paths_selected.pop(0)
            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

            # Convert to 4-channel (RGBA)
            if img.shape[2] == 3:  # Check if image is 3-channel (RGB)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

            # Resize the image to fit the region
            # noinspection PyTypeChecker
            img = cv2.resize(
                src=img,
                dsize=(stats[label, cv2.CC_STAT_WIDTH], stats[label, cv2.CC_STAT_HEIGHT]),
            )

            # Calculate top-left corner coordinates for placing the image
            x = int(cx - img.shape[1] / 2)
            y = int(cy - img.shape[0] / 2)

            # Ensure the image stays within the layout boundaries
            x = max(x, 0)
            y = max(y, 0)
            x_end = min(x + img.shape[1], img_res.shape[1])  # Ensure x_end doesn't exceed img_res width
            y_end = min(y + img.shape[0], img_res.shape[0])  # Ensure y_end doesn't exceed img_res height

            # Paste the resized image onto the result if it has non-zero dimensions
            if x_end > x and y_end > y:
                img_res[y:y_end, x:x_end] = img[:y_end - y, :x_end - x]

        # Save the result with a transparent background
        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(save_dir, sample_name)
        os.makedirs(sample_save_dir, exist_ok=True)
        save_path = os.path.join(sample_save_dir, f'{sample_name}_{img_num+1:02d}.png')
        cv2.imwrite(save_path, img_res)

@hydra.main(
    config_path=os.path.join(PROJECT_DIR, 'configs'),
    config_name='create_mockup',
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    log.info(f'Config:\n\n{OmegaConf.to_yaml(cfg)}')

    # Define absolute paths
    data_dir = os.path.join(PROJECT_DIR, cfg.data_dir)
    save_dir = os.path.join(PROJECT_DIR, cfg.save_dir)

    sample_dirs = get_dir_list(
        data_dir=data_dir,
        include_dirs=cfg.include_samples,
        exclude_dirs=cfg.exclude_samples,
    )

    for sample_dir in sample_dirs:
        process_sample(
            sample_dir=sample_dir,
            num_images=cfg.num_images,
            scaling_factor=cfg.scaling_factor,
            save_dir=save_dir,
            seed=cfg.seed,
        )


if __name__ == '__main__':
    main()