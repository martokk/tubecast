import random
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.paths import FONTS_PATH

dark_colors = [
    (51, 17, 0),
    (37, 0, 22),
    (17, 0, 34),
    (0, 17, 34),
    (0, 34, 17),
    (34, 17, 0),
    (22, 0, 37),
    (0, 22, 37),
    (17, 34, 0),
    (0, 37, 22),
    (34, 0, 17),
    (17, 0, 17),
    (0, 17, 17),
    (17, 17, 0),
    (0, 0, 17),
]


def create_logo_from_text(text: str, file_path: Path) -> Path:
    """
    Create a logo from text.

    Args:
        text(str): The text to create the logo from.

    Returns:
        Path: The path to the logo.
    """
    # Prepare canvas
    background = random.choice(dark_colors)
    foreground = (220, 220, 220)
    img = Image.new("RGB", (300, 300), color=background)
    draw = ImageDraw.Draw(img)

    # Set size and wrap text
    text = wrap_text(text)
    font = set_font_size(text=text, img=img)

    # Draw and center text
    width, height = draw.textsize(text, font)
    x = (img.width - width) / 2
    y = (img.height - height) / 2
    draw.text((x, y), text, font=font, fill=foreground, align="center")

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
