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

    def select_elements(self, lst: List[str], n: int) -> List[str]:
        random.seed(self.seed)
        if n > len(lst):
            raise ValueError('N is greater than the length of the list')
        selected_elements = random.sample(lst, n)
        random.shuffle(selected_elements)
        return selected_elements

    def process_sample(
        self,
        sample_dir: str,
    ) -> None:
        img_paths = self.get_file_list(os.path.join(sample_dir, 'img'), '.png')
        layout_path = os.path.join(sample_dir, 'layout.png')
        layout = cv2.imread(layout_path, cv2.IMREAD_UNCHANGED)
        gray_layout = cv2.cvtColor(layout, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray_layout, 127, 255, cv2.THRESH_BINARY)
        thresh_resized = cv2.resize(
            thresh,
            dsize=None,
            fx=self.scaling_factor,
            fy=self.scaling_factor,
            interpolation=cv2.INTER_NEAREST,
        )
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            thresh_resized,
            connectivity=8,
        )

        for img_num in tqdm(range(self.num_images), desc='Generate images', unit=' images'):
            img_res = np.zeros(
                (thresh_resized.shape[0], thresh_resized.shape[1], 4),
                dtype=np.uint8,
            )
            img_paths_selected = self.select_elements(img_paths, num_labels - 1)
            for label in range(1, num_labels):
                cx, cy = centroids[label]
                img_path = img_paths_selected.pop(0)
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                img = cv2.resize(
                    img,
                    (stats[label, cv2.CC_STAT_WIDTH], stats[label, cv2.CC_STAT_HEIGHT]),
                )
                x = int(cx - img.shape[1] / 2)
                y = int(cy - img.shape[0] / 2)
                x = max(x, 0)
                y = max(y, 0)
                x_end = min(x + img.shape[1], img_res.shape[1])
                y_end = min(y + img.shape[0], img_res.shape[0])
                if x_end > x and y_end > y:
                    img_res[y:y_end, x:x_end] = img[: y_end - y, : x_end - x]
            sample_name = Path(sample_dir).name
            sample_save_dir = os.path.join(self.save_dir, sample_name)
            os.makedirs(sample_save_dir, exist_ok=True)
            save_path = os.path.join(sample_save_dir, f'{sample_name}_{img_num + 1:02d}.png')
            cv2.imwrite(save_path, img_res)

    @staticmethod
    def get_file_list(src_dir: str, ext_list: str) -> List[str]:
        file_list = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(ext_list):
                    file_list.append(os.path.join(root, file))
        file_list.sort()
        return file_list


if __name__ == '__main__':

    sample_dir = 'data/stories/01'
    save_dir = 'data/stories_ready'

    processor = ImageGenerator(
        num_images=5,
        scaling_factor=2,
        seed=42,
        save_dir=save_dir,
    )
    processor.process_sample(sample_dir=sample_dir)
