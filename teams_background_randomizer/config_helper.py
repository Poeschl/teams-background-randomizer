from pathlib import Path
from typing import Dict, Optional

import platformdirs
from yaml import safe_load, YAMLError

default_config = {
    "image_source_dir": "",
    "msteams_upload_dir": "",
    "config_dir": "",
    "temp_dir": "",
    "overlay": {
        "enabled": False,
        "logo_file": "",
        "logo_file_light": "",
        "offset": {
            "x": 0.1,
            "y": 0.1
        },
        "size": {
            "width": 0.2,
            "height": 0.2
        }
    }
}


def read_config(config_file: Path) -> dict:
  """Reads the config file and returns the configuration as a dictionary. Will apply default values."""

  config = default_config
  config.update(_read_config_file(config_file))

  if len(config["image_source_dir"]) < 1:
    config["image_source_dir"] = platformdirs.user_pictures_dir()

  if len(config["config_dir"]) < 1:
    config["config_dir"] = platformdirs.user_data_dir("teams-background-randomizer")

    if len(config["temp_dir"]) < 1:
      config["temp_dir"] = platformdirs.user_cache_dir("teams-background-randomizer")

  #TODO: Auto-detect ms teams upload dir

  return config


def _read_config_file(config_file: Path) -> Dict:
  with open(config_file, 'r', encoding="utf-8") as stream:
    try:
      local_config = safe_load(stream)
      return local_config
    except YAMLError as exc:
      print("Error on file config read. {}".format(exc))
      return {}
