import re
from typing import Optional

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.constants import IMAGE_ACTIONS, THUMBNAIL_SIZES
from app.models.image_processing_model import ImageProcessingParameters

RGBA_PATTERN = re.compile(r"^\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)\s*$")


def _parse_rgba(rgba_str: str) -> tuple[int, int, int, int]:
    """Parse RGBA string '(r, g, b, a)' or '(r, g, b)' (alpha defaults to 255)."""
    rgba_str = rgba_str.strip()
    m = RGBA_PATTERN.match(rgba_str)
    if not m:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid font_color. Expected RGBA format: '(r, g, b, a)' or '(r, g, b)'. Got: {rgba_str}",
        )
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    a = int(m.group(4)) if m.group(4) is not None else 255
    for name, val in [("r", r), ("g", g), ("b", b), ("a", a)]:
        if not 0 <= val <= 255:
            raise HTTPException(
                status_code=400,
                detail=f"font_color {name} must be 0-255, got {val}",
            )
    return (r, g, b, a)


class ImageProcessingRepository:
    def __init__(self):
        pass

    def process_image(
        self,
        image: Image.Image,
        action: str,
        parameters: Optional[ImageProcessingParameters] = None,
    ) -> Image.Image:
        if parameters is None:
            parameters = ImageProcessingParameters()

        if action not in IMAGE_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

        # Use model defaults: parameters are already ImageProcessingParameters with defaults
        p = parameters

        match action:
            case "grayscale":
                image = image.convert("L")
            case "resize":
                image = image.resize((p.width, p.height))
            case "rotate":
                image = image.rotate(p.angle, expand=True)
            case "crop":
                # crop box: (left, upper, right, lower)
                image = image.crop((p.x, p.y, p.x + p.width, p.y + p.height))
            case "thumbnail":
                if p.thumbnail_size and p.thumbnail_size in THUMBNAIL_SIZES:
                    size = THUMBNAIL_SIZES[p.thumbnail_size]
                else:
                    size = (p.width, p.height)
                image = image.copy()
                image.thumbnail(size)
            case "blur":
                image = image.filter(ImageFilter.GaussianBlur(radius=p.blur_radius))
            case "sharpen":
                image = image.filter(ImageFilter.SHARPEN)
            case "contour":
                image = image.filter(ImageFilter.CONTOUR)
            case "detail":
                image = image.filter(ImageFilter.DETAIL)
            case "emboss":
                image = image.filter(ImageFilter.EMBOSS)
            case "smooth":
                image = image.filter(ImageFilter.SMOOTH)
            case "edge_enhance":
                image = image.filter(ImageFilter.EDGE_ENHANCE)
            case "text":
                text = p.text or "ImageCore <3"
                font_size = p.font_size
                fill_color = _parse_rgba(p.font_color)
                # font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", font_size)

                font = ImageFont.load_default(size=font_size)

                # Draw text at default size, then scale to achieve font_size
                temp_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
                bbox = temp_draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                # default_height = max(th, 1)
                # scale = font_size / default_height

                pad = int(max(tw, th) * 0.5)
                layer = Image.new("RGBA", (int(tw) + pad * 2, int(th) + pad * 2), (0, 0, 0, 0))
                layer_draw = ImageDraw.Draw(layer)
                layer_draw.fontmode = "1"
                layer_draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=fill_color)

                # Scale layer to achieve desired font size
                # if scale != 1.0:
                #     new_w = max(1, int(layer.width * scale))
                #     new_h = max(1, int(layer.height * scale))
                #     layer = layer.resize((new_w, new_h), Image.Resampling.NEAREST)

                if p.angle:
                    layer = layer.rotate(-p.angle, expand=True, resample=Image.Resampling.BICUBIC)

                orig_mode = image.mode
                if image.mode != "RGBA":
                    image = image.convert("RGBA")

                # Placement: center by default, else use (text_x, text_y) as center
                if p.text_x is not None and p.text_y is not None:
                    paste_x = p.text_x - layer.width // 2
                    paste_y = p.text_y - layer.height // 2
                else:
                    paste_x = (image.width - layer.width) // 2
                    paste_y = (image.height - layer.height) // 2

                image.paste(layer, (paste_x, paste_y), layer)
                if image.mode != orig_mode:
                    image = image.convert(orig_mode)

        return image
