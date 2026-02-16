import io
from typing import Optional

from fastapi import HTTPException
from PIL import Image

from app.constants import EXTENSION_TO_OUTPUT_FORMAT, IMAGE_ACTIONS
from app.models.image_processing_model import ImageProcessingParameters
from app.repositories import ImageProcessingRepository, S3Repository


class ImageProcessingService:
    def __init__(self):
        self.image_processing_repository = ImageProcessingRepository()
        self.s3_repository = S3Repository()

    async def transform_image(
        self,
        uri: str,
        action: str,
        parameters: Optional[ImageProcessingParameters] = None,
    ):
        if parameters is None:
            parameters = ImageProcessingParameters()
        if action not in IMAGE_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {action}. Must be one of: {IMAGE_ACTIONS}",
            )
        image_bytes = self.s3_repository.get_object(key=uri)
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid image at URI: {e!s}",
            )
        processed_image = self.image_processing_repository.process_image(
            image, action, parameters
        )
        ext = uri.rsplit(".", 1)[-1].lower() if "." in uri else "png"
        pil_format, content_type = EXTENSION_TO_OUTPUT_FORMAT.get(
            ext, ("PNG", "image/png")
        )
        output_buffer = io.BytesIO()
        processed_image.save(output_buffer, format=pil_format)
        output_buffer.seek(0)
        image_bytes = output_buffer.getvalue()
        url = self.s3_repository.put_processed_image(
            file_bytes=image_bytes,
            content_type=content_type,
        )
        signed_url = self.s3_repository.generate_presigned_url(object_url_or_key=url)
        return {"url": signed_url}