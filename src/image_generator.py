import fnmatch
import os
import random
from pathlib import Path
from typing import List

import cv2
import numpy as np
from tqdm import tqdm


class ImageGenerator:
    """Class for generating images."""

    def __init__(
        self,
        num_images: int,
        scaling_factor: float,
        seed: int,
        save_dir: str,
    ):
        self.num_images = num_images
        self.scaling_factor = scaling_factor
        self.seed = seed
        self.save_dir = save_dir

    @staticmethod
    def randomly_select_elements(
        lst: List[str],
        num_elements: int,
    ) -> List[str]:
        if num_elements > len(lst):
            raise ValueError('N is greater than the length of the list')
        selected_elements = random.sample(lst, num_elements)
        random.shuffle(selected_elements)
        return selected_elements

    @staticmethod
    def uniformly_select_elements(
        lst: List[str],
        num_elements: int,
        shuffle: bool = True,
    ):
        # Shuffle the list of elements
        random.shuffle(lst)

        # Calculate the number of times each element should be picked
        selections_per_element = num_elements // len(lst)

        # Create a list to store the selected elements
        selected_elements = []

        # Iterate through the shuffled list and select elements
        for element in lst:
            # Repeat each element for the calculated number of times
            selected_elements.extend([element] * selections_per_element)

        # If there are remaining selections, randomly pick elements to fill the quota
        remaining_selections = num_elements % len(lst)
        if remaining_selections > 0:
            selected_elements.extend(random.choices(lst, k=remaining_selections))

        if shuffle:
            random.shuffle(selected_elements)

        return selected_elements

    @staticmethod
    def crop_transparent_images(
        img: np.ndarray,
    ) -> np.ndarray:
        # Find non-zero alpha values
        non_transparent_pixels = cv2.findNonZero(img[:, :, 3])

        if non_transparent_pixels is None:
            return img

        # Get bounding box of non-transparent region
        x, y, w, h = cv2.boundingRect(non_transparent_pixels)

        # Crop the image
        cropped_img = img[y : y + h, x : x + w]

        return cropped_img

    def binarize_layout(
        self,
        layout_path: str,
    ) -> np.ndarray:
        layout = cv2.imread(layout_path, cv2.IMREAD_UNCHANGED)
        gray_layout = cv2.cvtColor(layout, cv2.COLOR_BGR2GRAY)
        ret, img_bin = cv2.threshold(gray_layout, 127, 255, cv2.THRESH_BINARY)
        img_bin_resized = cv2.resize(
            img_bin,
            dsize=None,
            fx=self.scaling_factor,
            fy=self.scaling_factor,
            interpolation=cv2.INTER_NEAREST,
        )
        return img_bin_resized

    def process_background(
        self,
        img_path: str,
        img_height: int,
        img_width: int,
    ) -> np.ndarray:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        img_resized = cv2.resize(img, dsize=(img_width, img_height), interpolation=cv2.INTER_CUBIC)
        return img_resized

    def process_sample(
        self,
        sample_dir: str,
    ) -> None:

        # Create a directory to store the files
        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(self.save_dir, sample_name)
        os.makedirs(sample_save_dir, exist_ok=True)

        img_dir = os.path.join(sample_dir, 'img')
        img_paths = self.get_file_list(img_dir, '*.[pP][nN][gG]')
        layout_path = os.path.join(sample_dir, 'layout.png')
        img_bin = self.binarize_layout(layout_path)
        img_back_paths_ = self.get_file_list(sample_dir, 'background_*.[pP][nN][gG]')
        img_back_paths = self.uniformly_select_elements(
            img_back_paths_,
            self.num_images,
            shuffle=True,
        )

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            img_bin,
            connectivity=8,
        )
        for idx, img_back_path in tqdm(
            enumerate(img_back_paths),
            desc='Generate images',
            unit=' images',
        ):
            img_res = self.process_background(
                img_back_path,
                img_height=img_bin.shape[0],
                img_width=img_bin.shape[1],
            )
            img_paths_selected = self.randomly_select_elements(img_paths, num_labels - 1)
            for label, img_path in zip(range(1, num_labels), img_paths_selected):
                cx, cy = centroids[label]
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                img = self.crop_transparent_images(img)
                img = cv2.resize(
                    img,
                    (stats[label, cv2.CC_STAT_WIDTH], stats[label, cv2.CC_STAT_HEIGHT]),
                )

                x, y = int(cx - img.shape[1] / 2), int(cy - img.shape[0] / 2)
                x, y = max(x, 0), max(y, 0)
                x_end, y_end = min(x + img.shape[1], img_res.shape[1]), min(
                    y + img.shape[0],
                    img_res.shape[0],
                )
                if x_end > x and y_end > y:
                    img_res[y:y_end, x:x_end] = img[: y_end - y, : x_end - x]

            save_path = os.path.join(sample_save_dir, f'{sample_name}_{idx + 1:02d}.png')
            cv2.imwrite(save_path, img_res)

    @staticmethod
    def get_file_list(
        src_dir: str,
        file_template: str,
    ) -> List[str]:
        file_list = []
        for root, dirs, files in os.walk(src_dir):
            file_list.extend(
                [os.path.join(root, file) for file in fnmatch.filter(files, file_template)],
            )
        file_list.sort()
        return file_list


if __name__ == '__main__':

    sample_dir = 'data/highlights/01'
    save_dir = 'data/highlights_ready'

    processor = ImageGenerator(
        num_images=10,
        scaling_factor=2,
        seed=42,
        save_dir=save_dir,
    )
    processor.process_sample(sample_dir=sample_dir)
