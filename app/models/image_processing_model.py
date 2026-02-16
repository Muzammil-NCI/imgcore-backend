import re
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator

from app.constants import IMAGE_ACTIONS

ThumbnailSize = Literal["small", "medium", "large"]


class ImageProcessingParameters(BaseModel):
    width: int = Field(description="The width of the image", ge=1, le=10000, default=100)
    height: int = Field(description="The height of the image", ge=1, le=10000, default=100)
    angle: int = Field(description="The angle of rotation in degrees", ge=0, le=360, default=90)
    x: int = Field(description="The x coordinate for crop (left)", ge=0, le=10000, default=0)
    y: int = Field(description="The y coordinate for crop (top)", ge=0, le=10000, default=0)
    text: Optional[str] = Field(description="Text to draw on image", default="Hello, world!")
    font_size: int = Field(description="Font size for text overlay", ge=6, le=200, default=20)
    font_color: str = Field(
        description="Text color as RGBA: '(r, g, b, a)' or '(r, g, b)' (0-255)",
        default="(255, 255, 255, 255)",
    )

    @field_validator("font_color")
    @classmethod
    def validate_rgba_color(cls, v: str) -> str:
        if not re.match(
            r"^\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*\d+\s*)?\)\s*$",
            v.strip(),
        ):
            raise ValueError("font_color must be RGBA format: '(r, g, b, a)' or '(r, g, b)'")
        return v.strip()
    text_x: Optional[int] = Field(description="X position for text (None = center)", ge=0, le=10000, default=None)
    text_y: Optional[int] = Field(description="Y position for text (None = center)", ge=0, le=10000, default=None)
    thumbnail_size: Optional[ThumbnailSize] = Field(
        description="Preset size for thumbnail: small, medium, or large",
        default=None,
    )
    blur_radius: float = Field(description="Radius for Gaussian blur", ge=0, le=100, default=2.0)


class TransformRequestBody(BaseModel):
    """Request body for POST /transform."""

    uri: str = Field(..., description="URL of the image to transform")
    action: str = Field(..., description="The action to perform on the image")
    parameters: Optional[ImageProcessingParameters] = Field(
        default=None,
        description="Optional parameters for the action (defaults used when omitted)",
    )