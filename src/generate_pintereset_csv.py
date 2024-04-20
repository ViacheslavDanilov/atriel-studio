import logging
import os
from glob import glob
from pathlib import Path
from typing import List

import hydra
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from src import PROJECT_DIR
from src.text_generators import DescriptionGenerator, TitleGenerator
from src.utils import CSV_COLUMNS

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def extract_id(
    path: str,
    type: str = 'category',
) -> str:

    parts = Path(path).parts
    if type == 'category':
        return parts[-4]
    elif type == 'sample_name':
        return parts[-3]
    elif type == 'sample_id':
        return parts[-2]
    else:
        raise ValueError('Invalid type')


def generate_sample_df(
    img_paths: List[str],
    df_desc: pd.DataFrame,
    df_key: pd.DataFrame,
) -> pd.DataFrame:

    df = pd.DataFrame(columns=CSV_COLUMNS)
    df['img_path'] = img_paths

    return df


@hydra.main(
    config_path=os.path.join(PROJECT_DIR, 'configs'),
    config_name='generate_pintereset_csv',
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    log.info(f'Config:\n\n{OmegaConf.to_yaml(cfg)}')

    # Define absolute paths
    data_dir = str(os.path.join(PROJECT_DIR, cfg.data_dir))
    save_dir = str(os.path.join(PROJECT_DIR, cfg.save_dir))
    print(save_dir)

    sample_paths = glob(os.path.join(data_dir, '*/*'))
    for sample_path in sample_paths:
        img_paths = glob(os.path.join(sample_path, '*/*.[jpPJ][nNpP][gG]'))

        # Prepare a list of titles
        df_key = pd.read_csv(os.path.join(sample_path, 'keywords.csv'))
        title_generator = TitleGenerator(df_key)
        title_list = title_generator.generate_titles(num_titles=len(img_paths))

        # Prepare a list of descriptions
        df_desc = pd.read_csv(os.path.join(sample_path, 'descriptions.csv'))
        desc_generator = DescriptionGenerator(df_desc)
        desc_list = desc_generator.generate_descriptions(num_descriptions=len(img_paths))

        # Prepare a list of keywords
        keyword_list = [''] * len(img_paths)

        print(title_list, desc_list, keyword_list)

    log.info('Complete')


if __name__ == '__main__':
    main()
