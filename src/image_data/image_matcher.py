import fnmatch
import os
from pathlib import Path
from typing import List, Tuple, Union

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
    ) -> Tuple[str, Union[str, None]]:
        filename = str(Path(path).stem)
        parts = filename.split("_")
        if len(parts) == 2:  # Format: layout_XX.jpg
            return parts[1], None
        elif len(parts) == 3:  # Format: background_XX_Y.jpg
            return parts[1], parts[2].split(".")[0]
        else:
            raise ValueError("Invalid filename format")

    def create_dataframe(
        self,
        layout_paths: List[str],
        bg_paths: List[str],
    ) -> pd.DataFrame:
        file_dict: dict = {
            "layout_id": [],
            "background_id": [],
            "layout_name": [],
            "background_name": [],
            "layout_path": [],
            "background_path": [],
        }
        for bg_path in bg_paths:
            id_layout_check, id_bg = self.extract_id(path=bg_path)
            for layout_path in layout_paths:
                id_layout, _ = self.extract_id(path=layout_path)

                if id_layout_check == id_layout:
                    file_dict["layout_id"].append(id_layout)
                    file_dict["background_id"].append(id_bg)
                    file_dict["layout_name"].append(Path(layout_path).name)
                    file_dict["background_name"].append(Path(bg_path).name)
                    file_dict["layout_path"].append(layout_path)
                    file_dict["background_path"].append(bg_path)
                else:
                    continue

        df = pd.DataFrame(file_dict)

        return df


if __name__ == "__main__":
    sample_dir = "data/input/stories/marketing_05"
    save_dir = "data/output/stories/"

    layout_dir = os.path.join(sample_dir, "layouts")
    bg_dir = os.path.join(sample_dir, "backgrounds")

    matcher = ImageMatcher()
    layout_paths = matcher.get_file_list(layout_dir, "layout*.[jpPJ][nNpP][gG]")
    bg_paths = matcher.get_file_list(bg_dir, "background*.[jpPJ][nNpP][gG]")
    df = matcher.create_dataframe(layout_paths, bg_paths)
    print("Complete!")
