import logging
import os
import shutil
from os import lstat
from pathlib import Path
from random import choices
from typing import Optional

import yaml

history_data_file = "background_history.yaml"


def clean_team_upload_folder(config: dict, keep_file: Path):
  upload_folder: Path = Path(config['msteams_upload_dir'])

  for file in upload_folder.iterdir():
    if file.name != keep_file.name and f"{file.stem}" != f"{keep_file.stem}_thumb":
      file.unlink()


def get_image_to_replace(config: dict) -> Path:
  upload_folder: Path = Path(config['msteams_upload_dir'])
  linked_image: Optional[Path] = None

  files = list(upload_folder.glob("**/*"))

  file: Path
  files = [file for file in files if file.name != ".DS_Store" and "_thumb" not in file.name]

  if len(files) > 0:
    for file in upload_folder.iterdir():
      if _is_hard_link(file):
        logging.info("Found image hard link: " + str(file))
        linked_image = file

    if linked_image is None:
      logging.info("No hard link was found. Searching for a png image")
      linked_image = _get_first_image(upload_folder, "png")

    if linked_image is None:
      logging.info("No hard link was found. Searching for a jpg image")
      linked_image = _get_first_image(upload_folder, "jpg")

    if linked_image is None:
      logging.info("No hard link was found. Searching for a jpeg image")
      linked_image = _get_first_image(upload_folder, "jpeg")

    logging.info(f"Detected image to replace: {linked_image.name}")
  else:
    logging.info("No uploaded image in MS Teams was found. Please upload a image manually, which will than be replaced.")

  return linked_image


def _get_first_image(folder: Path, extension: str):
  images = list(folder.glob(f'**/*.{extension}'))
  images = [file for file in images if "_thumb" not in file.name]
  return images[0] if images else None


def _is_hard_link(path: Path):
  return lstat(path).st_nlink == 2


def copy_image_to_temp_dir(config: dict, image: Path) -> Path:
  Path(config['temp_dir']).mkdir(parents=True, exist_ok=True)
  return shutil.copyfile(image, Path(config['temp_dir'], "teams-background" + image.suffix), follow_symlinks=False)


def replace_image_with_new_link(to_be_replaced: Path, new_image: Path):
  to_be_replaced.unlink()
  os.link(new_image, to_be_replaced)
  logging.info(f"Created hard link to {new_image.name} in {str(to_be_replaced)}")


def get_new_background_path(config: dict) -> Path:
  history_file = Path(config['config_dir'], history_data_file)
  logging.info(f"Reading history from {history_file}")

  if history_file.exists():
    with open(history_file, 'r') as infile:
      background_history = yaml.safe_load(infile)
  else:
    background_history = {}

  logging.info(f"Search for backgrounds in '{config['image_source_dir']}'")

  possible_backgrounds = list(Path(config['image_source_dir']).glob('**/*.png'))
  possible_backgrounds += list(Path(config['image_source_dir']).glob('**/*.jpeg'))
  possible_backgrounds += list(Path(config['image_source_dir']).glob('**/*.jpg'))

  logging.info(f"Found {len(possible_backgrounds)} background images")

  if len(possible_backgrounds) == 0:
    raise FileNotFoundError("No possible background images found")

  # Build up counts for existing files
  counts = {}
  possible_background: Path
  for possible_background in possible_backgrounds:
    if possible_background.stem in background_history:
      counts[possible_background.stem] = background_history[possible_background.stem]
    else:
      counts[possible_background.stem] = 0

  max_count = max(counts.values())
  weights = [(max_count - w) + 1 for w in counts.values()]

  new_background = choices(possible_backgrounds, weights, k=1)[0]

  counts[new_background.stem] += 1

  if not history_file.exists():
    # Create emtpy file if not existing
    if not history_file.parent.exists():
      history_file.parent.mkdir(parents=True)
    open(history_file, 'a').close()

  with open(history_file, 'w') as outfile:
    yaml.dump(counts, outfile)

  return new_background


def get_overlay_image_path(config: dict, light: bool) -> Path:
  if light:
    overlay_path = config['overlay']['logo_file_light']
    if len(overlay_path) > 0:
      return Path(overlay_path)
    else:
      return Path(config['overlay']['logo_file'])
  else:
    return Path(config['overlay']['logo_file'])
