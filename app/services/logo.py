import random
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from app.paths import FONTS_PATH

DARK_COLORS = [
    "#2C3E50",  # Midnight Blue
    "#1F3A93",  # Dark Indigo
    "#462066",  # Dark Purple
    "#7B4397",  # Dark Violet
    "#922B21",  # Dark Red
    "#943126",  # Dark Tomato
    "#CA6924",  # Dark Orange
    "#D35400",  # Dark Carrot
    "#D35400",  # Dark Pumpkin
    "#CA6F1E",  # Dark Goldenrod
    "#8E44AD",  # Dark Magenta
    "#6C3483",  # Dark Orchid
    "#5B2C6F",  # Dark Slate Blue
    "#515A5A",  # Dark Cyan
    "#2E4053",  # Dark Slate
    "#212F3D",  # Dark Blue Gray
    "#154360",  # Dark Denim
    "#0E6251",  # Dark Viridian
    "#145A32",  # Dark Moss Green
    "#186A3B",  # Dark Green
    "#7D6608",  # Dark Yellow
    "#7D6608",  # Dark Gold
    "#A04000",  # Dark Vermilion
    "#943126",  # Dark Coral
    "#943126",  # Dark Salmon
]


def is_invalid_image(image_url: str | None) -> bool:
    """
    Checks if the image url returns a invalid image (ie. 1x1px image)

    Args:
        image_url: url of image

    Returns:
        Boolean True/False
    """
    if not image_url:
        return True

    # Get Image from URL
    response = requests.get(image_url, stream=True)
    content_type = response.headers.get("Content-Type")
    if not content_type or not content_type.startswith("image/"):
        raise ValueError(f"The provided Image URL does not point to an image. ({image_url})")

    # Check Image Size
    image = Image.open(response.raw)
    image_width, image_height = image.size

    # Check for 1x1px image size
    if image_width == 1 and image_height == 1:
        return True

    return False


def html_color_to_rgb(color: str) -> tuple[int, ...]:
    return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))  # noqa: E203


def create_logo_from_text(
    text: str, file_path: Path, background_color: str | None = None, border_color: str | None = None
) -> Path:
    """
    Create a logo from text.

    Args:
        text(str): The text to create the logo from.

    Returns:
        Path: The path to the logo.
    """
    # Prepare canvas
    if not background_color:
        background_color_rgb = html_color_to_rgb(random.choice(DARK_COLORS))
    else:
        background_color_rgb = html_color_to_rgb(background_color)

    foreground = html_color_to_rgb("#FFFFFF")
    img = Image.new("RGB", (300, 300), color=background_color_rgb)
    draw = ImageDraw.Draw(img)

    # Set size and wrap text
    text = wrap_text(text)
    font = set_font_size(text=text, img=img)

    # Draw and center text
    width, height = ImageDraw.Draw(img).textsize(text, font)  # type: ignore
    x = (img.width - width) / 2
    y = (img.height - height) / 2
    draw.text((x, y), text, font=font, fill=foreground, align="center")

    # Draw red border
    if border_color:
        border_thickness = 5
        border_color_rgb = html_color_to_rgb(border_color)
        border_box = [
            (0, 0),
            (img.width, img.height),
        ]
        draw.rectangle(border_box, outline=border_color_rgb, width=border_thickness)  # type: ignore

    # Save image
    file_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(file_path)
    return file_path


def set_font_size(text: str, img: Image.Image) -> ImageFont.FreeTypeFont:
    """
    Set the font size to fit the image.

    Args:
        text(str): The text to create the logo from.
        img(Image): The image to fit the text into.

    Returns:
        ImageFont.FreeTypeFont: The font to use.
    """
    font_size = 1
    font_path = str(FONTS_PATH / "arial.ttf")
    font = ImageFont.truetype(font_path, font_size)
    while True:
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
        width, height = ImageDraw.Draw(img).textsize(text, font)
        if width >= img.width - 30 or height >= img.height - 30:
            font_size -= 4
            font = ImageFont.truetype(font_path, font_size)
            break
    return font


def wrap_text(text: str) -> str:
    """
    Wrap text to fit the image.

    Args:
        text(str): The text to wrap.

    Returns:
        str: The wrapped text.
    """
    if len(text) > 80:
        width = 20
    elif len(text) > 40:
        width = 12
    else:
        width = 8
    wrapper = textwrap.TextWrapper(width=width, break_long_words=False)
    word_list = wrapper.wrap(text)
    text = "\n".join(word_list)
    return text
