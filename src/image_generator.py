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
    def select_elements(
        lst: List[str],
        n: int,
    ) -> List[str]:
        if n > len(lst):
            raise ValueError('N is greater than the length of the list')
        selected_elements = random.sample(lst, n)
        random.shuffle(selected_elements)
        return selected_elements

    def crop_transparent_images(
        self,
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

    def process_sample(
        self,
        sample_dir: str,
    ) -> None:
        img_paths = self.get_file_list(os.path.join(sample_dir, 'img'), '.png')
        layout_path = os.path.join(sample_dir, 'layout.png')
        img_bin = self.binarize_layout(layout_path)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            img_bin,
            connectivity=8,
        )

        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(self.save_dir, sample_name)
        os.makedirs(sample_save_dir, exist_ok=True)

        for img_num in tqdm(range(self.num_images), desc='Generate images', unit=' images'):
            img_res = np.zeros(
                (img_bin.shape[0], img_bin.shape[1], 4),
                dtype=np.uint8,
            )
            img_paths_selected = self.select_elements(img_paths, num_labels - 1)
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

            save_path = os.path.join(sample_save_dir, f'{sample_name}_{img_num + 1:02d}.png')
            cv2.imwrite(save_path, img_res)

    @staticmethod
    def get_file_list(
        src_dir: str,
        ext_list: str,
    ) -> List[str]:
        file_list = [
            os.path.join(root, file)
            for root, dirs, files in os.walk(src_dir)
            for file in files
            if file.endswith(ext_list)
        ]
        file_list.sort()
        return file_list


if __name__ == '__main__':

    sample_dir = 'data/highlights/01'
    save_dir = 'data/highlights_ready'

    processor = ImageGenerator(
        num_images=5,
        scaling_factor=2,
        seed=42,
        save_dir=save_dir,
    )
    processor.process_sample(sample_dir=sample_dir)
