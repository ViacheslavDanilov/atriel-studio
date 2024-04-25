import logging
import os

import hydra
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src import PROJECT_DIR
from src.image_data.image_generator import ImageGenerator
from src.image_data.image_matcher import ImageMatcher
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

    # Get list of sample_dirs to process
    sample_dirs = get_dir_list(
        data_dir=data_dir,
        include_dirs=cfg.include_samples,
        exclude_dirs=cfg.exclude_samples,
    )

    # Initialize ImageMatcher and ImageGenerator instances
    matcher = ImageMatcher()
    generator = ImageGenerator(
        num_images_per_bg=cfg.num_images_per_bg,
        scaling_factor=cfg.scaling_factor,
        seed=cfg.seed,
    )

    # Process samples sequentially
    for sample_dir in tqdm(sample_dirs, desc='Creating images', unit='samples'):
        layout_dir = os.path.join(sample_dir, 'layouts')
        bg_dir = os.path.join(sample_dir, 'backgrounds')
        layout_paths = matcher.get_file_list(layout_dir, 'layout*.[jpPJ][nNpP][gG]')
        bg_paths = matcher.get_file_list(bg_dir, 'background*.[jpPJ][nNpP][gG]')
        df = matcher.create_dataframe(layout_paths, bg_paths)
        generator.process_sample(
            df=df,
            sample_dir=sample_dir,
            save_dir=save_dir,
        )


if __name__ == '__main__':
    main()
