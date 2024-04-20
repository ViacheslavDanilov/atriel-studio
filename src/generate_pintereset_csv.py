import logging
import os
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from src import PROJECT_DIR
from src.utils import get_file_list

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

    # Get list of dataset images
    img_paths = get_file_list(
        directory=data_dir,
        file_template='*.[jpPJ][nNpP][gG]',
    )

    category = extract_id(path=img_paths[0], type='category')
    sample_name = extract_id(path=img_paths[0], type='sample_name')
    sample_id = extract_id(path=img_paths[0], type='sample_id')
    print(category, sample_name, sample_id)

    log.info('Complete')


if __name__ == '__main__':
    main()
