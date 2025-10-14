import logging
from pathlib import Path

from PIL import Image, ImageStat
from PIL.Image import Resampling


def analyze_background_area(image: Path, area: tuple[float, float, float, float]) -> dict:
  """
  Advanced analysis of a background area to determine if it should have dark or light overlay.

  Returns a dictionary with analysis results including:
  - is_dark: Boolean indicating if the area is generally dark
  - mean_brightness: Average brightness value (0-255)
  - contrast: Measure of contrast within the area
  - histogram_analysis: Results from histogram analysis
  """
  with Image.open(image).convert("L") as img:
    image_area = img.crop(area)

    # Calculate statistics
    stats = ImageStat.Stat(image_area)
    mean_brightness = stats.mean[0]

    # Calculate contrast (standard deviation of brightness)
    contrast = stats.stddev[0]

    # Get histogram for more detailed analysis
    histogram = image_area.histogram()

    # Analyze histogram to find dominant brightness ranges
    dark_range_percentage = sum(histogram[:85]) / sum(histogram)  # Very dark pixels
    mid_range_percentage = sum(histogram[85:170]) / sum(histogram)  # Mid-range pixels
    light_range_percentage = sum(histogram[170:]) / sum(histogram)  # Light pixels

    # For high contrast images, we need to be more careful
    is_high_contrast = contrast > 60

    # Make final determination with multiple factors
    is_dark_mean = mean_brightness < 128

    # For logos, we want to consider dominant color ranges more heavily
    # If more than 40% of pixels are dark, or if dark+mid pixels are more than 65%, consider it dark
    is_dark_histogram = dark_range_percentage > 0.4 or (dark_range_percentage + mid_range_percentage > 0.65)

    # For high contrast images, we lean more on the mean brightness
    # For low contrast images, we trust the histogram analysis more
    if is_high_contrast:
      is_dark = is_dark_mean
    else:
      # For more uniform brightness (logos), use a combination with more weight on histogram
      is_dark = is_dark_histogram if dark_range_percentage > 0.35 else is_dark_mean

    return {
        "is_dark": is_dark,
        "mean_brightness": mean_brightness,
        "contrast": contrast,
        "histogram_analysis": {
            "dark_percentage": dark_range_percentage,
            "mid_percentage": mid_range_percentage,
            "light_percentage": light_range_percentage
        },
        "is_high_contrast": is_high_contrast
    }


def should_use_dark_overlay(image: Path, area: tuple[float, float, float, float]) -> bool:
  """
  Determine if a dark overlay should be used for better readability.

  Returns True if a dark overlay should be used, False if a light overlay is better.
  """
  analysis = analyze_background_area(image, area)

  # If the area is dark, use a light overlay (return False)
  # If the area is light, use a dark overlay (return True)
  return not analysis["is_dark"]


def scale_image_to_720p(image_path: Path) -> Path:
  with Image.open(image_path) as img:
    width, height = img.size
    if height > 720:
      new_width = int((720 / height) * width)
      img = img.resize((new_width, 720), Resampling.LANCZOS)
      save_path = image_path.parent / f"{image_path.stem}-scaled{image_path.suffix}"
      img.save(save_path)
      return save_path
    else:
      return image_path


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
