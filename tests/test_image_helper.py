import tempfile

import pytest
from pathlib import Path
from PIL import Image

from teams_background_randomizer.image_helper import analyze_background_area

IMAGE_SIZE = (100, 100)
FULL_AREA = (0, 0, 100, 100)

RESOURCES_DIR = Path(__file__).parent / "resources"

# Folder where the analyzed crop of each test is saved as an image, so it can be
# visually inspected after a test run. Not cleaned up automatically like tmp_path.
OUTPUT_DIR = Path(tempfile.gettempdir()) / "teams_background_randomizer_test_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print("Temp Folder for screenshots: ", OUTPUT_DIR)


def analyze_and_save(image: Path, area: tuple[float, float, float, float], output_name: str) -> dict:
  """
  Analyze the given area like analyze_background_area, but additionally save the
  cropped area as an image to OUTPUT_DIR for manual visual inspection.
  """
  with Image.open(image) as img:
    img.crop(area).convert("RGB").save(OUTPUT_DIR / f"{output_name}.png")

  return analyze_background_area(image, area)


def create_grayscale_image(tmp_path: Path, brightness: int, filename: str = "test.png") -> Path:
  img = Image.new("L", IMAGE_SIZE, brightness)
  path = tmp_path / filename
  img.save(path)
  return path


def create_checkerboard_image(tmp_path: Path, filename: str = "checkerboard.png") -> Path:
  img = Image.new("L", IMAGE_SIZE, 0)
  pixels = img.load()
  for x in range(IMAGE_SIZE[0]):
    for y in range(IMAGE_SIZE[1]):
      pixels[x, y] = 255 if (x + y) % 2 == 0 else 0
  path = tmp_path / filename
  img.save(path)
  return path


class TestAnalyzeBackgroundArea:

  def test_dark_image_is_detected_as_dark(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=20)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["is_dark"] is True

  def test_light_image_is_detected_as_light(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=220)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["is_dark"] is False

  def test_dark_image_has_low_mean_brightness(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=30)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["mean_brightness"] < 128

  def test_light_image_has_high_mean_brightness(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=200)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["mean_brightness"] >= 128

  def test_uniform_image_has_low_contrast(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=128)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["contrast"] < 10

  def test_checkerboard_image_has_high_contrast(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_checkerboard_image(tmp_path)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert result["is_high_contrast"] is True
    assert result["contrast"] > 60

  def test_result_contains_all_expected_keys(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=100)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    assert "is_dark" in result
    assert "mean_brightness" in result
    assert "contrast" in result
    assert "is_high_contrast" in result
    assert "histogram_analysis" in result
    assert "dark_percentage" in result["histogram_analysis"]
    assert "mid_percentage" in result["histogram_analysis"]
    assert "light_percentage" in result["histogram_analysis"]

  def test_histogram_percentages_sum_to_one(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given
    image = create_grayscale_image(tmp_path, brightness=80)

    # when
    result = analyze_and_save(image, FULL_AREA, request.node.name)

    # then
    total = (result["histogram_analysis"]["dark_percentage"] + result["histogram_analysis"]["mid_percentage"] +
             result["histogram_analysis"]["light_percentage"])
    assert abs(total - 1.0) < 1e-6

  def test_area_crop_is_respected(self, tmp_path: Path, request: pytest.FixtureRequest):
    # given - create an image that is white on the left half and dark on the right half
    img = Image.new("L", (200, 100), 220)
    pixels = img.load()
    for x in range(100, 200):
      for y in range(100):
        pixels[x, y] = 20
    path = tmp_path / "split.png"
    img.save(path)

    # when - analyze only the dark right half
    result = analyze_and_save(path, (100, 0, 200, 100), request.node.name)

    # then
    assert result["mean_brightness"] < 128

  def test_bobby_upper_right_corner_is_dark(self, request: pytest.FixtureRequest):
    # given - bobby.png is 1536x1024, upper right corner is 600x200
    image = RESOURCES_DIR / "bobby.png"
    area = (936, 0, 1536, 200)

    # when
    result = analyze_and_save(image, area, request.node.name)

    # then
    assert result["is_dark"] is True

  def test_coloor_upper_right_corner_is_dark(self, request: pytest.FixtureRequest):
    # given - coloor.png is 1536x1024, upper right corner is 900x200
    image = RESOURCES_DIR / "coloor.png"
    area = (636, 0, 1536, 200)

    # when
    result = analyze_and_save(image, area, request.node.name)

    # then
    assert result["is_dark"] is True

  def test_bobby_upper_right_corner_is_light(self, request: pytest.FixtureRequest):
    # given - bobby.png is 1536x1024, upper light right corner is 900x200 with offset of 400 px
    image = RESOURCES_DIR / "bobby.png"
    area = (36, 0, 936, 200)

    # when
    result = analyze_and_save(image, area, request.node.name)

    # then
    assert result["is_dark"] is False
