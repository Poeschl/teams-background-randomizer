import argparse
import logging
import sys
from pathlib import Path

from config_helper import read_config
from file_helper import get_new_background_path, copy_image_to_temp_dir, get_image_to_replace, \
  replace_image_with_new_link, \
  clean_team_upload_folder, get_overlay_image_path
from image_helper import get_absolute_area_of_overlay, background_in_area_is_dark, paint_overlay_on_background
from teams_background_randomizer.image_helper import scale_image_to_720p


def main(config_file: str):
  logging.info(f"Reading config from {config_file}")
  config: dict = read_config(Path(config_file))

  new_background: Path = get_new_background_path(config)
  logging.info(f"Selected new background: {new_background.stem}")

  # Create copy in cache dir to avoid locking the original file
  new_background = copy_image_to_temp_dir(config, new_background)
  new_background = scale_image_to_720p(new_background)

  # overlay a logo if configured to do so, also resizes background to configured size
  if config['overlay']['enabled']:
    # Get regular overlay image to get dimensions
    overlay = get_overlay_image_path(config, False)
    overlay_area = get_absolute_area_of_overlay(config, new_background)

    if background_in_area_is_dark(new_background, overlay_area):
      overlay = get_overlay_image_path(config, True)

    new_background = paint_overlay_on_background(overlay_area, overlay, new_background)

  # Clean the upload dir to get a valid image
  image_to_replace = get_image_to_replace(config)
  clean_team_upload_folder(config, image_to_replace)

  # (re)create hard link
  replace_image_with_new_link(image_to_replace, new_background)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", stream=sys.stdout)

  parser = argparse.ArgumentParser(description='Randomly switch the current custom background image in MS Teams')
  parser.add_argument('cfg_file', help='The configuration file to use.')

  args = parser.parse_args()
  main(args.cfg_file)
