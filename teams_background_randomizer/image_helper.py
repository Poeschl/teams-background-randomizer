import logging
from pathlib import Path

from PIL import Image

# The percentage of pixels which must be dark to classify a image as dark.
IMAGE_LIGHT_DARK_THRESHOLD_PERCENTAGE = .3


def background_in_area_is_dark(image: Path, area: tuple[float, float, float, float]) -> bool:
  with Image.open(image).convert("L") as img:
    image_area = img.crop(area)
    pixels = image_area.load()
    img.close()

  # Count the dark and light pixels
  dark_count = 0
  for x in range(image_area.width):
    for y in range(image_area.height):
      pixel = pixels[x, y]
      if pixel < 128:
        dark_count += 1

  ratio = dark_count / (image_area.width * image_area.height)
  return ratio > IMAGE_LIGHT_DARK_THRESHOLD_PERCENTAGE


def get_absolute_area_of_overlay(config: dict, background_image_path: Path) -> tuple[float, float, float, float]:
  with Image.open(background_image_path) as img:
    left = config['overlay']['offset']['x'] * img.width
    top = config['overlay']['offset']['y'] * img.height
    right = (config['overlay']['offset']['x'] * img.width) + (config['overlay']['size']['width'] * img.height)
    bottom = (config['overlay']['offset']['y'] * img.height) + (config['overlay']['size']['height'] * img.height)

  return left, top, right, bottom


def paint_overlay_on_background(area: tuple[float, float, float, float], overlay_image_path: Path, background_image_path: Path) -> Path:
  with Image.open(background_image_path).convert("RGBA") as background:
    with Image.open(overlay_image_path).convert("RGBA") as overlay:
      scaled_overlay = overlay.resize((int(area[2] - area[0]), int(area[3] - area[1])))

      # Create a transparent overlay layer and paste the overlay image on the right place
      overlay_layer = Image.new('RGBA', background.size, (255, 0, 0, 0))
      overlay_layer.paste(scaled_overlay, (int(area[2]), int(area[3])), scaled_overlay)

      # Combine the background and overlay layer
      background.paste(overlay_layer, (0, 0), overlay_layer)

      save_path = background_image_path.parent / f"{background_image_path.stem}-overlayed{background_image_path.suffix}"

      background_without_transparency = background.convert("RGB")
      background_without_transparency.save(save_path)
      logging.info(f"Saved background with overlay to {save_path}")

  return save_path
