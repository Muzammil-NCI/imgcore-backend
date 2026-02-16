IMAGE_ACTIONS = [
    "grayscale",
    "resize",
    "rotate",
    "crop",
    "thumbnail",
    "blur",
    "sharpen",
    "contour",
    "detail",
    "emboss",
    "smooth",
    "edge_enhance",
    "text",
]

# Thumbnail size presets: (width, height)
THUMBNAIL_SIZES = {
    "small": (128, 128),
    "medium": (256, 256),
    "large": (512, 512),
}

MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Extension -> (PIL save format, content_type) for processed output
EXTENSION_TO_OUTPUT_FORMAT = {
    "jpeg": ("JPEG", "image/jpeg"),
    "jpg": ("JPEG", "image/jpeg"),
    "png": ("PNG", "image/png"),
    "gif": ("GIF", "image/gif"),
    "webp": ("WEBP", "image/webp"),
}
