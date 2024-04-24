import fnmatch
import os
import random
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm.auto import tqdm


class ImageGenerator:
    """Class for generating images."""

    def __init__(
        self,
        num_images_per_bg: int,
        scaling_factor: float,
        seed: int,
    ):
        self.num_images_per_bg = num_images_per_bg
        self.scaling_factor = scaling_factor
        self.seed = seed

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

    @staticmethod
    def _randomly_select_elements(
        lst: List[str],
        num_elements: int,
    ) -> List[str]:
        if num_elements > len(lst):
            raise ValueError('N is greater than the length of the list')
        selected_elements = random.sample(lst, num_elements)
        random.shuffle(selected_elements)
        return selected_elements

    @staticmethod
    def _crop_transparent_images(
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

    def _load_layout(
        self,
        layout_path: str,
    ) -> np.ndarray:
        layout = cv2.imread(layout_path, cv2.IMREAD_COLOR)
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

    @staticmethod
    def _load_background(
        img_path: str,
        img_height: int,
        img_width: int,
    ) -> np.ndarray:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        if img.shape[0] != img_height or img.shape[1] != img_width:
            img_resized = cv2.resize(
                img,
                dsize=(img_width, img_height),
                interpolation=cv2.INTER_CUBIC,
            )
            return img_resized
        else:
            return img

    @staticmethod
    def _load_foreground(
        img_path: str,
    ) -> np.ndarray:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

        # Check if the image is grayscale (1-channel)
        if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
            # Convert grayscale to 3-channel RGB
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Check if the image has 3 channels (RGB)
        if img.shape[2] == 3:
            # Convert RGB to 4-channel RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)

        # Check if the image has 4 channels (RGBA)
        if img.shape[2] == 4:
            # Ensure that alpha channel values are in the range [0, 255]
            img[:, :, 3] = np.clip(img[:, :, 3], 0, 255)
        return img

    @staticmethod
    def _merge_images_masked(
        img_fore: np.ndarray,
        img_back: np.ndarray,
        mask_layout: np.ndarray,
        x_min: int,
        x_max: int,
        y_min: int,
        y_max: int,
    ) -> np.ndarray:
        # Apply mask to the inserted image
        img_fore = cv2.bitwise_and(img_fore, img_fore, mask=mask_layout[y_min:y_max, x_min:x_max])

        # Check if the background is completely transparent
        if np.max(img_back[y_min:y_max, x_min:x_max, 3]) == 0:
            # Copy non-transparent parts of the foreground directly onto the background
            img_back[y_min:y_max, x_min:x_max] = img_fore[: y_max - y_min, : x_max - x_min]
        else:
            # Perform alpha blending
            alpha_img = img_fore[:, :, 3] / 255.0
            alpha_res = 1.0 - alpha_img

            for c in range(3):
                img_back[y_min:y_max, x_min:x_max, c] = (
                    alpha_img * img_fore[: y_max - y_min, : x_max - x_min, c]
                    + alpha_res * img_back[y_min:y_max, x_min:x_max, c]
                )
        return img_back

    @staticmethod
    def _compute_coordinates(
        img_fore: np.ndarray,
        img_back: np.ndarray,
        centroid: List[float],
    ) -> Tuple[int, int, int, int]:
        cx, cy = centroid
        x_min = int(cx - img_fore.shape[1] / 2)
        y_min = int(cy - img_fore.shape[0] / 2)
        x_min = max(x_min, 0)
        y_min = max(y_min, 0)
        x_max = min(x_min + img_fore.shape[1], img_back.shape[1])
        y_max = min(y_min + img_fore.shape[0], img_back.shape[0])

        return x_min, y_min, x_max, y_max

    def _process_single_background(
        self,
        row: pd.Series,
        sample_dir: str,
        save_dir: str,
    ) -> None:
        img_dir = os.path.join(sample_dir, 'images')
        img_paths = self.get_file_list(img_dir, '*.[jpPJ][nNpP][gG]')
        mask_layout = self._load_layout(row.layout_path)
        img_back = self._load_background(
            row.background_path,
            img_height=mask_layout.shape[0],
            img_width=mask_layout.shape[1],
        )

        num_objects, _, stats, centroids = cv2.connectedComponentsWithStats(
            mask_layout,
            connectivity=8,
        )

        for idx in range(self.num_images_per_bg):
            img_paths_selected = self._randomly_select_elements(img_paths, num_objects - 1)
            for object_id, img_path in zip(range(1, num_objects), img_paths_selected):
                img_fore = self._load_foreground(img_path)
                img_fore = self._crop_transparent_images(img_fore)
                img_fore = cv2.resize(
                    img_fore,
                    dsize=(
                        stats[object_id, cv2.CC_STAT_WIDTH],
                        stats[object_id, cv2.CC_STAT_HEIGHT],
                    ),
                )

                x_min, y_min, x_max, y_max = self._compute_coordinates(
                    img_fore=img_fore,
                    img_back=img_back,
                    centroid=centroids[object_id],
                )

                if x_max > x_min and y_max > y_min:
                    img_back = self._merge_images_masked(
                        img_fore=img_fore,
                        img_back=img_back,
                        mask_layout=mask_layout,
                        x_min=x_min,
                        y_min=y_min,
                        x_max=x_max,
                        y_max=y_max,
                    )

            filename = f'{row.layout_id}_{row.background_id}_{idx + 1:01d}.png'
            save_path = os.path.join(save_dir, filename)
            cv2.imwrite(save_path, img_back, [cv2.IMWRITE_PNG_COMPRESSION, 6])

    def process_sample(
        self,
        df: pd.DataFrame,
        sample_dir: str,
        save_dir: str,
    ) -> None:

        # Create a directory to store the files
        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(save_dir, sample_name)
        os.makedirs(sample_save_dir, exist_ok=True)

        # Iterate over layout-background pairs
        _ = Parallel(n_jobs=-1)(
            delayed(self._process_single_background)(
                row=row,
                sample_dir=sample_dir,
                save_dir=sample_save_dir,
            )
            for row in tqdm(df.itertuples(), unit='pairs')
        )
