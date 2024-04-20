import logging
import os
import random
from glob import glob
from pathlib import Path
from typing import List

import hydra
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from src import PROJECT_DIR
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


def generate_sample_descriptions(
    num_descriptions: int,
    df_desc: pd.DataFrame,
) -> List[str]:
    descriptions = df_desc['Description'].tolist()
    random.shuffle(descriptions)
    result = []
    prev_desc = None

    for desc in descriptions:
        if desc != prev_desc:
            result.append(desc)
            prev_desc = desc
            if len(result) == num_descriptions:
                break

    # Not enough unique descriptions, fill the remaining with repeats
    if len(result) < num_descriptions:
        remaining = num_descriptions - len(result)
        unique_descriptions = set(descriptions)
        remaining_descriptions = [desc for desc in unique_descriptions if desc != prev_desc]
        random.shuffle(remaining_descriptions)
        result.extend(remaining_descriptions[:remaining])

    return result


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
        df_desc = pd.read_csv(os.path.join(sample_path, 'descriptions.csv'))
        df_key = pd.read_csv(os.path.join(sample_path, 'keywords.csv'))
        desc_list = generate_sample_descriptions(
            num_descriptions=len(img_paths),
            df_desc=df_desc,
        )
        print(df_key, desc_list)

    log.info('Complete')


if __name__ == '__main__':
    main()
