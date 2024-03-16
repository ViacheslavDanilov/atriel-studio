import logging
import os

import hydra
from joblib import Parallel, delayed
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src import PROJECT_DIR
from src.image_generator import ImageGenerator
from src.utils import get_dir_list

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@hydra.main(
    config_path=os.path.join(PROJECT_DIR, 'configs'),
    config_name='generate_images',
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

    # Initialize an Image Generator instance
    generator = ImageGenerator(
        num_images=cfg.num_images,
        scaling_factor=cfg.scaling_factor,
        seed=cfg.seed,
    )

    # Parse samples concurrently
    _ = Parallel(n_jobs=-1)(
        delayed(generator.process_sample)(
            sample_dir=sample_dir,
            save_dir=save_dir,
        )
        for sample_dir in tqdm(sample_dirs)
    )


if __name__ == '__main__':
    main()
