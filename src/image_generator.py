import fnmatch
import os
import random
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pandas as pd


class ImageMatcher:
    """A utility class for matching layout and background images based on their IDs.

    This class provides methods to retrieve file lists from directories, extract IDs from filenames,
    and create a DataFrame connecting layout and background images with matching IDs.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_file_list(
        directory: str,
        file_template: str,
    ):
        file_list = []
        for root, dirs, files in os.walk(directory):
            file_list.extend(
                [os.path.join(root, file) for file in fnmatch.filter(files, file_template)],
            )
        file_list.sort()
        return file_list

    @staticmethod
    def extract_id(
        path: str,
    ):
        filename = str(Path(path).stem)
        id = filename.split('_')[1]
        return id

    def create_dataframe(
        self,
        layout_paths: List[str],
        bg_paths: List[str],
    ) -> pd.DataFrame:

        file_dict: dict = {
            'id': [],
            'layout_path': [],
            'layout_name': [],
            'background_path': [],
            'background_name': [],
        }
        for bg_path in bg_paths:
            id_bg = self.extract_id(path=bg_path)
            for layout_path in layout_paths:
                id_layout = self.extract_id(path=layout_path)

                if id_bg == id_layout:
                    file_dict['id'].append(id_bg)
                    file_dict['layout_path'].append(layout_path)
                    file_dict['layout_name'].append(Path(layout_path).name)
                    file_dict['background_path'].append(bg_path)
                    file_dict['background_name'].append(Path(bg_path).name)
                else:
                    continue

        df = pd.DataFrame(file_dict)

        return df


class ImageGenerator:
    """Class for generating images."""

    def __init__(
        self,
        num_images: int,
        scaling_factor: float,
        seed: int,
    ):
        self.num_images = num_images
        self.scaling_factor = scaling_factor
        self.seed = seed

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

    def load_layout(
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

    @staticmethod
    def load_background(
        img_path: str,
        img_height: int,
        img_width: int,
    ) -> np.ndarray:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        img_resized = cv2.resize(img, dsize=(img_width, img_height), interpolation=cv2.INTER_CUBIC)
        return img_resized

    @staticmethod
    def load_image(
        img_path: str,
    ) -> np.ndarray:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        return img

    def process_sample(
        self,
        sample_dir: str,
        save_dir: str,
    ) -> None:

        # Create a directory to store the files
        sample_name = Path(sample_dir).name
        sample_save_dir = os.path.join(save_dir, sample_name)
        os.makedirs(sample_save_dir, exist_ok=True)

        img_dir = os.path.join(sample_dir, 'img')
        img_paths = self.get_file_list(img_dir, '*.[pP][nN][gG]')
        layout_path = os.path.join(sample_dir, 'layout.png')
        img_layout = self.load_layout(layout_path)
        bg_paths_ = self.get_file_list(sample_dir, 'background*.[pP][nN][gG]')
        # fmt: off
        bg_paths = self.uniformly_select_elements(bg_paths_, self.num_images, shuffle=True)
        num_objects, _, stats, centroids = cv2.connectedComponentsWithStats(img_layout, connectivity=8)
        # fmt: on
        for idx, img_back_path in enumerate(bg_paths):
            img_bg = self.load_background(
                img_back_path,
                img_height=img_layout.shape[0],
                img_width=img_layout.shape[1],
            )

            img_paths_selected = self.randomly_select_elements(img_paths, num_objects - 1)

            for object_id, img_path in zip(range(1, num_objects), img_paths_selected):
                cx, cy = centroids[object_id]

                img = self.load_image(img_path)
                img = self.crop_transparent_images(img)
                img_size = (
                    stats[object_id, cv2.CC_STAT_WIDTH],
                    stats[object_id, cv2.CC_STAT_HEIGHT],
                )
                img = cv2.resize(img, dsize=img_size)

                x, y = int(cx - img.shape[1] / 2), int(cy - img.shape[0] / 2)
                x, y = max(x, 0), max(y, 0)

                x_end, y_end = min(x + img.shape[1], img_bg.shape[1]), min(
                    y + img.shape[0],
                    img_bg.shape[0],
                )

                if x_end > x and y_end > y:
                    # Check if the background is completely transparent
                    if np.max(img_bg[y:y_end, x:x_end, 3]) == 0:
                        # Copy non-transparent parts of the foreground directly onto the background
                        img_bg[y:y_end, x:x_end] = img[: y_end - y, : x_end - x]
                    else:
                        # Perform alpha blending
                        alpha_img = img[:, :, 3] / 255.0
                        alpha_res = 1.0 - alpha_img

                        for c in range(3):
                            img_bg[y:y_end, x:x_end, c] = (
                                alpha_img * img[: y_end - y, : x_end - x, c]
                                + alpha_res * img_bg[y:y_end, x:x_end, c]
                            )

            save_path = os.path.join(sample_save_dir, f'{sample_name}_{idx + 1:02d}.png')
            cv2.imwrite(save_path, img_bg, [cv2.IMWRITE_PNG_COMPRESSION, 6])

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

    sample_dir = 'data/input/stories/marketing_01'
    save_dir = 'data/output/stories/'

    layout_dir = os.path.join(sample_dir, 'layouts')
    bg_dir = os.path.join(sample_dir, 'backgrounds')

    matcher = ImageMatcher()
    layout_paths = matcher.get_file_list(layout_dir, 'layout*.[jpPJ][nNpP][gG]')
    bg_paths = matcher.get_file_list(bg_dir, 'background*.[jpPJ][nNpP][gG]')
    df = matcher.create_dataframe(layout_paths, bg_paths)

    processor = ImageGenerator(
        num_images=5,
        scaling_factor=1,
        seed=11,
    )
    processor.process_sample(
        sample_dir=sample_dir,
        save_dir=save_dir,
    )
